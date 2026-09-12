from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .bundle import (
    CustodyLedger,
    ForwardBundle,
    GovernedContactReport,
    TransferCallable,
    governed_forward_contact,
)
from .content import ContentManifest
from .link import ScarceLinkProfile
from .store import ChunkManifest, reconstruct_from_store
from .store_forward import ForwardPeer
from .wire import DiscoveryDescriptor


@dataclass(frozen=True, slots=True)
class GovernedForwardContact:
    source_id: str
    target_id: str
    transfer_id_base: int
    max_chunks: int
    contact_id: str
    now_s: int

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id:
            raise ValueError("source_id must be a non-empty string")
        if not isinstance(self.target_id, str) or not self.target_id:
            raise ValueError("target_id must be a non-empty string")
        if self.source_id == self.target_id:
            raise ValueError("source_id and target_id must differ")
        if not isinstance(self.contact_id, str) or not self.contact_id:
            raise ValueError("contact_id must be a non-empty string")
        if isinstance(self.transfer_id_base, bool) or not isinstance(self.transfer_id_base, int):
            raise ValueError("transfer_id_base must be an integer")
        if not 0 <= self.transfer_id_base <= 0xFFFFFFFF:
            raise ValueError("transfer_id_base must fit in an unsigned 32-bit integer")
        if isinstance(self.max_chunks, bool) or not isinstance(self.max_chunks, int) or self.max_chunks < 0:
            raise ValueError("max_chunks must be a non-negative integer")
        if isinstance(self.now_s, bool) or not isinstance(self.now_s, int) or self.now_s < 0:
            raise ValueError("now_s must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class GovernedRouteReport:
    destination_id: str
    contacts: tuple[GovernedContactReport, ...]
    destination_complete: bool
    destination_exact: bool

    @property
    def forwarded_contacts(self) -> int:
        return sum(item.disposition == "forwarded" for item in self.contacts)

    @property
    def duplicate_suppressed_contacts(self) -> int:
        return sum(item.disposition == "duplicate_suppressed" for item in self.contacts)

    @property
    def expired_contacts(self) -> int:
        return sum(item.disposition == "expired" for item in self.contacts)

    @property
    def hop_limited_contacts(self) -> int:
        return sum(item.disposition == "hop_limit_exhausted" for item in self.contacts)

    @property
    def bundle_primary_data_wire_bytes(self) -> int:
        return sum(item.bundle_primary_data_wire_bytes for item in self.contacts)

    @property
    def custody_primary_data_wire_bytes(self) -> int:
        return sum(item.custody_primary_data_wire_bytes for item in self.contacts)

    @property
    def governance_primary_ack_wire_bytes(self) -> int:
        return sum(item.governance_primary_ack_wire_bytes for item in self.contacts)

    @property
    def governance_retransmission_data_wire_bytes(self) -> int:
        return sum(item.governance_retransmission_data_wire_bytes for item in self.contacts)

    @property
    def governance_retransmission_ack_wire_bytes(self) -> int:
        return sum(item.governance_retransmission_ack_wire_bytes for item in self.contacts)

    @property
    def governance_unknown_remote_failure_count(self) -> int:
        return sum(item.governance_unknown_remote_failure_count for item in self.contacts)

    @property
    def chunk_manifest_primary_data_wire_bytes(self) -> int:
        return sum(
            0 if item.inner is None else item.inner.manifest_primary_data_wire_bytes
            for item in self.contacts
        )

    @property
    def availability_primary_data_wire_bytes(self) -> int:
        return sum(
            0 if item.inner is None else item.inner.availability_primary_data_wire_bytes
            for item in self.contacts
        )

    @property
    def payload_primary_data_wire_bytes(self) -> int:
        return sum(
            0 if item.inner is None else item.inner.payload_primary_data_wire_bytes
            for item in self.contacts
        )

    @property
    def inner_primary_ack_wire_bytes(self) -> int:
        return sum(
            0 if item.inner is None else item.inner.primary_ack_wire_bytes
            for item in self.contacts
        )

    @property
    def inner_retransmission_data_wire_bytes(self) -> int:
        return sum(
            0 if item.inner is None else item.inner.retransmission_data_wire_bytes
            for item in self.contacts
        )

    @property
    def inner_retransmission_ack_wire_bytes(self) -> int:
        return sum(
            0 if item.inner is None else item.inner.retransmission_ack_wire_bytes
            for item in self.contacts
        )

    @property
    def inner_unknown_remote_failure_count(self) -> int:
        return sum(
            0 if item.inner is None else item.inner.unknown_remote_failure_count
            for item in self.contacts
        )

    @property
    def total_wire_bytes(self) -> int:
        return sum(item.total_wire_bytes for item in self.contacts)


@dataclass(frozen=True, slots=True)
class GovernedEndToEndTRCReport:
    discovery_wire_bytes: int
    rendezvous_wire_bytes: int
    bundle_primary_data_wire_bytes: int
    custody_primary_data_wire_bytes: int
    chunk_manifest_primary_data_wire_bytes: int
    availability_primary_data_wire_bytes: int
    payload_primary_data_wire_bytes: int
    primary_ack_wire_bytes: int
    retransmission_data_wire_bytes: int
    retransmission_ack_wire_bytes: int
    fec_wire_bytes: int
    unknown_remote_failure_count: int
    route_accounting: tuple[str, ...]
    forwarded_contacts: int
    duplicate_suppressed_contacts: int
    expired_contacts: int
    hop_limited_contacts: int
    exact: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("discovery_wire_bytes", self.discovery_wire_bytes),
            ("rendezvous_wire_bytes", self.rendezvous_wire_bytes),
            ("bundle_primary_data_wire_bytes", self.bundle_primary_data_wire_bytes),
            ("custody_primary_data_wire_bytes", self.custody_primary_data_wire_bytes),
            ("chunk_manifest_primary_data_wire_bytes", self.chunk_manifest_primary_data_wire_bytes),
            ("availability_primary_data_wire_bytes", self.availability_primary_data_wire_bytes),
            ("payload_primary_data_wire_bytes", self.payload_primary_data_wire_bytes),
            ("primary_ack_wire_bytes", self.primary_ack_wire_bytes),
            ("retransmission_data_wire_bytes", self.retransmission_data_wire_bytes),
            ("retransmission_ack_wire_bytes", self.retransmission_ack_wire_bytes),
            ("fec_wire_bytes", self.fec_wire_bytes),
            ("unknown_remote_failure_count", self.unknown_remote_failure_count),
            ("forwarded_contacts", self.forwarded_contacts),
            ("duplicate_suppressed_contacts", self.duplicate_suppressed_contacts),
            ("expired_contacts", self.expired_contacts),
            ("hop_limited_contacts", self.hop_limited_contacts),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

    @property
    def primary_data_wire_bytes(self) -> int:
        return (
            self.discovery_wire_bytes
            + self.rendezvous_wire_bytes
            + self.bundle_primary_data_wire_bytes
            + self.custody_primary_data_wire_bytes
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


def run_governed_store_forward_schedule(
    bundle: ForwardBundle,
    manifest: ChunkManifest,
    *,
    peers: Mapping[str, ForwardPeer],
    contacts: Sequence[GovernedForwardContact],
    destination_id: str,
    ledger: CustodyLedger,
    profile: ScarceLinkProfile,
    transmitter: TransferCallable | None = None,
) -> tuple[bytes | None, GovernedRouteReport]:
    """Execute a deterministic intermittent schedule under bundle governance."""

    if destination_id not in peers:
        raise KeyError("destination peer is not present in peers")
    reports: list[GovernedContactReport] = []
    for contact in contacts:
        try:
            source = peers[contact.source_id]
            target = peers[contact.target_id]
        except KeyError as exc:
            raise KeyError(f"contact references unknown peer: {exc.args[0]}") from exc
        _, report = governed_forward_contact(
            bundle,
            manifest,
            source=source,
            target=target,
            ledger=ledger,
            profile=profile,
            transfer_id_base=contact.transfer_id_base,
            max_chunks=contact.max_chunks,
            contact_id=contact.contact_id,
            now_s=contact.now_s,
            transmitter=transmitter,
        )
        reports.append(report)

    destination = peers[destination_id]
    complete = destination.store.has(manifest.fingerprint) and all(
        destination.store.has(ref.sha256_digest) for ref in manifest.chunks
    )
    reconstructed: bytes | None = None
    exact = False
    if complete:
        reconstructed = reconstruct_from_store(manifest, destination.store)
        exact = True

    return reconstructed, GovernedRouteReport(
        destination_id=destination_id,
        contacts=tuple(reports),
        destination_complete=complete,
        destination_exact=exact,
    )


def summarize_governed_end_to_end_trc(
    route: GovernedRouteReport,
    *,
    descriptor: DiscoveryDescriptor | None = None,
    resolved_manifest: ContentManifest | None = None,
    discovery_transmissions: int = 0,
    rendezvous_transmissions: int = 0,
    fec_wire_bytes: int = 0,
) -> GovernedEndToEndTRCReport:
    """Account end-to-end TRC including PNB1 and PNC1 governance traffic."""

    for name, value in (
        ("discovery_transmissions", discovery_transmissions),
        ("rendezvous_transmissions", rendezvous_transmissions),
        ("fec_wire_bytes", fec_wire_bytes),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    if descriptor is None and discovery_transmissions:
        raise ValueError("descriptor is required when discovery_transmissions is non-zero")
    if resolved_manifest is None and rendezvous_transmissions:
        raise ValueError("resolved_manifest is required when rendezvous_transmissions is non-zero")

    discovery_bytes = 0 if descriptor is None else len(descriptor.encode()) * discovery_transmissions
    rendezvous_bytes = (
        0 if resolved_manifest is None else len(resolved_manifest.encode()) * rendezvous_transmissions
    )
    accounting = tuple(
        sorted({item.accounting for item in route.contacts if item.accounting != "none"})
    )
    return GovernedEndToEndTRCReport(
        discovery_wire_bytes=discovery_bytes,
        rendezvous_wire_bytes=rendezvous_bytes,
        bundle_primary_data_wire_bytes=route.bundle_primary_data_wire_bytes,
        custody_primary_data_wire_bytes=route.custody_primary_data_wire_bytes,
        chunk_manifest_primary_data_wire_bytes=route.chunk_manifest_primary_data_wire_bytes,
        availability_primary_data_wire_bytes=route.availability_primary_data_wire_bytes,
        payload_primary_data_wire_bytes=route.payload_primary_data_wire_bytes,
        primary_ack_wire_bytes=(
            route.governance_primary_ack_wire_bytes + route.inner_primary_ack_wire_bytes
        ),
        retransmission_data_wire_bytes=(
            route.governance_retransmission_data_wire_bytes
            + route.inner_retransmission_data_wire_bytes
        ),
        retransmission_ack_wire_bytes=(
            route.governance_retransmission_ack_wire_bytes
            + route.inner_retransmission_ack_wire_bytes
        ),
        fec_wire_bytes=fec_wire_bytes,
        unknown_remote_failure_count=(
            route.governance_unknown_remote_failure_count
            + route.inner_unknown_remote_failure_count
        ),
        route_accounting=accounting,
        forwarded_contacts=route.forwarded_contacts,
        duplicate_suppressed_contacts=route.duplicate_suppressed_contacts,
        expired_contacts=route.expired_contacts,
        hop_limited_contacts=route.hop_limited_contacts,
        exact=route.destination_exact,
    )
