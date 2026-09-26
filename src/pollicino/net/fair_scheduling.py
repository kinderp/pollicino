from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

from .bearer import BearerKind, BearerProfile, EvidenceBasis
from .bundle import CustodyLedger, TransferCallable
from .persistence import _atomic_write_bytes
from .scheduling import (
    ContactSchedulingPolicy,
    ContactSchedulingReport,
    ScheduledBundle,
    schedule_contact_bundles,
)
from .store_forward import ForwardPeer


FAIR_SCHEDULER_STATE_SCHEMA = "pollicino-fair-scheduler-state-v1"
FAIR_SCHEDULER_CHECKPOINT_SCHEMA = "pollicino-fair-scheduler-checkpoint-v1"


def _require_non_negative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _require_id(name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class FairnessPolicy:
    """Local starvation protection above ordinary bundle priority.

    Once an eligible bundle has waited ``starvation_seconds`` without useful
    service it enters the rescue queue. Rescue is deliberately bounded: at most
    ``max_rescue_bundles`` bundles get at most ``rescue_chunks_per_bundle``
    chunks before normal priority scheduling resumes.

    This guarantees eventual progress only when at least one chunk of the
    starved bundle fits the explicit logical source-byte budget of some future
    encounter. It does not infer physical bearer capacity.
    """

    starvation_seconds: int
    max_rescue_bundles: int = 1
    rescue_chunks_per_bundle: int = 1

    def __post_init__(self) -> None:
        for name, value in (
            ("starvation_seconds", self.starvation_seconds),
            ("max_rescue_bundles", self.max_rescue_bundles),
            ("rescue_chunks_per_bundle", self.rescue_chunks_per_bundle),
        ):
            _require_non_negative_int(name, value)


@dataclass(frozen=True, slots=True)
class BundleWaitRecord:
    bundle_id: str
    eligible_since_s: int
    last_observed_s: int
    last_served_s: int | None = None
    service_count: int = 0
    deferral_count: int = 0

    def __post_init__(self) -> None:
        _require_id("bundle_id", self.bundle_id)
        _require_non_negative_int("eligible_since_s", self.eligible_since_s)
        _require_non_negative_int("last_observed_s", self.last_observed_s)
        if self.last_observed_s < self.eligible_since_s:
            raise ValueError("last_observed_s cannot precede eligible_since_s")
        if self.last_served_s is not None:
            _require_non_negative_int("last_served_s", self.last_served_s)
        _require_non_negative_int("service_count", self.service_count)
        _require_non_negative_int("deferral_count", self.deferral_count)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "eligible_since_s": self.eligible_since_s,
            "last_observed_s": self.last_observed_s,
            "last_served_s": self.last_served_s,
            "service_count": self.service_count,
            "deferral_count": self.deferral_count,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> BundleWaitRecord:
        bundle_id = value.get("bundle_id")
        if not isinstance(bundle_id, str) or not bundle_id:
            raise ValueError("scheduler bundle_id must be a non-empty string")
        last_served = value.get("last_served_s")
        if last_served is not None and (isinstance(last_served, bool) or not isinstance(last_served, int)):
            raise ValueError("last_served_s must be null or an integer")
        return cls(
            bundle_id=bundle_id,
            eligible_since_s=int(value["eligible_since_s"]),
            last_observed_s=int(value["last_observed_s"]),
            last_served_s=last_served,
            service_count=int(value.get("service_count", 0)),
            deferral_count=int(value.get("deferral_count", 0)),
        )


class FairSchedulerState:
    """Persistent local waiting-age and encounter-idempotency state."""

    def __init__(self) -> None:
        self._records: dict[str, BundleWaitRecord] = {}
        self._processed_encounters: set[str] = set()

    @property
    def records(self) -> tuple[BundleWaitRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    def get(self, bundle_id: str) -> BundleWaitRecord | None:
        _require_id("bundle_id", bundle_id)
        return self._records.get(bundle_id)

    def observe_eligible(self, bundle_id: str, *, now_s: int) -> BundleWaitRecord:
        _require_id("bundle_id", bundle_id)
        _require_non_negative_int("now_s", now_s)
        previous = self._records.get(bundle_id)
        if previous is None:
            record = BundleWaitRecord(
                bundle_id=bundle_id,
                eligible_since_s=now_s,
                last_observed_s=now_s,
            )
        else:
            record = BundleWaitRecord(
                bundle_id=bundle_id,
                eligible_since_s=previous.eligible_since_s,
                last_observed_s=max(previous.last_observed_s, now_s),
                last_served_s=previous.last_served_s,
                service_count=previous.service_count,
                deferral_count=previous.deferral_count,
            )
        self._records[bundle_id] = record
        return record

    def record_service(self, bundle_id: str, *, now_s: int) -> BundleWaitRecord:
        _require_non_negative_int("now_s", now_s)
        previous = self.observe_eligible(bundle_id, now_s=now_s)
        record = BundleWaitRecord(
            bundle_id=bundle_id,
            eligible_since_s=now_s,
            last_observed_s=now_s,
            last_served_s=now_s,
            service_count=previous.service_count + 1,
            deferral_count=0,
        )
        self._records[bundle_id] = record
        return record

    def record_deferral(self, bundle_id: str, *, now_s: int) -> BundleWaitRecord:
        _require_non_negative_int("now_s", now_s)
        previous = self.observe_eligible(bundle_id, now_s=now_s)
        record = BundleWaitRecord(
            bundle_id=bundle_id,
            eligible_since_s=previous.eligible_since_s,
            last_observed_s=now_s,
            last_served_s=previous.last_served_s,
            service_count=previous.service_count,
            deferral_count=previous.deferral_count + 1,
        )
        self._records[bundle_id] = record
        return record

    def encounter_seen(self, encounter_id: str) -> bool:
        _require_id("encounter_id", encounter_id)
        return encounter_id in self._processed_encounters

    def mark_encounter(self, encounter_id: str) -> None:
        _require_id("encounter_id", encounter_id)
        self._processed_encounters.add(encounter_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": FAIR_SCHEDULER_STATE_SCHEMA,
            "records": [record.to_dict() for record in self.records],
            "processed_encounters": sorted(self._processed_encounters),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> FairSchedulerState:
        if value.get("schema") != FAIR_SCHEDULER_STATE_SCHEMA:
            raise ValueError("unsupported fair scheduler state schema")
        records = value.get("records")
        encounters = value.get("processed_encounters")
        if not isinstance(records, list) or not isinstance(encounters, list):
            raise ValueError("fair scheduler records/encounters must be lists")
        state = cls()
        for item in records:
            if not isinstance(item, Mapping):
                raise ValueError("fair scheduler record must be an object")
            record = BundleWaitRecord.from_dict(item)
            if record.bundle_id in state._records:
                raise ValueError("fair scheduler state contains duplicate bundle IDs")
            state._records[record.bundle_id] = record
        for encounter_id in encounters:
            if not isinstance(encounter_id, str) or not encounter_id:
                raise ValueError("processed encounter ID must be a non-empty string")
            state._processed_encounters.add(encounter_id)
        return state


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def save_fair_scheduler_state(
    path: str | os.PathLike[str], state: FairSchedulerState
) -> Path:
    if not isinstance(state, FairSchedulerState):
        raise TypeError("state must be FairSchedulerState")
    body = state.to_dict()
    envelope = {
        "schema": FAIR_SCHEDULER_CHECKPOINT_SCHEMA,
        "state": body,
        "state_sha256": hashlib.sha256(_canonical_bytes(body)).hexdigest(),
    }
    encoded = (
        json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("utf-8")
    destination = Path(path)
    _atomic_write_bytes(destination, encoded)
    return destination


def load_fair_scheduler_state(path: str | os.PathLike[str]) -> FairSchedulerState:
    source = Path(path)
    try:
        envelope = json.loads(source.read_bytes())
    except FileNotFoundError as exc:
        raise LookupError("fair scheduler checkpoint does not exist") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("fair scheduler checkpoint is not valid UTF-8 JSON") from exc
    if not isinstance(envelope, Mapping) or envelope.get("schema") != FAIR_SCHEDULER_CHECKPOINT_SCHEMA:
        raise ValueError("unsupported fair scheduler checkpoint schema")
    body = envelope.get("state")
    if not isinstance(body, Mapping):
        raise ValueError("fair scheduler checkpoint state must be an object")
    expected = envelope.get("state_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError("fair scheduler checkpoint checksum is missing or invalid")
    actual = hashlib.sha256(_canonical_bytes(body)).hexdigest()
    if not hmac.compare_digest(actual, expected):
        raise ValueError("fair scheduler checkpoint checksum mismatch")
    return FairSchedulerState.from_dict(body)


def _transferable(
    item: ScheduledBundle,
    *,
    source: ForwardPeer,
    target: ForwardPeer,
    ledger: CustodyLedger,
    now_s: int,
) -> bool:
    if item.bundle.expired(now_s):
        return False
    if ledger.get(item.bundle.bundle_id, source.peer_id) is None:
        return False
    return any(
        not target.store.has(ref.sha256_digest) and source.store.has(ref.sha256_digest)
        for ref in item.manifest.chunks
    )


def _next_transfer_id(report: ContactSchedulingReport, fallback: int) -> int:
    if not report.decisions:
        return fallback
    return report.decisions[-1].report.next_transfer_id


@dataclass(frozen=True, slots=True)
class FairContactSchedulingReport:
    encounter_id: str
    source_id: str
    target_id: str
    logical_source_byte_budget: int
    used_source_bytes: int
    remaining_source_bytes: int
    rescued_bundle_ids: tuple[str, ...]
    rescue_reports: tuple[ContactSchedulingReport, ...]
    regular_report: ContactSchedulingReport | None
    duplicate_encounter: bool = False

    @property
    def total_wire_bytes(self) -> int:
        rescue = sum(report.total_wire_bytes for report in self.rescue_reports)
        regular = 0 if self.regular_report is None else self.regular_report.total_wire_bytes
        return rescue + regular

    @property
    def decisions(self) -> tuple[Any, ...]:
        result: list[Any] = []
        for report in self.rescue_reports:
            result.extend(report.decisions)
        if self.regular_report is not None:
            result.extend(self.regular_report.decisions)
        return tuple(result)



def schedule_fair_contact_bundles(
    bundles: Sequence[ScheduledBundle],
    *,
    source: ForwardPeer,
    target: ForwardPeer,
    ledger: CustodyLedger,
    state: FairSchedulerState,
    profile,
    transfer_id_base: int,
    encounter_id: str,
    now_s: int,
    policy: ContactSchedulingPolicy,
    fairness: FairnessPolicy,
    transmitter: TransferCallable | None = None,
) -> FairContactSchedulingReport:
    """Schedule one encounter with bounded starvation rescue before normal priority."""

    if not isinstance(state, FairSchedulerState):
        raise TypeError("state must be FairSchedulerState")
    if not isinstance(fairness, FairnessPolicy):
        raise TypeError("fairness must be FairnessPolicy")
    _require_id("encounter_id", encounter_id)
    _require_non_negative_int("now_s", now_s)

    if state.encounter_seen(encounter_id):
        return FairContactSchedulingReport(
            encounter_id=encounter_id,
            source_id=source.peer_id,
            target_id=target.peer_id,
            logical_source_byte_budget=policy.max_source_bytes,
            used_source_bytes=0,
            remaining_source_bytes=policy.max_source_bytes,
            rescued_bundle_ids=(),
            rescue_reports=(),
            regular_report=None,
            duplicate_encounter=True,
        )

    eligible: list[ScheduledBundle] = []
    wait_seconds: dict[str, int] = {}
    for item in bundles:
        if not isinstance(item, ScheduledBundle):
            raise TypeError("bundles must contain ScheduledBundle values")
        if not _transferable(item, source=source, target=target, ledger=ledger, now_s=now_s):
            continue
        bundle_id = item.bundle.bundle_id.hex()
        record = state.observe_eligible(bundle_id, now_s=now_s)
        eligible.append(item)
        wait_seconds[bundle_id] = max(0, now_s - record.eligible_since_s)

    starved = sorted(
        (
            item
            for item in eligible
            if wait_seconds[item.bundle.bundle_id.hex()] >= fairness.starvation_seconds
        ),
        key=lambda item: (
            -wait_seconds[item.bundle.bundle_id.hex()],
            state.get(item.bundle.bundle_id.hex()).eligible_since_s,
            item.bundle.bundle_id,
        ),
    )

    remaining = policy.max_source_bytes
    next_transfer_id = transfer_id_base
    rescue_reports: list[ContactSchedulingReport] = []
    rescued_ids: list[str] = []
    served_ids: set[str] = set()

    for rescue_index, item in enumerate(starved[: fairness.max_rescue_bundles]):
        if remaining <= 0 or fairness.rescue_chunks_per_bundle == 0:
            break
        rescue_policy = ContactSchedulingPolicy(
            max_source_bytes=remaining,
            max_bundles=1,
            max_chunks_per_bundle=min(
                policy.max_chunks_per_bundle, fairness.rescue_chunks_per_bundle
            ),
            prefer_completion=policy.prefer_completion,
        )
        report = schedule_contact_bundles(
            [item],
            source=source,
            target=target,
            ledger=ledger,
            profile=profile,
            transfer_id_base=next_transfer_id,
            encounter_id=f"{encounter_id}:rescue:{rescue_index}",
            now_s=now_s,
            policy=rescue_policy,
            transmitter=transmitter,
        )
        rescue_reports.append(report)
        next_transfer_id = _next_transfer_id(report, next_transfer_id)
        remaining -= report.used_source_bytes
        if report.used_source_bytes > 0:
            bundle_id = item.bundle.bundle_id.hex()
            rescued_ids.append(bundle_id)
            served_ids.add(bundle_id)
            state.record_service(bundle_id, now_s=now_s)

    regular_candidates = [
        item for item in eligible if item.bundle.bundle_id.hex() not in served_ids
    ]
    remaining_bundle_slots = max(0, policy.max_bundles - len(served_ids))
    regular_report: ContactSchedulingReport | None = None
    if remaining > 0 and remaining_bundle_slots > 0 and regular_candidates:
        regular_policy = ContactSchedulingPolicy(
            max_source_bytes=remaining,
            max_bundles=remaining_bundle_slots,
            max_chunks_per_bundle=policy.max_chunks_per_bundle,
            prefer_completion=policy.prefer_completion,
        )
        regular_report = schedule_contact_bundles(
            regular_candidates,
            source=source,
            target=target,
            ledger=ledger,
            profile=profile,
            transfer_id_base=next_transfer_id,
            encounter_id=f"{encounter_id}:regular",
            now_s=now_s,
            policy=regular_policy,
            transmitter=transmitter,
        )
        for decision in regular_report.decisions:
            if decision.selected_source_bytes > 0:
                served_ids.add(decision.bundle_id)
                state.record_service(decision.bundle_id, now_s=now_s)
        remaining -= regular_report.used_source_bytes

    for item in eligible:
        bundle_id = item.bundle.bundle_id.hex()
        if bundle_id not in served_ids:
            state.record_deferral(bundle_id, now_s=now_s)

    state.mark_encounter(encounter_id)
    used = policy.max_source_bytes - remaining
    return FairContactSchedulingReport(
        encounter_id=encounter_id,
        source_id=source.peer_id,
        target_id=target.peer_id,
        logical_source_byte_budget=policy.max_source_bytes,
        used_source_bytes=used,
        remaining_source_bytes=remaining,
        rescued_bundle_ids=tuple(rescued_ids),
        rescue_reports=tuple(rescue_reports),
        regular_report=regular_report,
    )


@dataclass(frozen=True, slots=True)
class BearerSchedulingPolicy:
    bearer_id: str
    contact_policy: ContactSchedulingPolicy
    fairness_policy: FairnessPolicy

    def __post_init__(self) -> None:
        _require_id("bearer_id", self.bearer_id)
        if not isinstance(self.contact_policy, ContactSchedulingPolicy):
            raise TypeError("contact_policy must be ContactSchedulingPolicy")
        if not isinstance(self.fairness_policy, FairnessPolicy):
            raise TypeError("fairness_policy must be FairnessPolicy")


@dataclass(frozen=True, slots=True)
class BearerSchedulingReport:
    bearer_id: str
    kind: BearerKind
    profile_evidence_basis: EvidenceBasis
    profile_provenance: str | None
    logical_budget_is_measured_capacity: bool
    scheduling: FairContactSchedulingReport

    @property
    def total_wire_bytes(self) -> int:
        return self.scheduling.total_wire_bytes

    @property
    def execution_accounting(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    decision.report.accounting
                    for decision in self.scheduling.decisions
                    if decision.report.accounting != "none"
                }
            )
        )

    @property
    def contains_physical_replay(self) -> bool:
        return "physical_replay_lower_bound" in self.execution_accounting


def schedule_fair_bearer_contact(
    bundles: Sequence[ScheduledBundle],
    *,
    source: ForwardPeer,
    target: ForwardPeer,
    ledger: CustodyLedger,
    state: FairSchedulerState,
    bearer: BearerProfile,
    policy: BearerSchedulingPolicy,
    transfer_id_base: int,
    encounter_id: str,
    now_s: int,
    transmitter: TransferCallable | None = None,
) -> BearerSchedulingReport:
    """Run fair scheduling with an explicit policy for one named bearer.

    The logical source-byte budget is always policy input here. Even when the
    bearer profile was derived from measurements, this function does not claim
    that the budget itself equals measured contact capacity. A future physical
    contact-window adapter must establish that relationship explicitly.
    """

    if not isinstance(bearer, BearerProfile):
        raise TypeError("bearer must be BearerProfile")
    if not isinstance(policy, BearerSchedulingPolicy):
        raise TypeError("policy must be BearerSchedulingPolicy")
    if policy.bearer_id != bearer.bearer_id:
        raise ValueError("bearer scheduling policy targets a different bearer_id")

    report = schedule_fair_contact_bundles(
        bundles,
        source=source,
        target=target,
        ledger=ledger,
        state=state,
        profile=bearer.link_profile,
        transfer_id_base=transfer_id_base,
        encounter_id=encounter_id,
        now_s=now_s,
        policy=policy.contact_policy,
        fairness=policy.fairness_policy,
        transmitter=transmitter,
    )
    return BearerSchedulingReport(
        bearer_id=bearer.bearer_id,
        kind=bearer.kind,
        profile_evidence_basis=bearer.evidence_basis,
        profile_provenance=bearer.provenance,
        logical_budget_is_measured_capacity=False,
        scheduling=report,
    )
