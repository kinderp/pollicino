from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Mapping

from .net.link import ScarceLinkProfile
from .net.persistence import DirectoryPollicinoStore, _atomic_write_bytes
from .net.store import ChunkManifest, reconstruct_from_store
from .net.store_forward import (
    ForwardContactReport,
    ForwardPeer,
    forward_contact,
    seed_forwarding_object,
)


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


class PollicinoNodeRuntime:
    """Small persistent host-side vertical slice for a carried Pollicino node.

    The runtime intentionally reuses the existing PollicinoStore/PCM1/PNA1
    store-forward path. Modes are lifecycle context only: changing mode never
    rewrites object bytes, manifests, or chunk identity.

    This first slice persists the content store, known-manifest registry and
    current mode. PNB1/PNC1 custody remains governed by the existing campaign
    ledger and is not silently reimplemented here; node-local governed custody
    is a separate follow-up gate.
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
        self.store = DirectoryPollicinoStore(self._root / "store")
        self.peer = ForwardPeer(node_id, self.store)
        self._mode = NodeMode.DISCOVERING
        self._objects: dict[bytes, NodeObjectRecord] = {}

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

        # Once PCM1 itself is verified locally, retain knowledge of the object
        # even if only a subset of its chunks arrived during this contact.
        if self.store.has(manifest.fingerprint):
            label = ""
            if source.knows_manifest(manifest.fingerprint):
                label = source.object_record(manifest.fingerprint).label
            self._register_manifest(manifest, label=label)

        return NodeContactReport(
            source_mode=source.mode,
            target_mode=self.mode,
            forwarding=report,
        )

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

    def _state_mapping(self) -> dict[str, object]:
        return {
            "schema": NODE_STATE_SCHEMA,
            "node_id": self.node_id,
            "mode": self.mode.value,
            "objects": [
                self._objects[key].to_mapping()
                for key in sorted(self._objects)
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
        loaded: dict[bytes, NodeObjectRecord] = {}
        for value in objects:
            if not isinstance(value, Mapping):
                raise ValueError("node runtime object record must be an object")
            record = NodeObjectRecord.from_mapping(value)
            if record.manifest_fingerprint in loaded:
                raise ValueError("duplicate object in node runtime state")
            # State must never advertise a manifest that the verified store
            # cannot actually provide after restart.
            try:
                encoded_manifest = self.store.get(record.manifest_fingerprint)
            except LookupError as exc:
                raise ValueError("node runtime state references a missing manifest") from exc
            manifest = ChunkManifest.decode(encoded_manifest)
            if manifest.fingerprint != record.manifest_fingerprint:
                raise ValueError("node runtime state manifest failed verification")
            loaded[record.manifest_fingerprint] = record
        self._objects = loaded
