from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .link import ScarceLinkProfile, transmit_exact
from .store import (
    AvailabilitySummary,
    ChunkManifest,
    PollicinoStore,
    availability_for,
    build_chunk_manifest,
    reconstruct_from_store,
)
from .trc import classify_transfer_wire


EXACT_SESSION_SCHEMA = "pollicino-exact-sync-session-v1"
_CHUNK_INDEX_BYTES = 2
_MAX_TRANSFER_ID = 0xFFFFFFFF
_TRANSFER_ID_EXHAUSTED = _MAX_TRANSFER_ID + 1
TransferCallable = Callable[..., tuple[bytes, Any]]


@dataclass(frozen=True, slots=True)
class ExactSyncSessionState:
    """Serializable state for resumable exact chunk synchronization.

    Coordination lives above PNF1. Verified chunk bytes remain in the
    receiver's ``PollicinoStore``; durable store persistence is deliberately a
    separate concern.
    """

    manifest_fingerprint: bytes
    next_transfer_id: int
    manifest_on_scarce: bool
    manifest_delivered: bool
    step_count: int = 0
    cumulative_manifest_wire_bytes: int = 0
    cumulative_availability_wire_bytes: int = 0
    cumulative_chunk_wire_bytes: int = 0
    cumulative_retransmissions: int = 0
    cumulative_primary_data_wire_bytes: int = 0
    cumulative_primary_ack_wire_bytes: int = 0
    cumulative_retransmission_data_wire_bytes: int = 0
    cumulative_retransmission_ack_wire_bytes: int = 0
    cumulative_unknown_remote_failure_count: int = 0
    wire_accounting: str | None = None
    completed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.manifest_fingerprint, bytes) or len(self.manifest_fingerprint) != 32:
            raise ValueError("manifest_fingerprint must be exactly 32 bytes")
        if not isinstance(self.next_transfer_id, int) or not 0 <= self.next_transfer_id <= _TRANSFER_ID_EXHAUSTED:
            raise ValueError("next_transfer_id is out of range")
        if not isinstance(self.manifest_on_scarce, bool):
            raise TypeError("manifest_on_scarce must be bool")
        if not isinstance(self.manifest_delivered, bool):
            raise TypeError("manifest_delivered must be bool")
        if not self.manifest_on_scarce and not self.manifest_delivered:
            raise ValueError("pre-resolved manifest sessions must start with manifest_delivered=True")
        if self.wire_accounting is not None and (
            not isinstance(self.wire_accounting, str) or not self.wire_accounting
        ):
            raise ValueError("wire_accounting must be None or a non-empty string")
        for name, value in (
            ("step_count", self.step_count),
            ("cumulative_manifest_wire_bytes", self.cumulative_manifest_wire_bytes),
            ("cumulative_availability_wire_bytes", self.cumulative_availability_wire_bytes),
            ("cumulative_chunk_wire_bytes", self.cumulative_chunk_wire_bytes),
            ("cumulative_retransmissions", self.cumulative_retransmissions),
            ("cumulative_primary_data_wire_bytes", self.cumulative_primary_data_wire_bytes),
            ("cumulative_primary_ack_wire_bytes", self.cumulative_primary_ack_wire_bytes),
            (
                "cumulative_retransmission_data_wire_bytes",
                self.cumulative_retransmission_data_wire_bytes,
            ),
            (
                "cumulative_retransmission_ack_wire_bytes",
                self.cumulative_retransmission_ack_wire_bytes,
            ),
            (
                "cumulative_unknown_remote_failure_count",
                self.cumulative_unknown_remote_failure_count,
            ),
        ):
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

    @property
    def cumulative_wire_bytes(self) -> int:
        return (
            self.cumulative_manifest_wire_bytes
            + self.cumulative_availability_wire_bytes
            + self.cumulative_chunk_wire_bytes
        )

    @property
    def cumulative_primary_wire_bytes(self) -> int:
        return self.cumulative_primary_data_wire_bytes + self.cumulative_primary_ack_wire_bytes

    @property
    def cumulative_retransmission_wire_bytes(self) -> int:
        return (
            self.cumulative_retransmission_data_wire_bytes
            + self.cumulative_retransmission_ack_wire_bytes
        )

    @property
    def cumulative_breakdown_wire_bytes(self) -> int:
        return self.cumulative_primary_wire_bytes + self.cumulative_retransmission_wire_bytes

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": EXACT_SESSION_SCHEMA,
            "manifest_fingerprint_sha256": self.manifest_fingerprint.hex(),
            "next_transfer_id": self.next_transfer_id,
            "manifest_on_scarce": self.manifest_on_scarce,
            "manifest_delivered": self.manifest_delivered,
            "step_count": self.step_count,
            "cumulative_manifest_wire_bytes": self.cumulative_manifest_wire_bytes,
            "cumulative_availability_wire_bytes": self.cumulative_availability_wire_bytes,
            "cumulative_chunk_wire_bytes": self.cumulative_chunk_wire_bytes,
            "cumulative_wire_bytes": self.cumulative_wire_bytes,
            "cumulative_retransmissions": self.cumulative_retransmissions,
            "cumulative_primary_data_wire_bytes": self.cumulative_primary_data_wire_bytes,
            "cumulative_primary_ack_wire_bytes": self.cumulative_primary_ack_wire_bytes,
            "cumulative_retransmission_data_wire_bytes": self.cumulative_retransmission_data_wire_bytes,
            "cumulative_retransmission_ack_wire_bytes": self.cumulative_retransmission_ack_wire_bytes,
            "cumulative_primary_wire_bytes": self.cumulative_primary_wire_bytes,
            "cumulative_retransmission_wire_bytes": self.cumulative_retransmission_wire_bytes,
            "cumulative_breakdown_wire_bytes": self.cumulative_breakdown_wire_bytes,
            "cumulative_unknown_remote_failure_count": self.cumulative_unknown_remote_failure_count,
            "wire_accounting": self.wire_accounting,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> ExactSyncSessionState:
        if value.get("schema") != EXACT_SESSION_SCHEMA:
            raise ValueError("unsupported exact-session state schema")
        try:
            fingerprint = bytes.fromhex(str(value["manifest_fingerprint_sha256"]))
        except (KeyError, ValueError) as exc:
            raise ValueError("invalid manifest fingerprint in exact-session state") from exc
        manifest_on_scarce = value.get("manifest_on_scarce")
        manifest_delivered = value.get("manifest_delivered")
        if not isinstance(manifest_on_scarce, bool) or not isinstance(manifest_delivered, bool):
            raise ValueError("manifest flags in exact-session state must be booleans")
        wire_accounting = value.get("wire_accounting")
        return cls(
            manifest_fingerprint=fingerprint,
            next_transfer_id=int(value["next_transfer_id"]),
            manifest_on_scarce=manifest_on_scarce,
            manifest_delivered=manifest_delivered,
            step_count=int(value.get("step_count", 0)),
            cumulative_manifest_wire_bytes=int(value.get("cumulative_manifest_wire_bytes", 0)),
            cumulative_availability_wire_bytes=int(value.get("cumulative_availability_wire_bytes", 0)),
            cumulative_chunk_wire_bytes=int(value.get("cumulative_chunk_wire_bytes", 0)),
            cumulative_retransmissions=int(value.get("cumulative_retransmissions", 0)),
            cumulative_primary_data_wire_bytes=int(value.get("cumulative_primary_data_wire_bytes", 0)),
            cumulative_primary_ack_wire_bytes=int(value.get("cumulative_primary_ack_wire_bytes", 0)),
            cumulative_retransmission_data_wire_bytes=int(
                value.get("cumulative_retransmission_data_wire_bytes", 0)
            ),
            cumulative_retransmission_ack_wire_bytes=int(
                value.get("cumulative_retransmission_ack_wire_bytes", 0)
            ),
            cumulative_unknown_remote_failure_count=int(
                value.get("cumulative_unknown_remote_failure_count", 0)
            ),
            wire_accounting=None if wire_accounting is None else str(wire_accounting),
            completed=bool(value.get("completed", False)),
        )


@dataclass(frozen=True, slots=True)
class ExactSyncStepReport:
    step_number: int
    cached_chunk_count_before: int
    missing_chunk_count_before: int
    transferred_chunk_indices: tuple[int, ...]
    transferred_source_bytes: int
    remaining_chunk_count: int
    manifest_wire_bytes: int
    availability_wire_bytes: int
    chunk_wire_bytes: int
    step_wire_bytes: int
    retransmissions: int
    primary_data_wire_bytes: int
    primary_ack_wire_bytes: int
    retransmission_data_wire_bytes: int
    retransmission_ack_wire_bytes: int
    unknown_remote_failure_count: int
    cumulative_wire_bytes: int
    cumulative_retransmissions: int
    wire_accounting: str
    next_transfer_id: int
    complete: bool
    exact: bool

    @property
    def primary_wire_bytes(self) -> int:
        return self.primary_data_wire_bytes + self.primary_ack_wire_bytes

    @property
    def retransmission_wire_bytes(self) -> int:
        return self.retransmission_data_wire_bytes + self.retransmission_ack_wire_bytes

    @property
    def breakdown_wire_bytes(self) -> int:
        return self.primary_wire_bytes + self.retransmission_wire_bytes

    @property
    def accounted_bits(self) -> int:
        return self.step_wire_bytes * 8


def _next_id(value: int) -> tuple[int, int]:
    if not 0 <= value <= _MAX_TRANSFER_ID:
        raise ValueError("PNF1 transfer-id space is exhausted for this session")
    return value, value + 1


def _missing_indices(manifest: ChunkManifest, store: PollicinoStore) -> list[int]:
    return [
        index
        for index, ref in enumerate(manifest.chunks)
        if not store.has(ref.sha256_digest)
    ]


def _new_state(
    manifest: ChunkManifest,
    *,
    transfer_id_base: int,
    manifest_on_scarce: bool,
) -> ExactSyncSessionState:
    if not isinstance(transfer_id_base, int) or not 0 <= transfer_id_base <= _MAX_TRANSFER_ID:
        raise ValueError("transfer_id_base must fit in an unsigned 32-bit integer")
    return ExactSyncSessionState(
        manifest_fingerprint=manifest.fingerprint,
        next_transfer_id=transfer_id_base,
        manifest_on_scarce=manifest_on_scarce,
        manifest_delivered=not manifest_on_scarce,
    )


def _merge_accounting(current: str | None, observed: str) -> str:
    if current is None:
        return observed
    if current != observed:
        raise ValueError(
            f"cannot mix wire-accounting semantics in one session: {current!r} vs {observed!r}"
        )
    return current


def sync_missing_chunks_step(
    data: bytes,
    *,
    chunk_size: int,
    sender_store: PollicinoStore,
    receiver_store: PollicinoStore,
    profile: ScarceLinkProfile,
    state: ExactSyncSessionState | None = None,
    transfer_id_base: int | None = None,
    max_chunks: int = 1,
    manifest_on_scarce: bool = True,
    transmitter: TransferCallable | None = None,
) -> tuple[bytes | None, ExactSyncSessionState, ExactSyncStepReport]:
    """Advance an exact synchronization session by at most ``max_chunks``.

    Resumability is provided at verified chunk boundaries. PNF1 itself remains
    unchanged. The default transmitter is the deterministic PN-002 simulator;
    callers may inject a compatible transfer primitive such as
    ``RFReplayTransmitter.transmit_exact``.

    The report uses non-overlapping primary/retransmission wire categories and
    preserves whether those bytes are exact model accounting or a physical
    replay lower bound.
    """

    if not isinstance(max_chunks, int) or max_chunks < 0:
        raise ValueError("max_chunks must be a non-negative integer")
    transfer: TransferCallable = transmit_exact if transmitter is None else transmitter
    if not callable(transfer):
        raise TypeError("transmitter must be callable")

    manifest, chunks = build_chunk_manifest(data, chunk_size=chunk_size)
    for chunk in chunks:
        sender_store.put(chunk)

    if state is None:
        if transfer_id_base is None:
            raise ValueError("transfer_id_base is required when starting a session")
        current = _new_state(
            manifest,
            transfer_id_base=transfer_id_base,
            manifest_on_scarce=manifest_on_scarce,
        )
    else:
        if transfer_id_base is not None:
            raise ValueError("transfer_id_base must be omitted when resuming a session")
        if state.manifest_fingerprint != manifest.fingerprint:
            raise ValueError("session state belongs to a different chunk manifest")
        if state.manifest_on_scarce != manifest_on_scarce:
            raise ValueError("manifest_on_scarce cannot change while resuming a session")
        current = state

    if current.completed:
        reconstructed = reconstruct_from_store(manifest, receiver_store)
        report = ExactSyncStepReport(
            step_number=current.step_count,
            cached_chunk_count_before=len(manifest.chunks),
            missing_chunk_count_before=0,
            transferred_chunk_indices=(),
            transferred_source_bytes=0,
            remaining_chunk_count=0,
            manifest_wire_bytes=0,
            availability_wire_bytes=0,
            chunk_wire_bytes=0,
            step_wire_bytes=0,
            retransmissions=0,
            primary_data_wire_bytes=0,
            primary_ack_wire_bytes=0,
            retransmission_data_wire_bytes=0,
            retransmission_ack_wire_bytes=0,
            unknown_remote_failure_count=0,
            cumulative_wire_bytes=current.cumulative_wire_bytes,
            cumulative_retransmissions=current.cumulative_retransmissions,
            wire_accounting=current.wire_accounting or "none",
            next_transfer_id=current.next_transfer_id,
            complete=True,
            exact=reconstructed == data,
        )
        return reconstructed, current, report

    next_transfer_id = current.next_transfer_id
    manifest_wire_bytes = 0
    availability_wire_bytes = 0
    chunk_wire_bytes = 0
    retransmissions = 0
    primary_data_wire_bytes = 0
    primary_ack_wire_bytes = 0
    retransmission_data_wire_bytes = 0
    retransmission_ack_wire_bytes = 0
    unknown_remote_failure_count = 0
    manifest_delivered = current.manifest_delivered
    wire_accounting = current.wire_accounting

    def account(payload: bytes, transfer_id: int, transfer_report: Any) -> int:
        nonlocal wire_accounting
        nonlocal primary_data_wire_bytes, primary_ack_wire_bytes
        nonlocal retransmission_data_wire_bytes, retransmission_ack_wire_bytes
        nonlocal unknown_remote_failure_count
        breakdown = classify_transfer_wire(
            payload,
            transfer_id=transfer_id,
            profile=profile,
            report=transfer_report,
        )
        wire_accounting = _merge_accounting(wire_accounting, breakdown.accounting)
        primary_data_wire_bytes += breakdown.primary_data_wire_bytes
        primary_ack_wire_bytes += breakdown.primary_ack_wire_bytes
        retransmission_data_wire_bytes += breakdown.retransmission_data_wire_bytes
        retransmission_ack_wire_bytes += breakdown.retransmission_ack_wire_bytes
        unknown_remote_failure_count += breakdown.unknown_remote_failure_count
        return breakdown.accounted_wire_bytes

    if current.manifest_on_scarce and not manifest_delivered:
        manifest_payload = manifest.encode()
        transfer_id, next_transfer_id = _next_id(next_transfer_id)
        received_manifest_wire, transfer_report = transfer(
            manifest_payload,
            transfer_id=transfer_id,
            profile=profile,
        )
        received_manifest = ChunkManifest.decode(received_manifest_wire)
        if received_manifest != manifest:
            raise AssertionError("chunk manifest changed during exact transfer")
        manifest_wire_bytes += account(manifest_payload, transfer_id, transfer_report)
        retransmissions += int(transfer_report.retransmissions)
        manifest_delivered = True

    summary = availability_for(manifest, receiver_store)
    summary_payload = summary.encode()
    transfer_id, next_transfer_id = _next_id(next_transfer_id)
    received_summary_wire, summary_report = transfer(
        summary_payload,
        transfer_id=transfer_id,
        profile=profile,
    )
    received_summary = AvailabilitySummary.decode(received_summary_wire)
    if received_summary.manifest_fingerprint != manifest.fingerprint:
        raise ValueError("availability summary targets a different chunk manifest")
    availability_wire_bytes += account(summary_payload, transfer_id, summary_report)
    retransmissions += int(summary_report.retransmissions)

    missing_before = [
        index for index in range(len(manifest.chunks)) if not received_summary.has(index)
    ]
    cached_before = len(manifest.chunks) - len(missing_before)
    selected = missing_before[:max_chunks]
    transferred_source_bytes = 0

    for index in selected:
        ref = manifest.chunks[index]
        source_chunk = sender_store.get(ref.sha256_digest)
        packet = index.to_bytes(_CHUNK_INDEX_BYTES, "big") + source_chunk
        transfer_id, next_transfer_id = _next_id(next_transfer_id)
        received_packet, chunk_report = transfer(
            packet,
            transfer_id=transfer_id,
            profile=profile,
        )
        if len(received_packet) < _CHUNK_INDEX_BYTES:
            raise ValueError("received chunk packet is truncated")
        received_index = int.from_bytes(received_packet[:_CHUNK_INDEX_BYTES], "big")
        if received_index != index:
            raise ValueError("received chunk packet index mismatch")
        received_chunk = received_packet[_CHUNK_INDEX_BYTES:]
        if len(received_chunk) != ref.length:
            raise ValueError("received chunk length does not match manifest")
        digest = receiver_store.put(received_chunk)
        if digest != ref.sha256_digest:
            raise ValueError("received chunk failed manifest SHA-256 verification")
        chunk_wire_bytes += account(packet, transfer_id, chunk_report)
        retransmissions += int(chunk_report.retransmissions)
        transferred_source_bytes += ref.length

    remaining = _missing_indices(manifest, receiver_store)
    complete = not remaining
    reconstructed: bytes | None = None
    exact = False
    if complete:
        reconstructed = reconstruct_from_store(manifest, receiver_store)
        exact = reconstructed == data
        if not exact:
            raise AssertionError("completed exact session reconstructed different bytes")

    step_wire_bytes = manifest_wire_bytes + availability_wire_bytes + chunk_wire_bytes
    breakdown_wire_bytes = (
        primary_data_wire_bytes
        + primary_ack_wire_bytes
        + retransmission_data_wire_bytes
        + retransmission_ack_wire_bytes
    )
    if breakdown_wire_bytes != step_wire_bytes:
        raise AssertionError("TRC wire breakdown does not equal logical session wire accounting")

    next_state = ExactSyncSessionState(
        manifest_fingerprint=current.manifest_fingerprint,
        next_transfer_id=next_transfer_id,
        manifest_on_scarce=current.manifest_on_scarce,
        manifest_delivered=manifest_delivered,
        step_count=current.step_count + 1,
        cumulative_manifest_wire_bytes=(
            current.cumulative_manifest_wire_bytes + manifest_wire_bytes
        ),
        cumulative_availability_wire_bytes=(
            current.cumulative_availability_wire_bytes + availability_wire_bytes
        ),
        cumulative_chunk_wire_bytes=current.cumulative_chunk_wire_bytes + chunk_wire_bytes,
        cumulative_retransmissions=current.cumulative_retransmissions + retransmissions,
        cumulative_primary_data_wire_bytes=(
            current.cumulative_primary_data_wire_bytes + primary_data_wire_bytes
        ),
        cumulative_primary_ack_wire_bytes=(
            current.cumulative_primary_ack_wire_bytes + primary_ack_wire_bytes
        ),
        cumulative_retransmission_data_wire_bytes=(
            current.cumulative_retransmission_data_wire_bytes + retransmission_data_wire_bytes
        ),
        cumulative_retransmission_ack_wire_bytes=(
            current.cumulative_retransmission_ack_wire_bytes + retransmission_ack_wire_bytes
        ),
        cumulative_unknown_remote_failure_count=(
            current.cumulative_unknown_remote_failure_count + unknown_remote_failure_count
        ),
        wire_accounting=wire_accounting,
        completed=complete,
    )
    if next_state.cumulative_breakdown_wire_bytes != next_state.cumulative_wire_bytes:
        raise AssertionError("cumulative TRC breakdown diverged from session wire accounting")

    report = ExactSyncStepReport(
        step_number=next_state.step_count,
        cached_chunk_count_before=cached_before,
        missing_chunk_count_before=len(missing_before),
        transferred_chunk_indices=tuple(selected),
        transferred_source_bytes=transferred_source_bytes,
        remaining_chunk_count=len(remaining),
        manifest_wire_bytes=manifest_wire_bytes,
        availability_wire_bytes=availability_wire_bytes,
        chunk_wire_bytes=chunk_wire_bytes,
        step_wire_bytes=step_wire_bytes,
        retransmissions=retransmissions,
        primary_data_wire_bytes=primary_data_wire_bytes,
        primary_ack_wire_bytes=primary_ack_wire_bytes,
        retransmission_data_wire_bytes=retransmission_data_wire_bytes,
        retransmission_ack_wire_bytes=retransmission_ack_wire_bytes,
        unknown_remote_failure_count=unknown_remote_failure_count,
        cumulative_wire_bytes=next_state.cumulative_wire_bytes,
        cumulative_retransmissions=next_state.cumulative_retransmissions,
        wire_accounting=wire_accounting or "none",
        next_transfer_id=next_state.next_transfer_id,
        complete=complete,
        exact=exact,
    )
    return reconstructed, next_state, report
