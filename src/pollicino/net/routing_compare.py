from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from .bearer import BearerKind, BearerProfile
from .bundle import CustodyLedger
from .contact_windows import SyntheticContactWindow
from .fair_scheduling import (
    BearerSchedulingPolicy,
    BearerSchedulingReport,
    FairSchedulerState,
    schedule_fair_bearer_contact,
)
from .scheduling import BundlePriority, ContactSchedulingPolicy, ScheduledBundle
from .store import PollicinoStore, reconstruct_from_store
from .store_forward import ForwardPeer


class RoutingStrategy(Protocol):
    """Select which bundles are eligible in one synthetic contact window."""

    strategy_id: str

    def select_bundles(
        self,
        bundles: Sequence[ScheduledBundle],
        *,
        window: SyntheticContactWindow,
        bearer: BearerProfile,
        source: ForwardPeer,
        target: ForwardPeer,
        ledger: CustodyLedger,
    ) -> tuple[ScheduledBundle, ...]: ...


def _require_strategy_id(value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError("strategy_id must be a non-empty string")


@dataclass(frozen=True, slots=True)
class FloodAllStrategy:
    """Offer every bundle to every available contact window."""

    strategy_id: str = "flood-all"

    def __post_init__(self) -> None:
        _require_strategy_id(self.strategy_id)

    def select_bundles(
        self,
        bundles: Sequence[ScheduledBundle],
        **_: object,
    ) -> tuple[ScheduledBundle, ...]:
        return tuple(bundles)


@dataclass(frozen=True, slots=True)
class GatewayProgressStrategy:
    """Forward only when a synthetic rank says the target is closer to a gateway.

    Lower rank means closer/better. These ranks are scenario metadata, not a
    measured radio property and not a claim that the chosen path is globally
    optimal.
    """

    peer_rank: Mapping[str, int]
    strategy_id: str = "gateway-progress"

    def __post_init__(self) -> None:
        _require_strategy_id(self.strategy_id)
        if not isinstance(self.peer_rank, Mapping) or not self.peer_rank:
            raise ValueError("peer_rank must be a non-empty mapping")
        for peer_id, rank in self.peer_rank.items():
            if not isinstance(peer_id, str) or not peer_id:
                raise ValueError("peer_rank keys must be non-empty strings")
            if isinstance(rank, bool) or not isinstance(rank, int) or rank < 0:
                raise ValueError("peer ranks must be non-negative integers")

    def select_bundles(
        self,
        bundles: Sequence[ScheduledBundle],
        *,
        source: ForwardPeer,
        target: ForwardPeer,
        **_: object,
    ) -> tuple[ScheduledBundle, ...]:
        try:
            source_rank = self.peer_rank[source.peer_id]
            target_rank = self.peer_rank[target.peer_id]
        except KeyError as exc:
            raise KeyError(f"missing gateway-progress rank for peer: {exc.args[0]}") from exc
        return tuple(bundles) if target_rank < source_rank else ()


@dataclass(frozen=True, slots=True)
class EmergencyFloodProgressStrategy:
    """Flood EMERGENCY bundles; require gateway progress for lower priorities."""

    peer_rank: Mapping[str, int]
    strategy_id: str = "emergency-flood-progress"

    def __post_init__(self) -> None:
        _require_strategy_id(self.strategy_id)
        # Reuse the validation contract.
        GatewayProgressStrategy(self.peer_rank)

    def select_bundles(
        self,
        bundles: Sequence[ScheduledBundle],
        *,
        source: ForwardPeer,
        target: ForwardPeer,
        **_: object,
    ) -> tuple[ScheduledBundle, ...]:
        try:
            progress = self.peer_rank[target.peer_id] < self.peer_rank[source.peer_id]
        except KeyError as exc:
            raise KeyError(f"missing gateway-progress rank for peer: {exc.args[0]}") from exc
        if progress:
            return tuple(bundles)
        return tuple(item for item in bundles if item.priority is BundlePriority.EMERGENCY)


@dataclass(frozen=True, slots=True)
class HoldLargeOnBearerStrategy:
    """Hold large non-urgent objects on selected bearer kinds.

    This is a policy experiment such as "do not spend scarce LoRa budget on a
    large NORMAL/BULK object; wait for Wi-Fi". ``max_object_size_bytes`` is a
    policy threshold, not measured bearer capacity.
    """

    max_object_size_bytes: int
    hold_kinds: tuple[BearerKind, ...] = (BearerKind.LORA,)
    priority_override: BundlePriority = BundlePriority.EMERGENCY
    strategy_id: str = "hold-large-on-scarce"

    def __post_init__(self) -> None:
        _require_strategy_id(self.strategy_id)
        if (
            isinstance(self.max_object_size_bytes, bool)
            or not isinstance(self.max_object_size_bytes, int)
            or self.max_object_size_bytes < 0
        ):
            raise ValueError("max_object_size_bytes must be a non-negative integer")
        if not isinstance(self.hold_kinds, tuple) or not self.hold_kinds:
            raise ValueError("hold_kinds must be a non-empty tuple")
        if not all(isinstance(kind, BearerKind) for kind in self.hold_kinds):
            raise TypeError("hold_kinds must contain BearerKind values")
        if not isinstance(self.priority_override, BundlePriority):
            raise TypeError("priority_override must be BundlePriority")

    def select_bundles(
        self,
        bundles: Sequence[ScheduledBundle],
        *,
        bearer: BearerProfile,
        **_: object,
    ) -> tuple[ScheduledBundle, ...]:
        if bearer.kind not in self.hold_kinds:
            return tuple(bundles)
        return tuple(
            item
            for item in bundles
            if item.manifest.object_size <= self.max_object_size_bytes
            or item.priority >= self.priority_override
        )


@dataclass(frozen=True, slots=True)
class StrategyWindowReport:
    encounter_id: str
    source_id: str
    target_id: str
    bearer_id: str
    start_s: int
    duration_seconds: int
    logical_source_byte_budget: int
    selected_bundle_ids: tuple[str, ...]
    skipped_by_strategy_bundle_ids: tuple[str, ...]
    scheduling: BearerSchedulingReport | None

    @property
    def used_source_bytes(self) -> int:
        return 0 if self.scheduling is None else self.scheduling.scheduling.used_source_bytes

    @property
    def total_wire_bytes(self) -> int:
        return 0 if self.scheduling is None else self.scheduling.total_wire_bytes


@dataclass(frozen=True, slots=True)
class StrategyBearerUsage:
    bearer_id: str
    kind: BearerKind
    window_count: int
    used_source_bytes: int
    total_wire_bytes: int


@dataclass(frozen=True, slots=True)
class StrategyBundleOutcome:
    bundle_id: str
    label: str | None
    priority: BundlePriority
    delivered_destination_ids: tuple[str, ...]
    first_delivery_s: int | None
    expired_undelivered_at_scenario_end: bool

    @property
    def delivered(self) -> bool:
        return bool(self.delivered_destination_ids)


@dataclass(frozen=True, slots=True)
class RoutingStrategyReport:
    strategy_id: str
    windows: tuple[StrategyWindowReport, ...]
    bearer_usage: tuple[StrategyBearerUsage, ...]
    outcomes: tuple[StrategyBundleOutcome, ...]
    scenario_end_s: int

    @property
    def delivered_bundle_count(self) -> int:
        return sum(item.delivered for item in self.outcomes)

    @property
    def emergency_delivered_count(self) -> int:
        return sum(
            item.delivered and item.priority is BundlePriority.EMERGENCY
            for item in self.outcomes
        )

    @property
    def expired_undelivered_count(self) -> int:
        return sum(item.expired_undelivered_at_scenario_end for item in self.outcomes)

    @property
    def offered_logical_source_bytes(self) -> int:
        return sum(item.logical_source_byte_budget for item in self.windows)

    @property
    def used_source_bytes(self) -> int:
        return sum(item.used_source_bytes for item in self.windows)

    @property
    def total_wire_bytes(self) -> int:
        return sum(item.total_wire_bytes for item in self.windows)

    @property
    def skipped_window_count(self) -> int:
        return sum(item.scheduling is None for item in self.windows)

    def outcome_for_label(self, label: str) -> StrategyBundleOutcome:
        for item in self.outcomes:
            if item.label == label:
                return item
        raise KeyError(f"bundle label {label!r} is not present in strategy report")


@dataclass(frozen=True, slots=True)
class RoutingComparisonReport:
    strategies: tuple[RoutingStrategyReport, ...]

    def strategy(self, strategy_id: str) -> RoutingStrategyReport:
        for item in self.strategies:
            if item.strategy_id == strategy_id:
                return item
        raise KeyError(f"strategy {strategy_id!r} is not present in comparison")


def _clone_store(
    store: object,
    bundles: Sequence[ScheduledBundle],
) -> PollicinoStore:
    clone = PollicinoStore()
    for item in bundles:
        digests = (item.manifest.fingerprint, *(ref.sha256_digest for ref in item.manifest.chunks))
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
    manifest = item.manifest
    if not peer.store.has(manifest.fingerprint):
        return False
    if not all(peer.store.has(ref.sha256_digest) for ref in manifest.chunks):
        return False
    reconstruct_from_store(manifest, peer.store)
    return True


def _run_strategy(
    strategy: RoutingStrategy,
    bundles: Sequence[ScheduledBundle],
    *,
    peers: Mapping[str, ForwardPeer],
    ledger: CustodyLedger,
    windows: Sequence[SyntheticContactWindow],
    bearers: Mapping[str, BearerProfile],
    scheduling_policies: Mapping[str, BearerSchedulingPolicy],
    scheduler_states: Mapping[str, FairSchedulerState],
    destination_ids: Sequence[str],
) -> RoutingStrategyReport:
    _require_strategy_id(strategy.strategy_id)
    local_peers = _clone_peers(peers, bundles)
    local_ledger = CustodyLedger.from_dict(ledger.to_dict())
    local_states = _clone_scheduler_states(scheduler_states)
    for destination_id in destination_ids:
        if destination_id not in local_peers:
            raise KeyError(f"unknown destination peer: {destination_id}")

    first_delivery: dict[str, int] = {}
    window_reports: list[StrategyWindowReport] = []
    bearer_totals: dict[str, list[int]] = {}
    ordered = sorted(windows, key=lambda item: (item.start_s, item.encounter_id))

    for window in ordered:
        try:
            source = local_peers[window.source_id]
            target = local_peers[window.target_id]
        except KeyError as exc:
            raise KeyError(f"routing window references unknown peer: {exc.args[0]}") from exc
        try:
            bearer = bearers[window.bearer_id]
            base_policy = scheduling_policies[window.bearer_id]
        except KeyError as exc:
            raise KeyError(f"routing window references unconfigured bearer: {exc.args[0]}") from exc

        selected = strategy.select_bundles(
            bundles,
            window=window,
            bearer=bearer,
            source=source,
            target=target,
            ledger=local_ledger,
        )
        selected_ids = {item.bundle.bundle_id.hex() for item in selected}
        skipped_ids = tuple(
            sorted(
                item.bundle.bundle_id.hex()
                for item in bundles
                if item.bundle.bundle_id.hex() not in selected_ids
            )
        )
        scheduling: BearerSchedulingReport | None = None
        if selected:
            state = local_states.get(source.peer_id)
            if state is None:
                state = FairSchedulerState()
                local_states[source.peer_id] = state
            scheduling = schedule_fair_bearer_contact(
                selected,
                source=source,
                target=target,
                ledger=local_ledger,
                state=state,
                bearer=bearer,
                policy=_window_policy(
                    base_policy,
                    logical_source_byte_budget=window.logical_source_byte_budget,
                ),
                transfer_id_base=window.transfer_id_base,
                encounter_id=f"{strategy.strategy_id}:{window.encounter_id}",
                now_s=window.start_s,
            )

        report = StrategyWindowReport(
            encounter_id=window.encounter_id,
            source_id=window.source_id,
            target_id=window.target_id,
            bearer_id=window.bearer_id,
            start_s=window.start_s,
            duration_seconds=window.duration_seconds,
            logical_source_byte_budget=window.logical_source_byte_budget,
            selected_bundle_ids=tuple(sorted(selected_ids)),
            skipped_by_strategy_bundle_ids=skipped_ids,
            scheduling=scheduling,
        )
        window_reports.append(report)

        usage = bearer_totals.setdefault(window.bearer_id, [0, 0, 0])
        usage[0] += 1
        usage[1] += report.used_source_bytes
        usage[2] += report.total_wire_bytes

        delivered_at = window.start_s + window.duration_seconds
        for item in bundles:
            bundle_id = item.bundle.bundle_id.hex()
            if bundle_id in first_delivery:
                continue
            if any(_complete_at_peer(item, local_peers[destination_id]) for destination_id in destination_ids):
                first_delivery[bundle_id] = delivered_at

    scenario_end_s = max(
        (window.start_s + window.duration_seconds for window in ordered),
        default=0,
    )
    outcomes: list[StrategyBundleOutcome] = []
    for item in bundles:
        bundle_id = item.bundle.bundle_id.hex()
        delivered_destinations = tuple(
            destination_id
            for destination_id in destination_ids
            if _complete_at_peer(item, local_peers[destination_id])
        )
        outcomes.append(
            StrategyBundleOutcome(
                bundle_id=bundle_id,
                label=item.label,
                priority=item.priority,
                delivered_destination_ids=delivered_destinations,
                first_delivery_s=first_delivery.get(bundle_id),
                expired_undelivered_at_scenario_end=(
                    not delivered_destinations and item.bundle.expired(scenario_end_s)
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
    return RoutingStrategyReport(
        strategy_id=strategy.strategy_id,
        windows=tuple(window_reports),
        bearer_usage=bearer_usage,
        outcomes=tuple(outcomes),
        scenario_end_s=scenario_end_s,
    )


def compare_synthetic_routing_strategies(
    strategies: Sequence[RoutingStrategy],
    bundles: Sequence[ScheduledBundle],
    *,
    peers: Mapping[str, ForwardPeer],
    ledger: CustodyLedger,
    windows: Sequence[SyntheticContactWindow],
    bearers: Mapping[str, BearerProfile],
    scheduling_policies: Mapping[str, BearerSchedulingPolicy],
    scheduler_states: Mapping[str, FairSchedulerState],
    destination_ids: Sequence[str],
) -> RoutingComparisonReport:
    """Run identical synthetic network state independently under each strategy.

    The comparator deliberately uses the deterministic model execution path.
    It compares policy behavior and does not turn synthetic window durations,
    ranks or logical budgets into physical LoRa/BLE/Wi-Fi/Internet evidence.
    """

    if not strategies:
        raise ValueError("at least one routing strategy is required")
    if not destination_ids:
        raise ValueError("at least one destination_id is required")
    ids = [strategy.strategy_id for strategy in strategies]
    if len(ids) != len(set(ids)):
        raise ValueError("routing strategy IDs must be unique")

    reports = tuple(
        _run_strategy(
            strategy,
            bundles,
            peers=peers,
            ledger=ledger,
            windows=windows,
            bearers=bearers,
            scheduling_policies=scheduling_policies,
            scheduler_states=scheduler_states,
            destination_ids=destination_ids,
        )
        for strategy in strategies
    )
    return RoutingComparisonReport(strategies=reports)
