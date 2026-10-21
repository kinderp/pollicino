from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from .content import ContentManifest
from .link import ScarceLinkProfile, transmit_exact
from .store import (
    AvailabilitySummary,
    ChunkManifest,
    PollicinoStore,
    availability_for,
    build_chunk_manifest,
    reconstruct_from_store,
)
from .trc import TransferWireBreakdown, classify_transfer_wire
from .wire import DiscoveryDescriptor


_CHUNK_INDEX_BYTES = 2
_MAX_TRANSFER_ID = 0xFFFFFFFF
TransferCallable = Callable[..., tuple[bytes, Any]]


@dataclass(frozen=True, slots=True)
class ForwardPeer:
    peer_id: str
    store: PollicinoStore

    def __post_init__(self) -> None:
        if not isinstance(self.peer_id, str) or not self.peer_id:
            raise ValueError("peer_id must be a non-empty string")
        if not isinstance(self.store, PollicinoStore):
            raise TypeError("store must implement the PollicinoStore contract")


@dataclass(frozen=True, slots=True)
class ForwardContact:
    source_id: str
    target_id: str
    transfer_id_base: int
    max_chunks: int

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id:
            raise ValueError("source_id must be a non-empty string")
        if not isinstance(self.target_id, str) or not self.target_id:
            raise ValueError("target_id must be a non-empty string")
        if self.source_id == self.target_id:
            raise ValueError("source_id and target_id must differ")
        if not isinstance(self.transfer_id_base, int) or not 0 <= self.transfer_id_base <= _MAX_TRANSFER_ID:
            raise ValueError("transfer_id_base must fit in an unsigned 32-bit integer")
        if not isinstance(self.max_chunks, int) or self.max_chunks < 0:
            raise ValueError("max_chunks must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class ForwardContactReport:
    source_id: str
    target_id: str
    cached_chunk_count_before: int
    missing_chunk_count_before: int
    source_available_missing_count: int
    transferred_chunk_indices: tuple[int, ...]
    transferred_source_bytes: int
    remaining_chunk_count: int
    manifest_sent: bool
    manifest_primary_data_wire_bytes: int
    availability_primary_data_wire_bytes: int
    payload_primary_data_wire_bytes: int
    primary_ack_wire_bytes: int
    retransmission_data_wire_bytes: int
    retransmission_ack_wire_bytes: int
    unknown_remote_failure_count: int
    next_transfer_id: int
    accounting: str
    target_complete: bool
    target_exact: bool

    @property
    def primary_data_wire_bytes(self) -> int:
        return (
            self.manifest_primary_data_wire_bytes
            + self.availability_primary_data_wire_bytes
            + self.payload_primary_data_wire_bytes
        )

    @property
    def primary_wire_bytes(self) -> int:
        return self.primary_data_wire_bytes + self.primary_ack_wire_bytes

    @property
    def retransmission_wire_bytes(self) -> int:
        return self.retransmission_data_wire_bytes + self.retransmission_ack_wire_bytes

    @property
    def total_wire_bytes(self) -> int:
        return self.primary_wire_bytes + self.retransmission_wire_bytes


@dataclass(frozen=True, slots=True)
class StoreForwardRouteReport:
    destination_id: str
    contacts: tuple[ForwardContactReport, ...]
    destination_complete: bool
    destination_exact: bool

    @property
    def manifest_primary_data_wire_bytes(self) -> int:
        return sum(item.manifest_primary_data_wire_bytes for item in self.contacts)

    @property
    def availability_primary_data_wire_bytes(self) -> int:
        return sum(item.availability_primary_data_wire_bytes for item in self.contacts)

    @property
    def payload_primary_data_wire_bytes(self) -> int:
        return sum(item.payload_primary_data_wire_bytes for item in self.contacts)

    @property
    def primary_ack_wire_bytes(self) -> int:
        return sum(item.primary_ack_wire_bytes for item in self.contacts)

    @property
    def retransmission_data_wire_bytes(self) -> int:
        return sum(item.retransmission_data_wire_bytes for item in self.contacts)

    @property
    def retransmission_ack_wire_bytes(self) -> int:
        return sum(item.retransmission_ack_wire_bytes for item in self.contacts)

    @property
    def unknown_remote_failure_count(self) -> int:
        return sum(item.unknown_remote_failure_count for item in self.contacts)

    @property
    def total_wire_bytes(self) -> int:
        return sum(item.total_wire_bytes for item in self.contacts)


@dataclass(frozen=True, slots=True)
class EndToEndTRCReport:
    discovery_wire_bytes: int
    rendezvous_wire_bytes: int
    chunk_manifest_primary_data_wire_bytes: int
    availability_primary_data_wire_bytes: int
    payload_primary_data_wire_bytes: int
    primary_ack_wire_bytes: int
    retransmission_data_wire_bytes: int
    retransmission_ack_wire_bytes: int
    fec_wire_bytes: int
    unknown_remote_failure_count: int
    route_accounting: tuple[str, ...]
    exact: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("discovery_wire_bytes", self.discovery_wire_bytes),
            ("rendezvous_wire_bytes", self.rendezvous_wire_bytes),
            ("chunk_manifest_primary_data_wire_bytes", self.chunk_manifest_primary_data_wire_bytes),
            ("availability_primary_data_wire_bytes", self.availability_primary_data_wire_bytes),
            ("payload_primary_data_wire_bytes", self.payload_primary_data_wire_bytes),
            ("primary_ack_wire_bytes", self.primary_ack_wire_bytes),
            ("retransmission_data_wire_bytes", self.retransmission_data_wire_bytes),
            ("retransmission_ack_wire_bytes", self.retransmission_ack_wire_bytes),
            ("fec_wire_bytes", self.fec_wire_bytes),
            ("unknown_remote_failure_count", self.unknown_remote_failure_count),
        ):
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

    @property
    def primary_data_wire_bytes(self) -> int:
        return (
            self.discovery_wire_bytes
            + self.rendezvous_wire_bytes
            + self.chunk_manifest_primary_data_wire_bytes
            + self.availability_primary_data_wire_bytes
            + self.payload_primary_data_wire_bytes
            + self.fec_wire_bytes
        )

    @property
    def retransmission_wire_bytes(self) -> int:
        return self.retransmission_data_wire_bytes + self.retransmission_ack_wire_bytes

    @property
    def total_wire_bytes(self) -> int:
        return self.primary_data_wire_bytes + self.primary_ack_wire_bytes + self.retransmission_wire_bytes

    @property
    def total_bits(self) -> int:
        return self.total_wire_bytes * 8


def seed_forwarding_object(
    data: bytes,
    *,
    chunk_size: int,
    store: PollicinoStore,
) -> ChunkManifest:
    """Seed one peer with the verified PCM1 manifest and every object chunk."""

    manifest, chunks = build_chunk_manifest(data, chunk_size=chunk_size)
    manifest_digest = store.put(manifest.encode())
    if manifest_digest != manifest.fingerprint:
        raise AssertionError("stored PCM1 manifest fingerprint mismatch")
    for chunk in chunks:
        store.put(chunk)
    return manifest


def _next_id(value: int) -> tuple[int, int]:
    if not 0 <= value <= _MAX_TRANSFER_ID:
        raise ValueError("PNF1 transfer-id space is exhausted for this contact")
    return value, value + 1


def _merge_accounting(current: str | None, observed: str) -> str:
    if current is None:
        return observed
    if current != observed:
        raise ValueError(
            f"cannot mix wire-accounting semantics in one contact: {current!r} vs {observed!r}"
        )
    return current


def _accumulate(
    breakdown: TransferWireBreakdown,
    totals: dict[str, int],
) -> None:
    totals["primary_ack"] += breakdown.primary_ack_wire_bytes
    totals["retry_data"] += breakdown.retransmission_data_wire_bytes
    totals["retry_ack"] += breakdown.retransmission_ack_wire_bytes
    totals["unknown"] += breakdown.unknown_remote_failure_count


def forward_contact(
    manifest: ChunkManifest,
    *,
    source: ForwardPeer,
    target: ForwardPeer,
    profile: ScarceLinkProfile,
    transfer_id_base: int,
    max_chunks: int,
    transmitter: TransferCallable | None = None,
) -> tuple[bytes | None, ForwardContactReport]:
    """Run one finite directional contact between two intermittently connected peers.

    The source may forward only a manifest and chunks it can verify locally.
    The target advertises current verified availability, making later contacts
    naturally resumable without an end-to-end connection or hidden global
    session state.
    """

    if source.peer_id == target.peer_id:
        raise ValueError("source and target peers must differ")
    if not isinstance(max_chunks, int) or max_chunks < 0:
        raise ValueError("max_chunks must be a non-negative integer")
    if not isinstance(transfer_id_base, int) or not 0 <= transfer_id_base <= _MAX_TRANSFER_ID:
        raise ValueError("transfer_id_base must fit in an unsigned 32-bit integer")

    transfer: TransferCallable = transmit_exact if transmitter is None else transmitter
    if not callable(transfer):
        raise TypeError("transmitter must be callable")

    manifest_payload = manifest.encode()
    if not source.store.has(manifest.fingerprint):
        raise ValueError("source peer does not possess a verified PCM1 manifest")
    if source.store.get(manifest.fingerprint) != manifest_payload:
        raise ValueError("source PCM1 manifest bytes do not match the requested manifest")

    next_transfer_id = transfer_id_base
    accounting: str | None = None
    totals = {"primary_ack": 0, "retry_data": 0, "retry_ack": 0, "unknown": 0}
    manifest_primary = 0
    availability_primary = 0
    payload_primary = 0
    manifest_sent = False

    def move(payload: bytes) -> tuple[bytes, TransferWireBreakdown]:
        nonlocal next_transfer_id, accounting
        transfer_id, next_transfer_id = _next_id(next_transfer_id)
        received, report = transfer(payload, transfer_id=transfer_id, profile=profile)
        breakdown = classify_transfer_wire(
            payload,
            transfer_id=transfer_id,
            profile=profile,
            report=report,
        )
        accounting = _merge_accounting(accounting, breakdown.accounting)
        _accumulate(breakdown, totals)
        return received, breakdown

    if not target.store.has(manifest.fingerprint):
        received_manifest_wire, breakdown = move(manifest_payload)
        received_manifest = ChunkManifest.decode(received_manifest_wire)
        if received_manifest != manifest:
            raise ValueError("PCM1 manifest changed during store-and-forward contact")
        stored_digest = target.store.put(received_manifest_wire)
        if stored_digest != manifest.fingerprint:
            raise ValueError("target stored PCM1 manifest under an unexpected digest")
        manifest_primary += breakdown.primary_data_wire_bytes
        manifest_sent = True

    summary = availability_for(manifest, target.store)
    summary_payload = summary.encode()
    received_summary_wire, breakdown = move(summary_payload)
    received_summary = AvailabilitySummary.decode(received_summary_wire)
    if received_summary.manifest_fingerprint != manifest.fingerprint:
        raise ValueError("availability summary targets a different PCM1 manifest")
    availability_primary += breakdown.primary_data_wire_bytes

    missing_before = [
        index for index in range(len(manifest.chunks)) if not received_summary.has(index)
    ]
    cached_before = len(manifest.chunks) - len(missing_before)
    source_available = [
        index for index in missing_before if source.store.has(manifest.chunks[index].sha256_digest)
    ]
    selected = source_available[:max_chunks]
    transferred_source_bytes = 0

    for index in selected:
        ref = manifest.chunks[index]
        source_chunk = source.store.get(ref.sha256_digest)
        if len(source_chunk) != ref.length:
            raise ValueError("source chunk length does not match PCM1 manifest")
        packet = index.to_bytes(_CHUNK_INDEX_BYTES, "big") + source_chunk
        received_packet, breakdown = move(packet)
        if len(received_packet) < _CHUNK_INDEX_BYTES:
            raise ValueError("forwarded chunk packet is truncated")
        received_index = int.from_bytes(received_packet[:_CHUNK_INDEX_BYTES], "big")
        if received_index != index:
            raise ValueError("forwarded chunk packet index mismatch")
        received_chunk = received_packet[_CHUNK_INDEX_BYTES:]
        if len(received_chunk) != ref.length:
            raise ValueError("forwarded chunk length does not match PCM1 manifest")
        digest = target.store.put(received_chunk)
        if digest != ref.sha256_digest:
            raise ValueError("forwarded chunk failed PCM1 SHA-256 verification")
        payload_primary += breakdown.primary_data_wire_bytes
        transferred_source_bytes += ref.length

    remaining = [
        index
        for index, ref in enumerate(manifest.chunks)
        if not target.store.has(ref.sha256_digest)
    ]
    target_complete = not remaining
    reconstructed: bytes | None = None
    target_exact = False
    if target_complete:
        reconstructed = reconstruct_from_store(manifest, target.store)
        target_exact = True

    return reconstructed, ForwardContactReport(
        source_id=source.peer_id,
        target_id=target.peer_id,
        cached_chunk_count_before=cached_before,
        missing_chunk_count_before=len(missing_before),
        source_available_missing_count=len(source_available),
        transferred_chunk_indices=tuple(selected),
        transferred_source_bytes=transferred_source_bytes,
        remaining_chunk_count=len(remaining),
        manifest_sent=manifest_sent,
        manifest_primary_data_wire_bytes=manifest_primary,
        availability_primary_data_wire_bytes=availability_primary,
        payload_primary_data_wire_bytes=payload_primary,
        primary_ack_wire_bytes=totals["primary_ack"],
        retransmission_data_wire_bytes=totals["retry_data"],
        retransmission_ack_wire_bytes=totals["retry_ack"],
        unknown_remote_failure_count=totals["unknown"],
        next_transfer_id=next_transfer_id,
        accounting=accounting or "none",
        target_complete=target_complete,
        target_exact=target_exact,
    )


def run_store_forward_schedule(
    manifest: ChunkManifest,
    *,
    peers: Mapping[str, ForwardPeer],
    contacts: Sequence[ForwardContact],
    destination_id: str,
    profile: ScarceLinkProfile,
    transmitter: TransferCallable | None = None,
) -> tuple[bytes | None, StoreForwardRouteReport]:
    """Execute discrete contacts without assuming any permanent end-to-end path."""

    if destination_id not in peers:
        raise KeyError("destination peer is not present in peers")
    reports: list[ForwardContactReport] = []
    for contact in contacts:
        try:
            source = peers[contact.source_id]
            target = peers[contact.target_id]
        except KeyError as exc:
            raise KeyError(f"contact references unknown peer: {exc.args[0]}") from exc
        _, report = forward_contact(
            manifest,
            source=source,
            target=target,
            profile=profile,
            transfer_id_base=contact.transfer_id_base,
            max_chunks=contact.max_chunks,
            transmitter=transmitter,
        )
        reports.append(report)

    destination = peers[destination_id]
    remaining = [
        ref for ref in manifest.chunks if not destination.store.has(ref.sha256_digest)
    ]
    complete = not remaining and destination.store.has(manifest.fingerprint)
    reconstructed: bytes | None = None
    exact = False
    if complete:
        reconstructed = reconstruct_from_store(manifest, destination.store)
        exact = True

    return reconstructed, StoreForwardRouteReport(
        destination_id=destination_id,
        contacts=tuple(reports),
        destination_complete=complete,
        destination_exact=exact,
    )


def summarize_end_to_end_trc(
    route: StoreForwardRouteReport,
    *,
    descriptor: DiscoveryDescriptor | None = None,
    resolved_manifest: ContentManifest | None = None,
    discovery_transmissions: int = 0,
    rendezvous_transmissions: int = 0,
    fec_wire_bytes: int = 0,
) -> EndToEndTRCReport:
    """Add DISCOVERY/rendezvous bytes to the non-overlapping route wire account.

    ``discovery_transmissions`` and ``rendezvous_transmissions`` are explicit
    because a store-and-forward experiment may relay those objects zero, one,
    or multiple times. This function never silently assumes a topology.
    """

    for name, value in (
        ("discovery_transmissions", discovery_transmissions),
        ("rendezvous_transmissions", rendezvous_transmissions),
        ("fec_wire_bytes", fec_wire_bytes),
    ):
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    if descriptor is None and discovery_transmissions:
        raise ValueError("descriptor is required when discovery_transmissions is non-zero")
    if resolved_manifest is None and rendezvous_transmissions:
        raise ValueError("resolved_manifest is required when rendezvous_transmissions is non-zero")

    discovery_bytes = 0 if descriptor is None else len(descriptor.encode()) * discovery_transmissions
    rendezvous_bytes = (
        0 if resolved_manifest is None else len(resolved_manifest.encode()) * rendezvous_transmissions
    )
    accounting = tuple(sorted({item.accounting for item in route.contacts if item.accounting != "none"}))
    return EndToEndTRCReport(
        discovery_wire_bytes=discovery_bytes,
        rendezvous_wire_bytes=rendezvous_bytes,
        chunk_manifest_primary_data_wire_bytes=route.manifest_primary_data_wire_bytes,
        availability_primary_data_wire_bytes=route.availability_primary_data_wire_bytes,
        payload_primary_data_wire_bytes=route.payload_primary_data_wire_bytes,
        primary_ack_wire_bytes=route.primary_ack_wire_bytes,
        retransmission_data_wire_bytes=route.retransmission_data_wire_bytes,
        retransmission_ack_wire_bytes=route.retransmission_ack_wire_bytes,
        fec_wire_bytes=fec_wire_bytes,
        unknown_remote_failure_count=route.unknown_remote_failure_count,
        route_accounting=accounting,
        exact=route.destination_exact,
    )
