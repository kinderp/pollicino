from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Mapping

from .net.bundle import (
    CustodyLedger,
    CustodyRecord,
    ForwardBundle,
    GovernedContactReport,
    governed_forward_contact,
    load_custody_ledger,
    save_custody_ledger,
    seed_bundle_custody,
)
from .net.link import ScarceLinkProfile
from .net.persistence import DirectoryPollicinoStore, _atomic_write_bytes
from .net.store import ChunkManifest, reconstruct_from_store
from .net.store_forward import (
    ForwardContactReport,
    ForwardPeer,
    forward_contact,
    seed_forwarding_object,
)
from .net.wire import DiscoveryDescriptor


NODE_STATE_SCHEMA = "pollicino-node-runtime-v1"


class NodeMode(str, Enum):
    """Research runtime modes; not a production bearer protocol."""

    DISCOVERING = "discovering"
    CONNECTED_MESH = "connected_mesh"
    OPPORTUNISTIC_DTN = "opportunistic_dtn"
    RICH_HOME = "rich_home"


@dataclass(frozen=True, slots=True)
class NodeObjectRecord:
    manifest_fingerprint: bytes
    label: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.manifest_fingerprint, bytes) or len(self.manifest_fingerprint) != 32:
            raise ValueError("manifest_fingerprint must be exactly 32 bytes")
        if not isinstance(self.label, str):
            raise TypeError("label must be a string")

    def to_mapping(self) -> dict[str, str]:
        return {
            "manifest_fingerprint": self.manifest_fingerprint.hex(),
            "label": self.label,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> NodeObjectRecord:
        fingerprint = value.get("manifest_fingerprint")
        label = value.get("label", "")
        if not isinstance(fingerprint, str) or not isinstance(label, str):
            raise ValueError("invalid node object record")
        try:
            decoded = bytes.fromhex(fingerprint)
        except ValueError as exc:
            raise ValueError("node object fingerprint is not hexadecimal") from exc
        return cls(manifest_fingerprint=decoded, label=label)


@dataclass(frozen=True, slots=True)
class NodeBundleRecord:
    """Persist one immutable PNB1 identity without persisting a route oracle."""

    bundle_id: bytes
    forward_zero_hop: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.bundle_id, bytes) or len(self.bundle_id) != 32:
            raise ValueError("bundle_id must be exactly 32 bytes")
        if not isinstance(self.forward_zero_hop, bytes):
            raise TypeError("forward_zero_hop must be bytes")
        bundle, hop = ForwardBundle.decode_forward(self.forward_zero_hop)
        if hop != 0 or bundle.bundle_id != self.bundle_id:
            raise ValueError("persisted bundle identity is invalid")

    @property
    def bundle(self) -> ForwardBundle:
        bundle, hop = ForwardBundle.decode_forward(self.forward_zero_hop)
        if hop != 0:
            raise AssertionError("persisted node bundle unexpectedly contains a route hop")
        return bundle

    def to_mapping(self) -> dict[str, str]:
        return {
            "bundle_id": self.bundle_id.hex(),
            "forward_zero_hop": self.forward_zero_hop.hex(),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> NodeBundleRecord:
        bundle_id = value.get("bundle_id")
        forward = value.get("forward_zero_hop")
        if not isinstance(bundle_id, str) or not isinstance(forward, str):
            raise ValueError("invalid node bundle record")
        try:
            return cls(
                bundle_id=bytes.fromhex(bundle_id),
                forward_zero_hop=bytes.fromhex(forward),
            )
        except ValueError as exc:
            raise ValueError("node bundle record is not valid hexadecimal") from exc


@dataclass(frozen=True, slots=True)
class NodeContactReport:
    source_mode: NodeMode
    target_mode: NodeMode
    forwarding: ForwardContactReport

    @property
    def exact(self) -> bool:
        return self.forwarding.target_exact

    @property
    def total_wire_bytes(self) -> int:
        return self.forwarding.total_wire_bytes


@dataclass(frozen=True, slots=True)
class NodeGovernedContactReport:
    source_mode: NodeMode
    target_mode: NodeMode
    governance: GovernedContactReport

    @property
    def exact(self) -> bool:
        return self.governance.inner is not None and self.governance.inner.target_exact

    @property
    def total_wire_bytes(self) -> int:
        return self.governance.total_wire_bytes


class PollicinoNodeRuntime:
    """Persistent host-side vertical slice for a carried Pollicino node.

    The runtime reuses the existing PollicinoStore/PCM1/PNA1 store-forward and
    PNB1/PNC1 governance paths. Modes are lifecycle context only: changing mode
    never rewrites object bytes, manifests, bundle identity or chunk identity.

    Custody is node-local in this prototype. Each runtime persists only its own
    PNC1 records plus contact IDs it originated. A governed encounter builds a
    temporary ledger containing only the source/target records needed by the
    existing ``governed_forward_contact`` implementation; the full network
    custody graph is never copied into either node.
    """

    def __init__(
        self,
        root: str | os.PathLike[str],
        *,
        node_id: str,
    ) -> None:
        if not isinstance(node_id, str) or not node_id:
            raise ValueError("node_id must be a non-empty string")
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)
        self._state_path = self._root / "node-state.json"
        self._custody_path = self._root / "custody-ledger.json"
        self.store = DirectoryPollicinoStore(self._root / "store")
        self.peer = ForwardPeer(node_id, self.store)
        self._mode = NodeMode.DISCOVERING
        self._objects: dict[bytes, NodeObjectRecord] = {}
        self._bundles: dict[bytes, NodeBundleRecord] = {}

        if self._custody_path.exists():
            self.custody = load_custody_ledger(self._custody_path)
        else:
            self.custody = CustodyLedger()
            self._save_custody()

        if self._state_path.exists():
            self._load_state(expected_node_id=node_id)
        else:
            self._save_state()

    @property
    def node_id(self) -> str:
        return self.peer.peer_id

    @property
    def root(self) -> Path:
        return self._root

    @property
    def mode(self) -> NodeMode:
        return self._mode

    @property
    def known_object_count(self) -> int:
        return len(self._objects)

    @property
    def known_bundle_count(self) -> int:
        return len(self._bundles)

    def transition(self, mode: NodeMode) -> None:
        if not isinstance(mode, NodeMode):
            raise TypeError("mode must be NodeMode")
        self._mode = mode
        self._save_state()

    def publish_exact(
        self,
        payload: bytes,
        *,
        chunk_size: int,
        label: str = "",
    ) -> ChunkManifest:
        manifest = seed_forwarding_object(
            payload,
            chunk_size=chunk_size,
            store=self.store,
        )
        self._register_manifest(manifest, label=label)
        return manifest

    def publish_governed(
        self,
        payload: bytes,
        *,
        chunk_size: int,
        descriptor: DiscoveryDescriptor,
        created_at_s: int,
        label: str = "",
    ) -> tuple[ChunkManifest, ForwardBundle]:
        if not isinstance(descriptor, DiscoveryDescriptor):
            raise TypeError("descriptor must be DiscoveryDescriptor")
        manifest = self.publish_exact(payload, chunk_size=chunk_size, label=label)
        bundle = ForwardBundle.from_descriptor(
            manifest,
            descriptor,
            created_at_s=created_at_s,
        )
        seed_bundle_custody(
            bundle,
            manifest,
            origin=self.peer,
            ledger=self.custody,
            now_s=created_at_s,
        )
        self._register_bundle(bundle)
        self._save_custody()
        return manifest, bundle

    def knows_manifest(self, manifest_fingerprint: bytes) -> bool:
        return manifest_fingerprint in self._objects

    def object_record(self, manifest_fingerprint: bytes) -> NodeObjectRecord:
        try:
            return self._objects[manifest_fingerprint]
        except KeyError as exc:
            raise LookupError("node does not know this manifest") from exc

    def manifest(self, manifest_fingerprint: bytes) -> ChunkManifest:
        self.object_record(manifest_fingerprint)
        try:
            encoded = self.store.get(manifest_fingerprint)
        except LookupError as exc:
            raise ValueError("known manifest is missing from the verified store") from exc
        manifest = ChunkManifest.decode(encoded)
        if manifest.fingerprint != manifest_fingerprint:
            raise ValueError("stored manifest fingerprint mismatch")
        return manifest

    def complete(self, manifest_fingerprint: bytes) -> bool:
        manifest = self.manifest(manifest_fingerprint)
        return all(self.store.has(ref.sha256_digest) for ref in manifest.chunks)

    def reconstruct(self, manifest_fingerprint: bytes) -> bytes:
        manifest = self.manifest(manifest_fingerprint)
        return reconstruct_from_store(manifest, self.store)

    def knows_bundle(self, bundle_id: bytes) -> bool:
        return bundle_id in self._bundles

    def bundle(self, bundle_id: bytes) -> ForwardBundle:
        try:
            return self._bundles[bundle_id].bundle
        except KeyError as exc:
            raise LookupError("node does not know this bundle") from exc

    def custody_record(self, bundle_id: bytes) -> CustodyRecord | None:
        return self.custody.get(bundle_id, self.node_id)

    def receive_from(
        self,
        source: PollicinoNodeRuntime,
        manifest: ChunkManifest,
        *,
        profile: ScarceLinkProfile,
        transfer_id_base: int,
        max_chunks: int,
    ) -> NodeContactReport:
        if not isinstance(source, PollicinoNodeRuntime):
            raise TypeError("source must be PollicinoNodeRuntime")
        _, report = forward_contact(
            manifest,
            source=source.peer,
            target=self.peer,
            profile=profile,
            transfer_id_base=transfer_id_base,
            max_chunks=max_chunks,
        )

        if self.store.has(manifest.fingerprint):
            self._register_manifest(manifest, label=source._label_for(manifest.fingerprint))

        return NodeContactReport(
            source_mode=source.mode,
            target_mode=self.mode,
            forwarding=report,
        )

    def receive_governed_from(
        self,
        source: PollicinoNodeRuntime,
        bundle: ForwardBundle,
        manifest: ChunkManifest,
        *,
        profile: ScarceLinkProfile,
        transfer_id_base: int,
        max_chunks: int,
        contact_id: str,
        now_s: int,
    ) -> NodeGovernedContactReport:
        if not isinstance(source, PollicinoNodeRuntime):
            raise TypeError("source must be PollicinoNodeRuntime")
        if not isinstance(bundle, ForwardBundle):
            raise TypeError("bundle must be ForwardBundle")
        if not source.knows_bundle(bundle.bundle_id):
            raise ValueError("source runtime does not know the governed bundle")
        source_record = source.custody_record(bundle.bundle_id)
        if source_record is None:
            raise ValueError("source runtime has no local custody for the bundle")

        encounter = CustodyLedger()
        encounter.record(source_record)
        target_record = self.custody_record(bundle.bundle_id)
        if target_record is not None:
            encounter.record(target_record)
        if source.custody.contact_seen(bundle.bundle_id, contact_id):
            encounter.mark_contact(bundle.bundle_id, contact_id)

        _, report = governed_forward_contact(
            bundle,
            manifest,
            source=source.peer,
            target=self.peer,
            ledger=encounter,
            profile=profile,
            transfer_id_base=transfer_id_base,
            max_chunks=max_chunks,
            contact_id=contact_id,
            now_s=now_s,
        )

        # Idempotency belongs to the node that initiated this directional
        # contact. It can therefore suppress an exact replay after restart
        # without requiring a network-global contact database.
        if encounter.contact_seen(bundle.bundle_id, contact_id):
            source.custody.mark_contact(bundle.bundle_id, contact_id)
            source._save_custody()

        received_record = encounter.get(bundle.bundle_id, self.node_id)
        if received_record is not None:
            self.custody.record(received_record)
            self._save_custody()

        if self.store.has(manifest.fingerprint):
            self._register_manifest(manifest, label=source._label_for(manifest.fingerprint))
        if received_record is not None:
            self._register_bundle(bundle)

        return NodeGovernedContactReport(
            source_mode=source.mode,
            target_mode=self.mode,
            governance=report,
        )

    def _label_for(self, manifest_fingerprint: bytes) -> str:
        record = self._objects.get(manifest_fingerprint)
        return "" if record is None else record.label

    def _register_manifest(self, manifest: ChunkManifest, *, label: str) -> None:
        if not isinstance(manifest, ChunkManifest):
            raise TypeError("manifest must be ChunkManifest")
        encoded = manifest.encode()
        if not self.store.has(manifest.fingerprint):
            raise ValueError("cannot register a manifest not present in the verified store")
        if self.store.get(manifest.fingerprint) != encoded:
            raise ValueError("registered manifest bytes do not match verified store")
        record = NodeObjectRecord(manifest_fingerprint=manifest.fingerprint, label=label)
        previous = self._objects.get(manifest.fingerprint)
        if previous is not None and previous.label and label and previous.label != label:
            raise ValueError("manifest is already registered with a different label")
        if previous is not None and previous.label and not label:
            record = previous
        self._objects[manifest.fingerprint] = record
        self._save_state()

    def _register_bundle(self, bundle: ForwardBundle) -> None:
        if not isinstance(bundle, ForwardBundle):
            raise TypeError("bundle must be ForwardBundle")
        if not self.knows_manifest(bundle.manifest_fingerprint):
            raise ValueError("cannot register bundle before its manifest is known")
        record = NodeBundleRecord(
            bundle_id=bundle.bundle_id,
            forward_zero_hop=bundle.encode_forward(0),
        )
        previous = self._bundles.get(bundle.bundle_id)
        if previous is not None and previous != record:
            raise ValueError("bundle_id is already bound to different immutable fields")
        self._bundles[bundle.bundle_id] = record
        self._save_state()

    def _state_mapping(self) -> dict[str, object]:
        return {
            "schema": NODE_STATE_SCHEMA,
            "node_id": self.node_id,
            "mode": self.mode.value,
            "objects": [
                self._objects[key].to_mapping()
                for key in sorted(self._objects)
            ],
            "bundles": [
                self._bundles[key].to_mapping()
                for key in sorted(self._bundles)
            ],
        }

    @staticmethod
    def _canonical(value: Mapping[str, object]) -> bytes:
        return json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")

    def _save_state(self) -> None:
        body = self._state_mapping()
        canonical = self._canonical(body)
        envelope = {
            "schema": NODE_STATE_SCHEMA,
            "state": body,
            "state_sha256": hashlib.sha256(canonical).hexdigest(),
        }
        encoded = (
            json.dumps(
                envelope,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            )
            + "\n"
        ).encode("utf-8")
        _atomic_write_bytes(self._state_path, encoded)

    def _save_custody(self) -> None:
        save_custody_ledger(self._custody_path, self.custody)

    def _load_state(self, *, expected_node_id: str) -> None:
        try:
            envelope = json.loads(self._state_path.read_bytes())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("node runtime state is not valid UTF-8 JSON") from exc
        if not isinstance(envelope, Mapping) or envelope.get("schema") != NODE_STATE_SCHEMA:
            raise ValueError("unsupported node runtime state envelope")
        body = envelope.get("state")
        expected = envelope.get("state_sha256")
        if not isinstance(body, Mapping) or not isinstance(expected, str) or len(expected) != 64:
            raise ValueError("node runtime state envelope is incomplete")
        actual = hashlib.sha256(self._canonical(body)).hexdigest()
        if not hmac.compare_digest(actual, expected):
            raise ValueError("node runtime state checksum mismatch")
        if body.get("schema") != NODE_STATE_SCHEMA:
            raise ValueError("unsupported node runtime state schema")
        node_id = body.get("node_id")
        if node_id != expected_node_id:
            raise ValueError("node runtime state belongs to a different node_id")
        mode = body.get("mode")
        if not isinstance(mode, str):
            raise ValueError("node runtime mode is invalid")
        try:
            self._mode = NodeMode(mode)
        except ValueError as exc:
            raise ValueError("node runtime mode is unsupported") from exc

        objects = body.get("objects")
        if not isinstance(objects, list):
            raise ValueError("node runtime objects must be a list")
        loaded_objects: dict[bytes, NodeObjectRecord] = {}
        for value in objects:
            if not isinstance(value, Mapping):
                raise ValueError("node runtime object record must be an object")
            record = NodeObjectRecord.from_mapping(value)
            if record.manifest_fingerprint in loaded_objects:
                raise ValueError("duplicate object in node runtime state")
            try:
                encoded_manifest = self.store.get(record.manifest_fingerprint)
            except LookupError as exc:
                raise ValueError("node runtime state references a missing manifest") from exc
            manifest = ChunkManifest.decode(encoded_manifest)
            if manifest.fingerprint != record.manifest_fingerprint:
                raise ValueError("node runtime state manifest failed verification")
            loaded_objects[record.manifest_fingerprint] = record
        self._objects = loaded_objects

        # Backward-compatible with the very first prototype state that had only
        # mode + object records.
        bundles = body.get("bundles", [])
        if not isinstance(bundles, list):
            raise ValueError("node runtime bundles must be a list")
        loaded_bundles: dict[bytes, NodeBundleRecord] = {}
        for value in bundles:
            if not isinstance(value, Mapping):
                raise ValueError("node runtime bundle record must be an object")
            record = NodeBundleRecord.from_mapping(value)
            if record.bundle_id in loaded_bundles:
                raise ValueError("duplicate bundle in node runtime state")
            if record.bundle.manifest_fingerprint not in self._objects:
                raise ValueError("node runtime bundle references an unknown manifest")
            loaded_bundles[record.bundle_id] = record
        self._bundles = loaded_bundles
