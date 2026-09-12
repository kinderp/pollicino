from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from .bundle import CustodyLedger, GovernedContactReport, TransferCallable, governed_forward_contact
from .bundle_route import GovernedForwardContact
from .link import ScarceLinkProfile
from .store import ChunkManifest, reconstruct_from_store
from .store_forward import ForwardPeer


class BearerKind(str, Enum):
    LORA = "lora"
    BLE = "ble"
    WIFI = "wifi"
    INTERNET = "internet"


class EvidenceBasis(str, Enum):
    SYNTHETIC = "synthetic"
    MEASURED = "measured"


@dataclass(frozen=True, slots=True)
class BearerProfile:
    """One bearer configuration with explicit evidence provenance.

    ``evidence_basis`` describes where the profile numbers came from. It does
    not describe how a route execution was observed. A deterministic simulator
    using measured parameters is still a model run; only a transmitter/report
    that exposes physical-replay accounting is physical evidence.
    """

    bearer_id: str
    kind: BearerKind
    evidence_basis: EvidenceBasis
    link_profile: ScarceLinkProfile
    provenance: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.bearer_id, str) or not self.bearer_id:
            raise ValueError("bearer_id must be a non-empty string")
        if not isinstance(self.kind, BearerKind):
            raise TypeError("kind must be BearerKind")
        if not isinstance(self.evidence_basis, EvidenceBasis):
            raise TypeError("evidence_basis must be EvidenceBasis")
        if not isinstance(self.link_profile, ScarceLinkProfile):
            raise TypeError("link_profile must be ScarceLinkProfile")
        if self.evidence_basis is EvidenceBasis.MEASURED:
            if not isinstance(self.provenance, str) or not self.provenance.strip():
                raise ValueError("measured bearer profiles require explicit provenance")
        elif self.provenance is not None and (
            not isinstance(self.provenance, str) or not self.provenance.strip()
        ):
            raise ValueError("provenance must be None or a non-empty string")


@dataclass(frozen=True, slots=True)
class BearerGovernedContact:
    contact: GovernedForwardContact
    bearer_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.contact, GovernedForwardContact):
            raise TypeError("contact must be GovernedForwardContact")
        if not isinstance(self.bearer_id, str) or not self.bearer_id:
            raise ValueError("bearer_id must be a non-empty string")


@dataclass(frozen=True, slots=True)
class BearerContactReport:
    bearer_id: str
    kind: BearerKind
    profile_evidence_basis: EvidenceBasis
    profile_provenance: str | None
    execution_accounting: str
    contact: GovernedContactReport

    @property
    def physical_replay(self) -> bool:
        return self.execution_accounting == "physical_replay_lower_bound"

    @property
    def model_execution(self) -> bool:
        return not self.physical_replay

    @property
    def total_wire_bytes(self) -> int:
        return self.contact.total_wire_bytes

    @property
    def primary_data_wire_bytes(self) -> int:
        inner = self.contact.inner
        return (
            self.contact.bundle_primary_data_wire_bytes
            + self.contact.custody_primary_data_wire_bytes
            + (0 if inner is None else inner.primary_data_wire_bytes)
        )

    @property
    def primary_ack_wire_bytes(self) -> int:
        inner = self.contact.inner
        return self.contact.governance_primary_ack_wire_bytes + (
            0 if inner is None else inner.primary_ack_wire_bytes
        )

    @property
    def retransmission_data_wire_bytes(self) -> int:
        inner = self.contact.inner
        return self.contact.governance_retransmission_data_wire_bytes + (
            0 if inner is None else inner.retransmission_data_wire_bytes
        )

    @property
    def retransmission_ack_wire_bytes(self) -> int:
        inner = self.contact.inner
        return self.contact.governance_retransmission_ack_wire_bytes + (
            0 if inner is None else inner.retransmission_ack_wire_bytes
        )

    @property
    def unknown_remote_failure_count(self) -> int:
        inner = self.contact.inner
        return self.contact.governance_unknown_remote_failure_count + (
            0 if inner is None else inner.unknown_remote_failure_count
        )


@dataclass(frozen=True, slots=True)
class BearerTRCLine:
    bearer_id: str
    kind: BearerKind
    profile_evidence_basis: EvidenceBasis
    profile_provenance: str | None
    contact_count: int
    forwarded_contact_count: int
    physical_replay_contact_count: int
    model_contact_count: int
    primary_data_wire_bytes: int
    primary_ack_wire_bytes: int
    retransmission_data_wire_bytes: int
    retransmission_ack_wire_bytes: int
    unknown_remote_failure_count: int

    @property
    def total_wire_bytes(self) -> int:
        return (
            self.primary_data_wire_bytes
            + self.primary_ack_wire_bytes
            + self.retransmission_data_wire_bytes
            + self.retransmission_ack_wire_bytes
        )

    @property
    def total_bits(self) -> int:
        return self.total_wire_bytes * 8

    @property
    def fully_physical_replay(self) -> bool:
        return self.contact_count > 0 and self.physical_replay_contact_count == self.contact_count


@dataclass(frozen=True, slots=True)
class PerBearerTRCReport:
    lines: tuple[BearerTRCLine, ...]
    destination_id: str
    destination_complete: bool
    destination_exact: bool

    @property
    def total_wire_bytes(self) -> int:
        return sum(line.total_wire_bytes for line in self.lines)

    @property
    def total_bits(self) -> int:
        return self.total_wire_bytes * 8

    @property
    def contains_synthetic_profile(self) -> bool:
        return any(line.profile_evidence_basis is EvidenceBasis.SYNTHETIC for line in self.lines)

    @property
    def contains_measured_profile(self) -> bool:
        return any(line.profile_evidence_basis is EvidenceBasis.MEASURED for line in self.lines)

    @property
    def fully_physical_replay(self) -> bool:
        return bool(self.lines) and all(line.fully_physical_replay for line in self.lines)

    def line_for(self, bearer_id: str) -> BearerTRCLine:
        for line in self.lines:
            if line.bearer_id == bearer_id:
                return line
        raise KeyError(f"bearer {bearer_id!r} is not present in the report")


def _aggregate_bearer_lines(
    reports: Sequence[BearerContactReport],
) -> tuple[BearerTRCLine, ...]:
    grouped: dict[str, list[BearerContactReport]] = {}
    for report in reports:
        grouped.setdefault(report.bearer_id, []).append(report)

    lines: list[BearerTRCLine] = []
    for bearer_id in sorted(grouped):
        items = grouped[bearer_id]
        first = items[0]
        if any(item.kind is not first.kind for item in items):
            raise ValueError("one bearer_id cannot change bearer kind inside one report")
        if any(item.profile_evidence_basis is not first.profile_evidence_basis for item in items):
            raise ValueError("one bearer_id cannot mix profile evidence bases inside one report")
        if any(item.profile_provenance != first.profile_provenance for item in items):
            raise ValueError("one bearer_id cannot mix provenance inside one report")
        lines.append(
            BearerTRCLine(
                bearer_id=bearer_id,
                kind=first.kind,
                profile_evidence_basis=first.profile_evidence_basis,
                profile_provenance=first.profile_provenance,
                contact_count=len(items),
                forwarded_contact_count=sum(
                    item.contact.disposition == "forwarded" for item in items
                ),
                physical_replay_contact_count=sum(item.physical_replay for item in items),
                model_contact_count=sum(item.model_execution for item in items),
                primary_data_wire_bytes=sum(item.primary_data_wire_bytes for item in items),
                primary_ack_wire_bytes=sum(item.primary_ack_wire_bytes for item in items),
                retransmission_data_wire_bytes=sum(
                    item.retransmission_data_wire_bytes for item in items
                ),
                retransmission_ack_wire_bytes=sum(
                    item.retransmission_ack_wire_bytes for item in items
                ),
                unknown_remote_failure_count=sum(
                    item.unknown_remote_failure_count for item in items
                ),
            )
        )
    return tuple(lines)


def run_per_bearer_governed_schedule(
    bundle,
    manifest: ChunkManifest,
    *,
    peers: Mapping[str, ForwardPeer],
    contacts: Sequence[BearerGovernedContact],
    destination_id: str,
    ledger: CustodyLedger,
    bearers: Mapping[str, BearerProfile],
    transmitters: Mapping[str, TransferCallable] | None = None,
) -> tuple[bytes | None, PerBearerTRCReport]:
    """Execute governed contacts with a bearer selected explicitly per contact.

    There are intentionally no built-in LoRa/BLE/Wi-Fi/Internet performance
    defaults. Callers must provide every profile, including whether its numbers
    are synthetic or measured and, for measured profiles, where they came from.
    """

    if destination_id not in peers:
        raise KeyError("destination peer is not present in peers")
    reports: list[BearerContactReport] = []
    transmitter_map = {} if transmitters is None else transmitters

    for scheduled in contacts:
        try:
            profile = bearers[scheduled.bearer_id]
        except KeyError as exc:
            raise KeyError(f"unknown bearer profile: {scheduled.bearer_id}") from exc
        contact = scheduled.contact
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
            profile=profile.link_profile,
            transfer_id_base=contact.transfer_id_base,
            max_chunks=contact.max_chunks,
            contact_id=contact.contact_id,
            now_s=contact.now_s,
            transmitter=transmitter_map.get(scheduled.bearer_id),
        )
        reports.append(
            BearerContactReport(
                bearer_id=profile.bearer_id,
                kind=profile.kind,
                profile_evidence_basis=profile.evidence_basis,
                profile_provenance=profile.provenance,
                execution_accounting=report.accounting,
                contact=report,
            )
        )

    destination = peers[destination_id]
    complete = destination.store.has(manifest.fingerprint) and all(
        destination.store.has(ref.sha256_digest) for ref in manifest.chunks
    )
    reconstructed: bytes | None = None
    exact = False
    if complete:
        reconstructed = reconstruct_from_store(manifest, destination.store)
        exact = True

    return reconstructed, PerBearerTRCReport(
        lines=_aggregate_bearer_lines(reports),
        destination_id=destination_id,
        destination_complete=complete,
        destination_exact=exact,
    )
