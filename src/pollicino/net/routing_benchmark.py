from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, median
from typing import Mapping, Sequence

from .bearer import BearerKind, BearerProfile
from .bundle import CustodyLedger
from .contact_windows import SyntheticContactWindow
from .fair_scheduling import BearerSchedulingPolicy, FairSchedulerState
from .routing_compare import (
    RoutingComparisonReport,
    RoutingStrategy,
    RoutingStrategyReport,
    compare_synthetic_routing_strategies,
)
from .scheduling import BundlePriority, ScheduledBundle
from .store_forward import ForwardPeer


def _require_id(name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class RoutingBenchmarkScenario:
    """One independent synthetic scenario in a routing benchmark.

    Strategy objects live inside the scenario so scenario-specific metadata such
    as synthetic gateway ranks can change while the stable ``strategy_id`` is
    still aggregated across scenarios.
    """

    scenario_id: str
    strategies: tuple[RoutingStrategy, ...]
    bundles: tuple[ScheduledBundle, ...]
    peers: Mapping[str, ForwardPeer]
    ledger: CustodyLedger
    windows: tuple[SyntheticContactWindow, ...]
    bearers: Mapping[str, BearerProfile]
    scheduling_policies: Mapping[str, BearerSchedulingPolicy]
    scheduler_states: Mapping[str, FairSchedulerState]
    destination_ids: tuple[str, ...]
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_id("scenario_id", self.scenario_id)
        if not self.strategies:
            raise ValueError("scenario must contain at least one routing strategy")
        strategy_ids = [strategy.strategy_id for strategy in self.strategies]
        if len(strategy_ids) != len(set(strategy_ids)):
            raise ValueError("scenario routing strategy IDs must be unique")
        if not self.bundles:
            raise ValueError("scenario must contain at least one bundle")
        if not self.peers:
            raise ValueError("scenario must contain at least one peer")
        if not isinstance(self.ledger, CustodyLedger):
            raise TypeError("ledger must be CustodyLedger")
        if not self.destination_ids:
            raise ValueError("scenario must contain at least one destination_id")
        for destination_id in self.destination_ids:
            _require_id("destination_id", destination_id)
            if destination_id not in self.peers:
                raise KeyError(f"unknown destination peer: {destination_id}")
        for tag in self.tags:
            _require_id("tag", tag)


@dataclass(frozen=True, slots=True)
class RoutingBenchmarkScenarioReport:
    scenario_id: str
    tags: tuple[str, ...]
    comparison: RoutingComparisonReport


@dataclass(frozen=True, slots=True)
class BenchmarkBearerAggregate:
    bearer_id: str
    kind: BearerKind
    scenario_count: int
    window_count: int
    used_source_bytes: int
    total_wire_bytes: int


@dataclass(frozen=True, slots=True)
class BenchmarkStrategyAggregate:
    strategy_id: str
    scenario_count: int
    bundle_opportunity_count: int
    delivered_bundle_count: int
    emergency_opportunity_count: int
    emergency_delivered_count: int
    expired_undelivered_count: int
    delivery_latency_samples_s: tuple[int, ...]
    used_source_bytes: int
    total_wire_bytes: int
    skipped_window_count: int
    total_window_count: int
    bearer_usage: tuple[BenchmarkBearerAggregate, ...]

    @property
    def delivery_rate(self) -> float:
        total = self.bundle_opportunity_count
        return 0.0 if total == 0 else self.delivered_bundle_count / total

    @property
    def emergency_delivery_rate(self) -> float:
        total = self.emergency_opportunity_count
        return 0.0 if total == 0 else self.emergency_delivered_count / total

    @property
    def mean_delivery_latency_s(self) -> float | None:
        if not self.delivery_latency_samples_s:
            return None
        return fmean(self.delivery_latency_samples_s)

    @property
    def median_delivery_latency_s(self) -> float | None:
        if not self.delivery_latency_samples_s:
            return None
        return float(median(self.delivery_latency_samples_s))

    @property
    def mean_wire_bytes_per_delivered_bundle(self) -> float | None:
        if self.delivered_bundle_count == 0:
            return None
        return self.total_wire_bytes / self.delivered_bundle_count


@dataclass(frozen=True, slots=True)
class RoutingBenchmarkReport:
    scenarios: tuple[RoutingBenchmarkScenarioReport, ...]
    strategies: tuple[BenchmarkStrategyAggregate, ...]

    def strategy(self, strategy_id: str) -> BenchmarkStrategyAggregate:
        for item in self.strategies:
            if item.strategy_id == strategy_id:
                return item
        raise KeyError(f"strategy {strategy_id!r} is not present in benchmark")

    def scenario(self, scenario_id: str) -> RoutingBenchmarkScenarioReport:
        for item in self.scenarios:
            if item.scenario_id == scenario_id:
                return item
        raise KeyError(f"scenario {scenario_id!r} is not present in benchmark")


def _bundle_created_at_by_id(scenario: RoutingBenchmarkScenario) -> dict[str, int]:
    return {
        item.bundle.bundle_id.hex(): item.bundle.created_at_s
        for item in scenario.bundles
    }


def _aggregate_strategy(
    strategy_id: str,
    scenario_reports: Sequence[tuple[RoutingBenchmarkScenario, RoutingStrategyReport]],
) -> BenchmarkStrategyAggregate:
    bundle_opportunities = 0
    delivered = 0
    emergency_opportunities = 0
    emergency_delivered = 0
    expired = 0
    latencies: list[int] = []
    used_source_bytes = 0
    total_wire_bytes = 0
    skipped_windows = 0
    total_windows = 0
    bearer_totals: dict[str, list[object]] = {}

    for scenario, report in scenario_reports:
        created_at = _bundle_created_at_by_id(scenario)
        bundle_opportunities += len(report.outcomes)
        delivered += report.delivered_bundle_count
        emergency_opportunities += sum(
            outcome.priority is BundlePriority.EMERGENCY for outcome in report.outcomes
        )
        emergency_delivered += report.emergency_delivered_count
        expired += report.expired_undelivered_count
        used_source_bytes += report.used_source_bytes
        total_wire_bytes += report.total_wire_bytes
        skipped_windows += report.skipped_window_count
        total_windows += len(report.windows)

        for outcome in report.outcomes:
            if outcome.first_delivery_s is None:
                continue
            origin_s = created_at[outcome.bundle_id]
            latency = outcome.first_delivery_s - origin_s
            if latency < 0:
                raise ValueError(
                    "synthetic delivery time cannot precede bundle creation time"
                )
            latencies.append(latency)

        for usage in report.bearer_usage:
            current = bearer_totals.get(usage.bearer_id)
            if current is None:
                bearer_totals[usage.bearer_id] = [
                    usage.kind,
                    1,
                    usage.window_count,
                    usage.used_source_bytes,
                    usage.total_wire_bytes,
                ]
                continue
            if current[0] is not usage.kind:
                raise ValueError(
                    f"bearer {usage.bearer_id!r} changes kind across benchmark scenarios"
                )
            current[1] = int(current[1]) + 1
            current[2] = int(current[2]) + usage.window_count
            current[3] = int(current[3]) + usage.used_source_bytes
            current[4] = int(current[4]) + usage.total_wire_bytes

    bearer_usage = tuple(
        BenchmarkBearerAggregate(
            bearer_id=bearer_id,
            kind=values[0],  # type: ignore[arg-type]
            scenario_count=int(values[1]),
            window_count=int(values[2]),
            used_source_bytes=int(values[3]),
            total_wire_bytes=int(values[4]),
        )
        for bearer_id, values in sorted(bearer_totals.items())
    )
    return BenchmarkStrategyAggregate(
        strategy_id=strategy_id,
        scenario_count=len(scenario_reports),
        bundle_opportunity_count=bundle_opportunities,
        delivered_bundle_count=delivered,
        emergency_opportunity_count=emergency_opportunities,
        emergency_delivered_count=emergency_delivered,
        expired_undelivered_count=expired,
        delivery_latency_samples_s=tuple(sorted(latencies)),
        used_source_bytes=used_source_bytes,
        total_wire_bytes=total_wire_bytes,
        skipped_window_count=skipped_windows,
        total_window_count=total_windows,
        bearer_usage=bearer_usage,
    )


def run_synthetic_routing_benchmark(
    scenarios: Sequence[RoutingBenchmarkScenario],
) -> RoutingBenchmarkReport:
    """Aggregate routing-policy behavior over multiple independent scenarios.

    This benchmark intentionally reports separate delivery, latency and traffic
    dimensions. It does not manufacture a global winner score, and all scenario
    timing/rank/contact-budget inputs remain synthetic unless a future evidence
    adapter explicitly replaces them with measured observations.
    """

    if not scenarios:
        raise ValueError("at least one routing benchmark scenario is required")

    scenario_ids = [scenario.scenario_id for scenario in scenarios]
    if len(scenario_ids) != len(set(scenario_ids)):
        raise ValueError("routing benchmark scenario IDs must be unique")

    expected_strategy_ids = tuple(
        strategy.strategy_id for strategy in scenarios[0].strategies
    )
    expected_strategy_set = set(expected_strategy_ids)
    scenario_reports: list[RoutingBenchmarkScenarioReport] = []
    per_strategy: dict[str, list[tuple[RoutingBenchmarkScenario, RoutingStrategyReport]]] = {
        strategy_id: [] for strategy_id in expected_strategy_ids
    }

    for scenario in scenarios:
        strategy_ids = tuple(strategy.strategy_id for strategy in scenario.strategies)
        if set(strategy_ids) != expected_strategy_set or len(strategy_ids) != len(expected_strategy_ids):
            raise ValueError(
                "every benchmark scenario must expose the same unique strategy IDs"
            )
        comparison = compare_synthetic_routing_strategies(
            scenario.strategies,
            scenario.bundles,
            peers=scenario.peers,
            ledger=scenario.ledger,
            windows=scenario.windows,
            bearers=scenario.bearers,
            scheduling_policies=scenario.scheduling_policies,
            scheduler_states=scenario.scheduler_states,
            destination_ids=scenario.destination_ids,
        )
        scenario_reports.append(
            RoutingBenchmarkScenarioReport(
                scenario_id=scenario.scenario_id,
                tags=scenario.tags,
                comparison=comparison,
            )
        )
        reports_by_id = {report.strategy_id: report for report in comparison.strategies}
        for strategy_id in expected_strategy_ids:
            per_strategy[strategy_id].append((scenario, reports_by_id[strategy_id]))

    aggregates = tuple(
        _aggregate_strategy(strategy_id, per_strategy[strategy_id])
        for strategy_id in expected_strategy_ids
    )
    return RoutingBenchmarkReport(
        scenarios=tuple(scenario_reports),
        strategies=aggregates,
    )
