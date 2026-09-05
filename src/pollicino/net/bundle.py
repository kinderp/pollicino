from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import os
from pathlib import Path
import struct
from typing import Any, Callable, Mapping

from .link import ScarceLinkProfile, transmit_exact
from .persistence import _atomic_write_bytes
from .store import ChunkManifest
from .store_forward import ForwardContactReport, ForwardPeer, forward_contact
from .trc import TransferWireBreakdown, classify_transfer_wire
from .wire import DiscoveryDescriptor


BUNDLE_MAGIC = b"PNB1"
BUNDLE_VERSION = 1
CUSTODY_MAGIC = b"PNC1"
CUSTODY_VERSION = 1
CUSTODY_LEDGER_SCHEMA = "pollicino-custody-ledger-v1"

# magic, version, bundle id, manifest fingerprint, discovery sha256,
# created_at_s, ttl_seconds, hop_limit, nonce, current_hop
_BUNDLE_HEADER = struct.Struct(">4sB32s32s32sQIHQH")
_BUNDLE_IDENTITY = struct.Struct(">4sB32s32sQIHQ")
# magic, version, bundle id, acquired_at_s, hop_count, verified chunks,
# complete flag, peer-id length
_CUSTODY_HEADER = struct.Struct(">4sB32sQHHBB")
_MAX_U16 = 0xFFFF
_MAX_U32 = 0xFFFFFFFF
_MAX_U64 = 0xFFFFFFFFFFFFFFFF
_MAX_PEER_ID_BYTES = 255
_MAX_TRANSFER_ID = 0xFFFFFFFF
TransferCallable = Callable[..., tuple[bytes, Any]]


def _require_u(name: str, value: int, maximum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise ValueError(f"{name} must be an integer in 0..{maximum}")


def _require_digest(name: str, value: bytes) -> None:
    if not isinstance(value, bytes) or len(value) != 32:
        raise ValueError(f"{name} must be exactly 32 bytes")


def _peer_bytes(peer_id: str) -> bytes:
    if not isinstance(peer_id, str) or not peer_id:
        raise ValueError("peer_id must be a non-empty string")
    try:
        encoded = peer_id.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("peer_id must be UTF-8 encodable") from exc
    if len(encoded) > _MAX_PEER_ID_BYTES:
        raise ValueError(f"peer_id exceeds {_MAX_PEER_ID_BYTES} UTF-8 bytes")
    return encoded


@dataclass(frozen=True, slots=True)
class ForwardBundle:
    """Immutable forwarding identity bound to PND1 discovery and PCM1 content.

    TTL and hop limit come from the discovery descriptor. ``current_hop`` is
    intentionally not part of the bundle identity: the same bundle retains one
    ID while custody moves between peers.
    """

    manifest_fingerprint: bytes
    discovery_sha256: bytes
    created_at_s: int
    ttl_seconds: int
    hop_limit: int
    nonce: int
    version: int = BUNDLE_VERSION

    def __post_init__(self) -> None:
        if self.version != BUNDLE_VERSION:
            raise ValueError(f"unsupported bundle version: {self.version}")
        _require_digest("manifest_fingerprint", self.manifest_fingerprint)
        _require_digest("discovery_sha256", self.discovery_sha256)
        _require_u("created_at_s", self.created_at_s, _MAX_U64)
        _require_u("ttl_seconds", self.ttl_seconds, _MAX_U32)
        _require_u("hop_limit", self.hop_limit, _MAX_U16)
        _require_u("nonce", self.nonce, _MAX_U64)

    @classmethod
    def from_descriptor(
        cls,
        manifest: ChunkManifest,
        descriptor: DiscoveryDescriptor,
        *,
        created_at_s: int,
    ) -> ForwardBundle:
        return cls(
            manifest_fingerprint=manifest.fingerprint,
            discovery_sha256=hashlib.sha256(descriptor.encode()).digest(),
            created_at_s=created_at_s,
            ttl_seconds=descriptor.ttl_seconds,
            hop_limit=descriptor.hop_limit,
            nonce=descriptor.nonce,
        )

    @property
    def bundle_id(self) -> bytes:
        identity = _BUNDLE_IDENTITY.pack(
            BUNDLE_MAGIC,
            self.version,
            self.manifest_fingerprint,
            self.discovery_sha256,
            self.created_at_s,
            self.ttl_seconds,
            self.hop_limit,
            self.nonce,
        )
        return hashlib.sha256(identity).digest()

    def expired(self, now_s: int) -> bool:
        _require_u("now_s", now_s, _MAX_U64)
        if now_s < self.created_at_s:
            return False
        return now_s - self.created_at_s >= self.ttl_seconds

    def encode_forward(self, current_hop: int) -> bytes:
        _require_u("current_hop", current_hop, _MAX_U16)
        return _BUNDLE_HEADER.pack(
            BUNDLE_MAGIC,
            self.version,
            self.bundle_id,
            self.manifest_fingerprint,
            self.discovery_sha256,
            self.created_at_s,
            self.ttl_seconds,
            self.hop_limit,
            self.nonce,
            current_hop,
        )

    @classmethod
    def decode_forward(cls, data: bytes) -> tuple[ForwardBundle, int]:
        if not isinstance(data, bytes) or len(data) != _BUNDLE_HEADER.size:
            raise ValueError("invalid PNB1 forwarding envelope length")
        (
            magic,
            version,
            bundle_id,
            manifest_fingerprint,
            discovery_sha256,
            created_at_s,
            ttl_seconds,
            hop_limit,
            nonce,
            current_hop,
        ) = _BUNDLE_HEADER.unpack(data)
        if magic != BUNDLE_MAGIC:
            raise ValueError("invalid PNB1 bundle magic")
        bundle = cls(
            version=version,
            manifest_fingerprint=manifest_fingerprint,
            discovery_sha256=discovery_sha256,
            created_at_s=created_at_s,
            ttl_seconds=ttl_seconds,
            hop_limit=hop_limit,
            nonce=nonce,
        )
        if not hmac.compare_digest(bundle.bundle_id, bundle_id):
            raise ValueError("PNB1 bundle identity mismatch")
        return bundle, current_hop


@dataclass(frozen=True, slots=True)
class CustodyRecord:
    bundle_id: bytes
    peer_id: str
    acquired_at_s: int
    hop_count: int
    verified_chunk_count: int
    complete: bool

    def __post_init__(self) -> None:
        _require_digest("bundle_id", self.bundle_id)
        _peer_bytes(self.peer_id)
        _require_u("acquired_at_s", self.acquired_at_s, _MAX_U64)
        _require_u("hop_count", self.hop_count, _MAX_U16)
        _require_u("verified_chunk_count", self.verified_chunk_count, _MAX_U16)
        if not isinstance(self.complete, bool):
            raise TypeError("complete must be bool")

    def encode_receipt(self) -> bytes:
        peer = _peer_bytes(self.peer_id)
        return _CUSTODY_HEADER.pack(
            CUSTODY_MAGIC,
            CUSTODY_VERSION,
            self.bundle_id,
            self.acquired_at_s,
            self.hop_count,
            self.verified_chunk_count,
            1 if self.complete else 0,
            len(peer),
        ) + peer

    @classmethod
    def decode_receipt(cls, data: bytes) -> CustodyRecord:
        if not isinstance(data, bytes) or len(data) < _CUSTODY_HEADER.size:
            raise ValueError("custody receipt is truncated")
        (
            magic,
            version,
            bundle_id,
            acquired_at_s,
            hop_count,
            verified_chunk_count,
            complete,
            peer_len,
        ) = _CUSTODY_HEADER.unpack_from(data)
        if magic != CUSTODY_MAGIC or version != CUSTODY_VERSION:
            raise ValueError("unsupported custody receipt")
        if complete not in {0, 1}:
            raise ValueError("invalid custody complete flag")
        if len(data) != _CUSTODY_HEADER.size + peer_len:
            raise ValueError("custody receipt length mismatch")
        try:
            peer_id = data[_CUSTODY_HEADER.size :].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("custody peer_id is not UTF-8") from exc
        return cls(
            bundle_id=bundle_id,
            peer_id=peer_id,
            acquired_at_s=acquired_at_s,
            hop_count=hop_count,
            verified_chunk_count=verified_chunk_count,
            complete=bool(complete),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id.hex(),
            "peer_id": self.peer_id,
            "acquired_at_s": self.acquired_at_s,
            "hop_count": self.hop_count,
            "verified_chunk_count": self.verified_chunk_count,
            "complete": self.complete,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> CustodyRecord:
        try:
            bundle_id = bytes.fromhex(str(value["bundle_id"]))
        except (KeyError, ValueError) as exc:
            raise ValueError("invalid custody bundle_id") from exc
        peer_id = value.get("peer_id")
        complete = value.get("complete")
        if not isinstance(peer_id, str) or not peer_id:
            raise ValueError("custody peer_id must be a non-empty string")
        if not isinstance(complete, bool):
            raise ValueError("custody complete must be boolean")
        return cls(
            bundle_id=bundle_id,
            peer_id=peer_id,
            acquired_at_s=int(value["acquired_at_s"]),
            hop_count=int(value["hop_count"]),
            verified_chunk_count=int(value["verified_chunk_count"]),
            complete=complete,
        )


class CustodyLedger:
    """Local custody and idempotency state for deterministic experiments."""

    def __init__(self) -> None:
        self._records: dict[tuple[bytes, str], CustodyRecord] = {}
        self._contacts: set[tuple[bytes, str]] = set()

    def get(self, bundle_id: bytes, peer_id: str) -> CustodyRecord | None:
        _require_digest("bundle_id", bundle_id)
        _peer_bytes(peer_id)
        return self._records.get((bundle_id, peer_id))

    def record(self, record: CustodyRecord) -> CustodyRecord:
        key = (record.bundle_id, record.peer_id)
        previous = self._records.get(key)
        if previous is not None:
            # Preserve the shortest known path while refreshing actual verified
            # inventory. This avoids increasing a peer's hop distance merely
            # because it saw the same bundle later via a longer route.
            record = CustodyRecord(
                bundle_id=record.bundle_id,
                peer_id=record.peer_id,
                acquired_at_s=min(previous.acquired_at_s, record.acquired_at_s),
                hop_count=min(previous.hop_count, record.hop_count),
                verified_chunk_count=record.verified_chunk_count,
                complete=record.complete,
            )
        self._records[key] = record
        return record

    def contact_seen(self, bundle_id: bytes, contact_id: str) -> bool:
        _require_digest("bundle_id", bundle_id)
        if not isinstance(contact_id, str) or not contact_id:
            raise ValueError("contact_id must be a non-empty string")
        return (bundle_id, contact_id) in self._contacts

    def mark_contact(self, bundle_id: bytes, contact_id: str) -> None:
        if self.contact_seen(bundle_id, contact_id):
            return
        self._contacts.add((bundle_id, contact_id))

    def to_dict(self) -> dict[str, Any]:
        records = sorted(
            (record.to_dict() for record in self._records.values()),
            key=lambda item: (item["bundle_id"], item["peer_id"]),
        )
        contacts = sorted(
            (
                {"bundle_id": bundle_id.hex(), "contact_id": contact_id}
                for bundle_id, contact_id in self._contacts
            ),
            key=lambda item: (item["bundle_id"], item["contact_id"]),
        )
        return {
            "schema": CUSTODY_LEDGER_SCHEMA,
            "records": records,
            "processed_contacts": contacts,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> CustodyLedger:
        if value.get("schema") != CUSTODY_LEDGER_SCHEMA:
            raise ValueError("unsupported custody ledger schema")
        records = value.get("records")
        contacts = value.get("processed_contacts")
        if not isinstance(records, list) or not isinstance(contacts, list):
            raise ValueError("custody ledger records/contacts must be lists")
        ledger = cls()
        for item in records:
            if not isinstance(item, Mapping):
                raise ValueError("custody record must be an object")
            ledger.record(CustodyRecord.from_dict(item))
        for item in contacts:
            if not isinstance(item, Mapping):
                raise ValueError("processed contact must be an object")
            try:
                bundle_id = bytes.fromhex(str(item["bundle_id"]))
            except (KeyError, ValueError) as exc:
                raise ValueError("invalid processed contact bundle_id") from exc
            contact_id = item.get("contact_id")
            if not isinstance(contact_id, str) or not contact_id:
                raise ValueError("processed contact_id must be a non-empty string")
            ledger.mark_contact(bundle_id, contact_id)
        return ledger


@dataclass(frozen=True, slots=True)
class GovernedContactReport:
    contact_id: str
    source_id: str
    target_id: str
    disposition: str
    source_hop_count: int
    target_hop_count: int | None
    bundle_primary_data_wire_bytes: int
    custody_primary_data_wire_bytes: int
    governance_primary_ack_wire_bytes: int
    governance_retransmission_data_wire_bytes: int
    governance_retransmission_ack_wire_bytes: int
    governance_unknown_remote_failure_count: int
    accounting: str
    next_transfer_id: int
    inner: ForwardContactReport | None

    @property
    def duplicate_suppressed(self) -> bool:
        return self.disposition == "duplicate_suppressed"

    @property
    def total_wire_bytes(self) -> int:
        inner_bytes = 0 if self.inner is None else self.inner.total_wire_bytes
        return (
            self.bundle_primary_data_wire_bytes
            + self.custody_primary_data_wire_bytes
            + self.governance_primary_ack_wire_bytes
            + self.governance_retransmission_data_wire_bytes
            + self.governance_retransmission_ack_wire_bytes
            + inner_bytes
        )


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def save_custody_ledger(path: str | os.PathLike[str], ledger: CustodyLedger) -> Path:
    if not isinstance(ledger, CustodyLedger):
        raise TypeError("ledger must be CustodyLedger")
    destination = Path(path)
    body = ledger.to_dict()
    canonical = _canonical_bytes(body)
    envelope = {
        "schema": CUSTODY_LEDGER_SCHEMA,
        "ledger": body,
        "ledger_sha256": hashlib.sha256(canonical).hexdigest(),
    }
    encoded = (
        json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("utf-8")
    _atomic_write_bytes(destination, encoded)
    return destination


def load_custody_ledger(path: str | os.PathLike[str]) -> CustodyLedger:
    source = Path(path)
    try:
        envelope = json.loads(source.read_bytes())
    except FileNotFoundError as exc:
        raise LookupError("custody ledger does not exist") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("custody ledger is not valid UTF-8 JSON") from exc
    if not isinstance(envelope, Mapping) or envelope.get("schema") != CUSTODY_LEDGER_SCHEMA:
        raise ValueError("unsupported custody ledger envelope")
    body = envelope.get("ledger")
    if not isinstance(body, Mapping):
        raise ValueError("custody ledger body must be an object")
    expected = envelope.get("ledger_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError("custody ledger checksum is missing or invalid")
    actual = hashlib.sha256(_canonical_bytes(body)).hexdigest()
    if not hmac.compare_digest(actual, expected):
        raise ValueError("custody ledger checksum mismatch")
    return CustodyLedger.from_dict(body)


def seed_bundle_custody(
    bundle: ForwardBundle,
    manifest: ChunkManifest,
    *,
    origin: ForwardPeer,
    ledger: CustodyLedger,
    now_s: int,
) -> CustodyRecord:
    if bundle.manifest_fingerprint != manifest.fingerprint:
        raise ValueError("bundle manifest fingerprint mismatch")
    if not origin.store.has(manifest.fingerprint):
        raise ValueError("origin lacks verified PCM1 manifest")
    missing = [ref for ref in manifest.chunks if not origin.store.has(ref.sha256_digest)]
    if missing:
        raise ValueError("origin must possess every verified chunk before seeding custody")
    record = CustodyRecord(
        bundle_id=bundle.bundle_id,
        peer_id=origin.peer_id,
        acquired_at_s=now_s,
        hop_count=0,
        verified_chunk_count=len(manifest.chunks),
        complete=True,
    )
    return ledger.record(record)


def _next_id(value: int) -> tuple[int, int]:
    if not 0 <= value <= _MAX_TRANSFER_ID:
        raise ValueError("PNF1 transfer-id space is exhausted for governed contact")
    return value, value + 1


def _blocked_report(
    *,
    contact_id: str,
    source: ForwardPeer,
    target: ForwardPeer,
    disposition: str,
    source_hop_count: int,
    target_hop_count: int | None,
    transfer_id_base: int,
) -> GovernedContactReport:
    return GovernedContactReport(
        contact_id=contact_id,
        source_id=source.peer_id,
        target_id=target.peer_id,
        disposition=disposition,
        source_hop_count=source_hop_count,
        target_hop_count=target_hop_count,
        bundle_primary_data_wire_bytes=0,
        custody_primary_data_wire_bytes=0,
        governance_primary_ack_wire_bytes=0,
        governance_retransmission_data_wire_bytes=0,
        governance_retransmission_ack_wire_bytes=0,
        governance_unknown_remote_failure_count=0,
        accounting="none",
        next_transfer_id=transfer_id_base,
        inner=None,
    )


def governed_forward_contact(
    bundle: ForwardBundle,
    manifest: ChunkManifest,
    *,
    source: ForwardPeer,
    target: ForwardPeer,
    ledger: CustodyLedger,
    profile: ScarceLinkProfile,
    transfer_id_base: int,
    max_chunks: int,
    contact_id: str,
    now_s: int,
    transmitter: TransferCallable | None = None,
) -> tuple[bytes | None, GovernedContactReport]:
    """Apply TTL/hop/custody/idempotency around one store-forward contact.

    Duplicate suppression is intentionally scoped to an explicit ``contact_id``.
    Replaying the same scheduled encounter is zero-wire; a genuinely new
    encounter must use a new ID and will still rely on PNA1 to suppress already
    stored chunks.
    """

    if bundle.manifest_fingerprint != manifest.fingerprint:
        raise ValueError("bundle manifest fingerprint mismatch")
    if not isinstance(contact_id, str) or not contact_id:
        raise ValueError("contact_id must be a non-empty string")
    _require_u("now_s", now_s, _MAX_U64)
    _require_u("transfer_id_base", transfer_id_base, _MAX_TRANSFER_ID)

    source_record = ledger.get(bundle.bundle_id, source.peer_id)
    if source_record is None:
        raise ValueError("source peer does not hold custody for this bundle")

    if ledger.contact_seen(bundle.bundle_id, contact_id):
        return None, _blocked_report(
            contact_id=contact_id,
            source=source,
            target=target,
            disposition="duplicate_suppressed",
            source_hop_count=source_record.hop_count,
            target_hop_count=None,
            transfer_id_base=transfer_id_base,
        )

    if bundle.expired(now_s):
        ledger.mark_contact(bundle.bundle_id, contact_id)
        return None, _blocked_report(
            contact_id=contact_id,
            source=source,
            target=target,
            disposition="expired",
            source_hop_count=source_record.hop_count,
            target_hop_count=None,
            transfer_id_base=transfer_id_base,
        )

    target_hop = source_record.hop_count + 1
    if target_hop > bundle.hop_limit:
        ledger.mark_contact(bundle.bundle_id, contact_id)
        return None, _blocked_report(
            contact_id=contact_id,
            source=source,
            target=target,
            disposition="hop_limit_exhausted",
            source_hop_count=source_record.hop_count,
            target_hop_count=target_hop,
            transfer_id_base=transfer_id_base,
        )

    transfer: TransferCallable = transmit_exact if transmitter is None else transmitter
    if not callable(transfer):
        raise TypeError("transmitter must be callable")

    next_transfer_id = transfer_id_base
    accounting: str | None = None
    governance_ack = 0
    governance_retry_data = 0
    governance_retry_ack = 0
    governance_unknown = 0

    def move(payload: bytes) -> tuple[bytes, TransferWireBreakdown]:
        nonlocal next_transfer_id, accounting
        nonlocal governance_ack, governance_retry_data, governance_retry_ack, governance_unknown
        transfer_id, next_transfer_id = _next_id(next_transfer_id)
        received, report = transfer(payload, transfer_id=transfer_id, profile=profile)
        breakdown = classify_transfer_wire(
            payload, transfer_id=transfer_id, profile=profile, report=report
        )
        if accounting is None:
            accounting = breakdown.accounting
        elif accounting != breakdown.accounting:
            raise ValueError("cannot mix wire-accounting semantics in governed contact")
        governance_ack += breakdown.primary_ack_wire_bytes
        governance_retry_data += breakdown.retransmission_data_wire_bytes
        governance_retry_ack += breakdown.retransmission_ack_wire_bytes
        governance_unknown += breakdown.unknown_remote_failure_count
        return received, breakdown

    envelope_payload = bundle.encode_forward(target_hop)
    received_envelope, envelope_breakdown = move(envelope_payload)
    decoded_bundle, decoded_hop = ForwardBundle.decode_forward(received_envelope)
    if decoded_bundle != bundle or decoded_hop != target_hop:
        raise ValueError("PNB1 forwarding envelope changed in transit")

    reconstructed, inner = forward_contact(
        manifest,
        source=source,
        target=target,
        profile=profile,
        transfer_id_base=next_transfer_id,
        max_chunks=max_chunks,
        transmitter=transmitter,
    )
    next_transfer_id = inner.next_transfer_id
    if accounting is None:
        accounting = inner.accounting
    elif inner.accounting != "none" and accounting != inner.accounting:
        raise ValueError("cannot mix wire-accounting semantics in governed contact")

    verified_chunks = sum(
        1 for ref in manifest.chunks if target.store.has(ref.sha256_digest)
    )
    complete = target.store.has(manifest.fingerprint) and verified_chunks == len(manifest.chunks)
    receipt = CustodyRecord(
        bundle_id=bundle.bundle_id,
        peer_id=target.peer_id,
        acquired_at_s=now_s,
        hop_count=target_hop,
        verified_chunk_count=verified_chunks,
        complete=complete,
    )
    receipt_payload = receipt.encode_receipt()
    received_receipt_wire, receipt_breakdown = move(receipt_payload)
    received_receipt = CustodyRecord.decode_receipt(received_receipt_wire)
    if received_receipt != receipt:
        raise ValueError("custody receipt changed in transit")
    ledger.record(received_receipt)
    ledger.mark_contact(bundle.bundle_id, contact_id)

    return reconstructed, GovernedContactReport(
        contact_id=contact_id,
        source_id=source.peer_id,
        target_id=target.peer_id,
        disposition="forwarded",
        source_hop_count=source_record.hop_count,
        target_hop_count=target_hop,
        bundle_primary_data_wire_bytes=envelope_breakdown.primary_data_wire_bytes,
        custody_primary_data_wire_bytes=receipt_breakdown.primary_data_wire_bytes,
        governance_primary_ack_wire_bytes=governance_ack,
        governance_retransmission_data_wire_bytes=governance_retry_data,
        governance_retransmission_ack_wire_bytes=governance_retry_ack,
        governance_unknown_remote_failure_count=governance_unknown,
        accounting=accounting or inner.accounting,
        next_transfer_id=next_transfer_id,
        inner=inner,
    )
