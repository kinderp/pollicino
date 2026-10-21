from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .bearer import BearerProfile
from .bundle import CustodyLedger
from .contact_windows import SyntheticContactWindow
from .fair_scheduling import (
    BearerSchedulingPolicy,
    BearerSchedulingReport,
    FairSchedulerState,
    schedule_fair_bearer_contact,
)
from .rapid_encounter import (
    RapidEncounterDecisionReport,
    RapidEncounterPrototypeState,
    evaluate_rapid_encounter,
)
from .routing_compare import (
    RoutingStrategyReport,
    StrategyBearerUsage,
    StrategyBundleOutcome,
    StrategyWindowReport,
)
from .scheduling import BundlePriority, ContactSchedulingPolicy, ScheduledBundle
from .store import PollicinoStore, reconstruct_from_store
from .store_forward import ForwardPeer


RAPID_DEADLINE_PROTOTYPE_ID = "rapid-deadline-prototype"


def _require_id(name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class RapidPriorMeetingObservation:
    node_a: str
    node_b: str
    observed_at_s: int
    opportunity_bytes_a_to_b: int | None = None
    opportunity_bytes_b_to_a: int | None = None

    def __post_init__(self) -> None:
        _require_id("node_a", self.node_a)
        _require_id("node_b", self.node_b)
        if self.node_a == self.node_b:
            raise ValueError("prior meeting endpoints must differ")
        if (
            isinstance(self.observed_at_s, bool)
            or not isinstance(self.observed_at_s, int)
            or self.observed_at_s < 0
        ):
            raise ValueError("observed_at_s must be a non-negative integer")
        for name, value in (
            ("opportunity_bytes_a_to_b", self.opportunity_bytes_a_to_b),
            ("opportunity_bytes_b_to_a", self.opportunity_bytes_b_to_a),
        ):
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
            ):
                raise ValueError(f"{name} must be None or a positive integer")


@dataclass(frozen=True, slots=True)
class RapidScheduleWindowReport:
    encounter: RapidEncounterDecisionReport
    routing: StrategyWindowReport

    @property
    def control_entry_count_lower_bound(self) -> int:
        return self.encounter.control_entry_count_lower_bound


@dataclass(frozen=True, slots=True)
class RapidScheduleReport:
    routing: RoutingStrategyReport
    windows: tuple[RapidScheduleWindowReport, ...]
    evidence_class: str = "model_synthetic"

    @property
    def strategy_id(self) -> str:
        return self.routing.strategy_id

    @property
    def control_entry_count_lower_bound(self) -> int:
        return sum(item.control_entry_count_lower_bound for item in self.windows)

    @property
    def total_wire_bytes_excluding_rapid_control(self) -> int:
        return self.routing.total_wire_bytes


def _clone_store(store: object, bundles: Sequence[ScheduledBundle]) -> PollicinoStore:
    clone = PollicinoStore()
    for item in bundles:
        digests = (
            item.manifest.fingerprint,
            *(ref.sha256_digest for ref in item.manifest.chunks),
        )
        for digest in digests:
            if store.has(digest):  # type: ignore[attr-defined]
                clone.put(store.get(digest))  # type: ignore[attr-defined]
    return clone


def _clone_peers(
    peers: Mapping[str, ForwardPeer],
    bundles: Sequence[ScheduledBundle],
) -> dict[str, ForwardPeer]:
    return {
        peer_id: ForwardPeer(peer_id, _clone_store(peer.store, bundles))
        for peer_id, peer in peers.items()
    }


def _clone_scheduler_states(
    states: Mapping[str, FairSchedulerState],
) -> dict[str, FairSchedulerState]:
    return {
        peer_id: FairSchedulerState.from_dict(state.to_dict())
        for peer_id, state in states.items()
    }


def _window_policy(
    base: BearerSchedulingPolicy,
    *,
    logical_source_byte_budget: int,
) -> BearerSchedulingPolicy:
    contact = base.contact_policy
    return BearerSchedulingPolicy(
        bearer_id=base.bearer_id,
        contact_policy=ContactSchedulingPolicy(
            max_source_bytes=logical_source_byte_budget,
            max_bundles=contact.max_bundles,
            max_chunks_per_bundle=contact.max_chunks_per_bundle,
            prefer_completion=contact.prefer_completion,
        ),
        fairness_policy=base.fairness_policy,
    )


def _complete_at_peer(item: ScheduledBundle, peer: ForwardPeer) -> bool:
    if not peer.store.has(item.manifest.fingerprint):
        return False
    if not all(peer.store.has(ref.sha256_digest) for ref in item.manifest.chunks):
        return False
    reconstruct_from_store(item.manifest, peer.store)
    return True


def _seed_prior_history(
    state: RapidEncounterPrototypeState,
    observations: Sequence[RapidPriorMeetingObservation],
    *,
    first_window_s: int | None,
) -> None:
    ordered = sorted(
        observations,
        key=lambda item: (item.observed_at_s, item.node_a, item.node_b),
    )
    for observation in ordered:
        if first_window_s is not None and observation.observed_at_s >= first_window_s:
            raise ValueError(
                "RAPID prior-history observations must precede the first routing window"
            )
        state.observe_prior_meeting(
            observation.node_a,
            observation.node_b,
            now_s=observation.observed_at_s,
            opportunity_bytes_a_to_b=observation.opportunity_bytes_a_to_b,
            opportunity_bytes_b_to_a=observation.opportunity_bytes_b_to_a,
        )


def _post_transfer_control_update(
    state: RapidEncounterPrototypeState,
    selected: Sequence[ScheduledBundle],
    *,
    target: ForwardPeer,
    destination_id: str,
    delivered_at_s: int,
) -> None:
    target_state = state.replica_state(target.peer_id)
    for item in selected:
        if not _complete_at_peer(item, target):
            continue
        target_state.advertise_local_replica(
            item.bundle.bundle_id,
            present=True,
            now_s=delivered_at_s,
        )
        if target.peer_id == destination_id:
            target_state.acknowledge_local_delivery(
                item.bundle.bundle_id,
                delivered_at_s=delivered_at_s,
            )


def run_rapid_deadline_schedule(
    bundles: Sequence[ScheduledBundle],
    *,
    peers: Mapping[str, ForwardPeer],
    ledger: CustodyLedger,
    windows: Sequence[SyntheticContactWindow],
    bearers: Mapping[str, BearerProfile],
    scheduling_policies: Mapping[str, BearerSchedulingPolicy],
    scheduler_states: Mapping[str, FairSchedulerState],
    destination_id: str,
    application_deadlines: Mapping[bytes, int],
    prior_meetings: Sequence[RapidPriorMeetingObservation] = (),
) -> RapidScheduleReport:
    """Run the one-selection RAPID deadline prototype end-to-end.

    This runner intentionally remains outside the common routing comparator.
    It clones mutable network state, uses the same governed/fair Pollicino
    transfer path, and accounts content/protocol wire bytes exactly as the
    existing comparator does. RAPID control work remains entry-count only until
    a control encoding is explicitly designed.
    """

    if not bundles:
        raise ValueError("at least one scheduled bundle is required")
    if not all(isinstance(item, ScheduledBundle) for item in bundles):
        raise TypeError("bundles must contain ScheduledBundle values")
    if not isinstance(peers, Mapping) or not peers:
        raise ValueError("peers must be a non-empty mapping")
    if not isinstance(ledger, CustodyLedger):
        raise TypeError("ledger must be CustodyLedger")
    _require_id("destination_id", destination_id)
    if destination_id not in peers:
        raise KeyError(f"unknown destination peer: {destination_id}")
    if not isinstance(application_deadlines, Mapping):
        raise TypeError("application_deadlines must be a mapping")
    bundle_ids = {item.bundle.bundle_id for item in bundles}
    for bundle_id, deadline_s in application_deadlines.items():
        if bundle_id not in bundle_ids:
            raise KeyError("application deadline references unknown bundle")
        if isinstance(deadline_s, bool) or not isinstance(deadline_s, int) or deadline_s < 0:
            raise ValueError("application deadlines must be non-negative integers")

    local_peers = _clone_peers(peers, bundles)
    local_ledger = CustodyLedger.from_dict(ledger.to_dict())
    local_scheduler_states = _clone_scheduler_states(scheduler_states)
    rapid_state = RapidEncounterPrototypeState()
    ordered_windows = sorted(windows, key=lambda item: (item.start_s, item.encounter_id))
    first_window_s = None if not ordered_windows else ordered_windows[0].start_s
    _seed_prior_history(
        rapid_state,
        prior_meetings,
        first_window_s=first_window_s,
    )

    first_delivery: dict[str, int] = {}
    rapid_windows: list[RapidScheduleWindowReport] = []
    bearer_totals: dict[str, list[int]] = {}

    for window in ordered_windows:
        try:
            source = local_peers[window.source_id]
            target = local_peers[window.target_id]
        except KeyError as exc:
            raise KeyError(f"RAPID window references unknown peer: {exc.args[0]}") from exc
        try:
            bearer = bearers[window.bearer_id]
            base_policy = scheduling_policies[window.bearer_id]
        except KeyError as exc:
            raise KeyError(
                f"RAPID window references unconfigured bearer: {exc.args[0]}"
            ) from exc

        encounter = evaluate_rapid_encounter(
            rapid_state,
            bundles,
            source=source,
            target=target,
            ledger=local_ledger,
            window=window,
            destination_ids=(destination_id,),
            application_deadlines=application_deadlines,
        )

        if encounter.direct_delivery:
            selected_bytes_ids = set(encounter.direct_bundle_ids)
        elif encounter.selected_bundle_id is not None:
            selected_bytes_ids = {encounter.selected_bundle_id}
        else:
            selected_bytes_ids = set()
        selected = tuple(
            item for item in bundles if item.bundle.bundle_id in selected_bytes_ids
        )
        selected_hex_ids = {item.bundle.bundle_id.hex() for item in selected}
        skipped_ids = tuple(
            sorted(
                item.bundle.bundle_id.hex()
                for item in bundles
                if item.bundle.bundle_id.hex() not in selected_hex_ids
            )
        )

        scheduling: BearerSchedulingReport | None = None
        if selected:
            scheduler_state = local_scheduler_states.get(source.peer_id)
            if scheduler_state is None:
                scheduler_state = FairSchedulerState()
                local_scheduler_states[source.peer_id] = scheduler_state
            scheduling = schedule_fair_bearer_contact(
                selected,
                source=source,
                target=target,
                ledger=local_ledger,
                state=scheduler_state,
                bearer=bearer,
                policy=_window_policy(
                    base_policy,
                    logical_source_byte_budget=window.logical_source_byte_budget,
                ),
                transfer_id_base=window.transfer_id_base,
                encounter_id=f"{RAPID_DEADLINE_PROTOTYPE_ID}:{window.encounter_id}",
                now_s=window.start_s,
            )

        routing_window = StrategyWindowReport(
            encounter_id=window.encounter_id,
            source_id=window.source_id,
            target_id=window.target_id,
            bearer_id=window.bearer_id,
            start_s=window.start_s,
            duration_seconds=window.duration_seconds,
            logical_source_byte_budget=window.logical_source_byte_budget,
            selected_bundle_ids=tuple(sorted(selected_hex_ids)),
            skipped_by_strategy_bundle_ids=skipped_ids,
            scheduling=scheduling,
        )
        rapid_windows.append(
            RapidScheduleWindowReport(encounter=encounter, routing=routing_window)
        )

        usage = bearer_totals.setdefault(window.bearer_id, [0, 0, 0])
        usage[0] += 1
        usage[1] += routing_window.used_source_bytes
        usage[2] += routing_window.total_wire_bytes

        delivered_at = window.start_s + window.duration_seconds
        if selected:
            _post_transfer_control_update(
                rapid_state,
                selected,
                target=target,
                destination_id=destination_id,
                delivered_at_s=delivered_at,
            )

        for item in bundles:
            bundle_hex = item.bundle.bundle_id.hex()
            if bundle_hex in first_delivery:
                continue
            if _complete_at_peer(item, local_peers[destination_id]):
                first_delivery[bundle_hex] = delivered_at

    scenario_end_s = max(
        (window.start_s + window.duration_seconds for window in ordered_windows),
        default=0,
    )
    outcomes: list[StrategyBundleOutcome] = []
    for item in bundles:
        bundle_hex = item.bundle.bundle_id.hex()
        delivered = _complete_at_peer(item, local_peers[destination_id])
        outcomes.append(
            StrategyBundleOutcome(
                bundle_id=bundle_hex,
                label=item.label,
                priority=item.priority,
                delivered_destination_ids=(destination_id,) if delivered else (),
                first_delivery_s=first_delivery.get(bundle_hex),
                expired_undelivered_at_scenario_end=(
                    not delivered and item.bundle.expired(scenario_end_s)
                ),
            )
        )

    bearer_usage = tuple(
        StrategyBearerUsage(
            bearer_id=bearer_id,
            kind=bearers[bearer_id].kind,
            window_count=values[0],
            used_source_bytes=values[1],
            total_wire_bytes=values[2],
        )
        for bearer_id, values in sorted(bearer_totals.items())
    )
    routing = RoutingStrategyReport(
        strategy_id=RAPID_DEADLINE_PROTOTYPE_ID,
        windows=tuple(item.routing for item in rapid_windows),
        bearer_usage=bearer_usage,
        outcomes=tuple(outcomes),
        scenario_end_s=scenario_end_s,
    )
    return RapidScheduleReport(
        routing=routing,
        windows=tuple(rapid_windows),
    )
