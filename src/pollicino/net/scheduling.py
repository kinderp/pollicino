from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Mapping, Sequence

from .bundle import CustodyLedger, ForwardBundle, GovernedContactReport, TransferCallable, governed_forward_contact
from .link import ScarceLinkProfile
from .store import ChunkManifest
from .store_forward import ForwardPeer


class BundlePriority(IntEnum):
    """Local forwarding priority; higher values are sent first."""

    BULK = 0
    NORMAL = 1
    HIGH = 2
    EMERGENCY = 3


@dataclass(frozen=True, slots=True)
class ScheduledBundle:
    bundle: ForwardBundle
    manifest: ChunkManifest
    priority: BundlePriority = BundlePriority.NORMAL
    label: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.bundle, ForwardBundle):
            raise TypeError("bundle must be ForwardBundle")
        if not isinstance(self.manifest, ChunkManifest):
            raise TypeError("manifest must be ChunkManifest")
        if self.bundle.manifest_fingerprint != self.manifest.fingerprint:
            raise ValueError("bundle manifest fingerprint mismatch")
        if not isinstance(self.priority, BundlePriority):
            raise TypeError("priority must be BundlePriority")
        if self.label is not None and (not isinstance(self.label, str) or not self.label):
            raise ValueError("label must be None or a non-empty string")


@dataclass(frozen=True, slots=True)
class ContactSchedulingPolicy:
    """Deterministic logical budget for one intermittent encounter.

    ``max_source_bytes`` limits authoritative chunk bytes, not total radio-wire
    bytes. That distinction is deliberate: until a bearer has measured contact
    capacity, the scheduler must not pretend a synthetic logical budget is a
    physical contact-window measurement.
    """

    max_source_bytes: int
    max_bundles: int
    max_chunks_per_bundle: int
    prefer_completion: bool = True

    def __post_init__(self) -> None:
        for name, value in (
            ("max_source_bytes", self.max_source_bytes),
            ("max_bundles", self.max_bundles),
            ("max_chunks_per_bundle", self.max_chunks_per_bundle),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if not isinstance(self.prefer_completion, bool):
            raise TypeError("prefer_completion must be bool")


@dataclass(frozen=True, slots=True)
class BundleSchedulingDecision:
    bundle_id: str
    label: str | None
    priority: BundlePriority
    seconds_to_expiry: int
    target_missing_chunk_count_before: int
    source_available_missing_count_before: int
    source_available_missing_bytes_before: int
    selected_chunk_count: int
    selected_source_bytes: int
    would_complete_target: bool
    contact_id: str
    report: GovernedContactReport


@dataclass(frozen=True, slots=True)
class ContactSchedulingReport:
    encounter_id: str
    source_id: str
    target_id: str
    logical_source_byte_budget: int
    used_source_bytes: int
    remaining_source_bytes: int
    decisions: tuple[BundleSchedulingDecision, ...]
    skipped_expired_bundle_ids: tuple[str, ...]
    skipped_no_custody_bundle_ids: tuple[str, ...]
    skipped_no_transferable_data_bundle_ids: tuple[str, ...]

    @property
    def scheduled_bundle_count(self) -> int:
        return len(self.decisions)

    @property
    def total_wire_bytes(self) -> int:
        return sum(item.report.total_wire_bytes for item in self.decisions)

    @property
    def emergency_bundle_count(self) -> int:
        return sum(item.priority is BundlePriority.EMERGENCY for item in self.decisions)


@dataclass(frozen=True, slots=True)
class _Candidate:
    item: ScheduledBundle
    seconds_to_expiry: int
    missing_indices: tuple[int, ...]
    source_available_indices: tuple[int, ...]
    source_available_bytes: int
    target_missing_bytes: int
    source_can_complete: bool


def _candidate_for(
    item: ScheduledBundle,
    *,
    source: ForwardPeer,
    target: ForwardPeer,
    ledger: CustodyLedger,
    now_s: int,
) -> _Candidate | None:
    bundle = item.bundle
    if bundle.expired(now_s):
        return None
    if ledger.get(bundle.bundle_id, source.peer_id) is None:
        return None

    missing = tuple(
        index
        for index, ref in enumerate(item.manifest.chunks)
        if not target.store.has(ref.sha256_digest)
    )
    available = tuple(
        index
        for index in missing
        if source.store.has(item.manifest.chunks[index].sha256_digest)
    )
    available_bytes = sum(item.manifest.chunks[index].length for index in available)
    missing_bytes = sum(item.manifest.chunks[index].length for index in missing)
    source_can_complete = bool(missing) and len(available) == len(missing)
    expiry = bundle.created_at_s + bundle.ttl_seconds
    return _Candidate(
        item=item,
        seconds_to_expiry=max(0, expiry - now_s),
        missing_indices=missing,
        source_available_indices=available,
        source_available_bytes=available_bytes,
        target_missing_bytes=missing_bytes,
        source_can_complete=source_can_complete,
    )


def _sort_key(candidate: _Candidate, *, prefer_completion: bool) -> tuple[object, ...]:
    # Priority is authoritative locally. Inside the same class, expiring work is
    # preferred; then, optionally, transfers that can finish the target; then
    # smaller remaining objects so a short contact can complete more useful work.
    completion_rank = 0 if (prefer_completion and candidate.source_can_complete) else 1
    return (
        -int(candidate.item.priority),
        candidate.seconds_to_expiry,
        completion_rank,
        candidate.target_missing_bytes,
        candidate.item.bundle.bundle_id,
    )


def _select_chunk_count(
    candidate: _Candidate,
    *,
    remaining_bytes: int,
    max_chunks: int,
) -> tuple[int, int]:
    count = 0
    selected_bytes = 0
    for index in candidate.source_available_indices:
        if count >= max_chunks:
            break
        length = candidate.item.manifest.chunks[index].length
        if selected_bytes + length > remaining_bytes:
            break
        count += 1
        selected_bytes += length
    return count, selected_bytes


def schedule_contact_bundles(
    bundles: Sequence[ScheduledBundle],
    *,
    source: ForwardPeer,
    target: ForwardPeer,
    ledger: CustodyLedger,
    profile: ScarceLinkProfile,
    transfer_id_base: int,
    encounter_id: str,
    now_s: int,
    policy: ContactSchedulingPolicy,
    transmitter: TransferCallable | None = None,
) -> ContactSchedulingReport:
    """Select and forward useful bundle chunks within one logical contact budget.

    This is deliberately a policy experiment above the existing governed
    transport. It does not estimate how many bytes a real LoRa/BLE/Wi-Fi contact
    can carry. A future measured-contact adapter may derive this logical budget
    from physical evidence, but until then callers must provide it explicitly.
    """

    if source.peer_id == target.peer_id:
        raise ValueError("source and target peers must differ")
    if not isinstance(encounter_id, str) or not encounter_id:
        raise ValueError("encounter_id must be a non-empty string")
    if isinstance(now_s, bool) or not isinstance(now_s, int) or now_s < 0:
        raise ValueError("now_s must be a non-negative integer")
    if isinstance(transfer_id_base, bool) or not isinstance(transfer_id_base, int):
        raise ValueError("transfer_id_base must be an integer")
    if not 0 <= transfer_id_base <= 0xFFFFFFFF:
        raise ValueError("transfer_id_base must fit in an unsigned 32-bit integer")
    if not isinstance(policy, ContactSchedulingPolicy):
        raise TypeError("policy must be ContactSchedulingPolicy")

    candidates: list[_Candidate] = []
    expired: list[str] = []
    no_custody: list[str] = []
    no_data: list[str] = []

    for item in bundles:
        if not isinstance(item, ScheduledBundle):
            raise TypeError("bundles must contain ScheduledBundle values")
        bundle_id = item.bundle.bundle_id.hex()
        if item.bundle.expired(now_s):
            expired.append(bundle_id)
            continue
        if ledger.get(item.bundle.bundle_id, source.peer_id) is None:
            no_custody.append(bundle_id)
            continue
        candidate = _candidate_for(
            item,
            source=source,
            target=target,
            ledger=ledger,
            now_s=now_s,
        )
        if candidate is None or not candidate.source_available_indices:
            no_data.append(bundle_id)
            continue
        candidates.append(candidate)

    candidates.sort(key=lambda value: _sort_key(value, prefer_completion=policy.prefer_completion))

    remaining = policy.max_source_bytes
    next_transfer_id = transfer_id_base
    decisions: list[BundleSchedulingDecision] = []

    for candidate in candidates:
        if len(decisions) >= policy.max_bundles or remaining <= 0:
            break
        chunk_count, planned_bytes = _select_chunk_count(
            candidate,
            remaining_bytes=remaining,
            max_chunks=policy.max_chunks_per_bundle,
        )
        if chunk_count == 0:
            continue

        bundle = candidate.item.bundle
        contact_id = f"{encounter_id}:{bundle.bundle_id.hex()}"
        _, report = governed_forward_contact(
            bundle,
            candidate.item.manifest,
            source=source,
            target=target,
            ledger=ledger,
            profile=profile,
            transfer_id_base=next_transfer_id,
            max_chunks=chunk_count,
            contact_id=contact_id,
            now_s=now_s,
            transmitter=transmitter,
        )
        next_transfer_id = report.next_transfer_id
        actual_source_bytes = 0 if report.inner is None else report.inner.transferred_source_bytes
        if actual_source_bytes > planned_bytes:
            raise AssertionError("scheduler transferred more source bytes than planned")
        remaining -= actual_source_bytes
        decisions.append(
            BundleSchedulingDecision(
                bundle_id=bundle.bundle_id.hex(),
                label=candidate.item.label,
                priority=candidate.item.priority,
                seconds_to_expiry=candidate.seconds_to_expiry,
                target_missing_chunk_count_before=len(candidate.missing_indices),
                source_available_missing_count_before=len(candidate.source_available_indices),
                source_available_missing_bytes_before=candidate.source_available_bytes,
                selected_chunk_count=chunk_count,
                selected_source_bytes=actual_source_bytes,
                would_complete_target=(
                    candidate.source_can_complete
                    and chunk_count == len(candidate.missing_indices)
                ),
                contact_id=contact_id,
                report=report,
            )
        )

    used = policy.max_source_bytes - remaining
    return ContactSchedulingReport(
        encounter_id=encounter_id,
        source_id=source.peer_id,
        target_id=target.peer_id,
        logical_source_byte_budget=policy.max_source_bytes,
        used_source_bytes=used,
        remaining_source_bytes=remaining,
        decisions=tuple(decisions),
        skipped_expired_bundle_ids=tuple(sorted(expired)),
        skipped_no_custody_bundle_ids=tuple(sorted(no_custody)),
        skipped_no_transferable_data_bundle_ids=tuple(sorted(no_data)),
    )
