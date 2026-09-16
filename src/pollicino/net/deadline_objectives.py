from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean
from typing import Sequence

from .routing_benchmark import RoutingBenchmarkReport, RoutingBenchmarkScenario
from .scheduling import BundlePriority


def _require_id(name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class ApplicationDeadlineObjective:
    """Benchmark-only usefulness deadline for one bundle in one scenario.

    This value is application evaluation metadata. It is not PNB1 TTL, does
    not extend transport lifetime, and is not serialized onto any bearer.
    """

    scenario_id: str
    bundle_id: str
    deadline_s: int

    def __post_init__(self) -> None:
        _require_id("scenario_id", self.scenario_id)
        _require_id("bundle_id", self.bundle_id)
        if (
            isinstance(self.deadline_s, bool)
            or not isinstance(self.deadline_s, int)
            or self.deadline_s < 0
        ):
            raise ValueError("deadline_s must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class DeadlineBundleOutcome:
    scenario_id: str
    strategy_id: str
    bundle_id: str
    label: str | None
    priority: BundlePriority
    deadline_s: int
    first_delivery_s: int | None

    @property
    def delivered(self) -> bool:
        return self.first_delivery_s is not None

    @property
    def delivered_before_deadline(self) -> bool:
        return self.first_delivery_s is not None and self.first_delivery_s <= self.deadline_s

    @property
    def delivered_late(self) -> bool:
        return self.first_delivery_s is not None and self.first_delivery_s > self.deadline_s

    @property
    def slack_s(self) -> int | None:
        if self.first_delivery_s is None:
            return None
        return self.deadline_s - self.first_delivery_s


@dataclass(frozen=True, slots=True)
class DeadlineStrategyAggregate:
    strategy_id: str
    deadline_opportunity_count: int
    delivered_before_deadline_count: int
    delivered_late_count: int
    undelivered_count: int
    delivery_slack_samples_s: tuple[int, ...]

    @property
    def on_time_delivery_rate(self) -> float:
        if self.deadline_opportunity_count == 0:
            return 0.0
        return self.delivered_before_deadline_count / self.deadline_opportunity_count

    @property
    def eventual_delivery_count(self) -> int:
        return self.delivered_before_deadline_count + self.delivered_late_count

    @property
    def mean_delivery_slack_s(self) -> float | None:
        if not self.delivery_slack_samples_s:
            return None
        return fmean(self.delivery_slack_samples_s)


@dataclass(frozen=True, slots=True)
class ApplicationDeadlineReport:
    outcomes: tuple[DeadlineBundleOutcome, ...]
    strategies: tuple[DeadlineStrategyAggregate, ...]
    evidence_class: str

    def strategy(self, strategy_id: str) -> DeadlineStrategyAggregate:
        for item in self.strategies:
            if item.strategy_id == strategy_id:
                return item
        raise KeyError(f"strategy {strategy_id!r} is not present in deadline report")


def evaluate_application_deadlines(
    benchmark: RoutingBenchmarkReport,
    scenarios: Sequence[RoutingBenchmarkScenario],
    objectives: Sequence[ApplicationDeadlineObjective],
) -> ApplicationDeadlineReport:
    """Evaluate application usefulness independently from transport TTL.

    The evaluator is post-processing only: it does not alter routing selection,
    scheduling, custody, cache state or wire accounting.
    """

    if not isinstance(benchmark, RoutingBenchmarkReport):
        raise TypeError("benchmark must be RoutingBenchmarkReport")
    if not scenarios:
        raise ValueError("at least one routing scenario is required")
    if not objectives:
        raise ValueError("at least one application deadline objective is required")
    if not all(isinstance(item, RoutingBenchmarkScenario) for item in scenarios):
        raise TypeError("scenarios must contain RoutingBenchmarkScenario values")
    if not all(isinstance(item, ApplicationDeadlineObjective) for item in objectives):
        raise TypeError("objectives must contain ApplicationDeadlineObjective values")

    scenarios_by_id = {scenario.scenario_id: scenario for scenario in scenarios}
    if len(scenarios_by_id) != len(scenarios):
        raise ValueError("routing scenarios must have unique scenario IDs")

    objective_keys = [(item.scenario_id, item.bundle_id) for item in objectives]
    if len(objective_keys) != len(set(objective_keys)):
        raise ValueError("application deadline objectives must be unique per scenario/bundle")

    outcomes: list[DeadlineBundleOutcome] = []
    for objective in objectives:
        try:
            scenario = scenarios_by_id[objective.scenario_id]
        except KeyError as exc:
            raise KeyError(
                f"deadline objective references unknown scenario: {objective.scenario_id}"
            ) from exc

        bundles_by_id = {
            item.bundle.bundle_id.hex(): item
            for item in scenario.bundles
        }
        try:
            scheduled = bundles_by_id[objective.bundle_id]
        except KeyError as exc:
            raise KeyError(
                "deadline objective references unknown bundle "
                f"{objective.bundle_id!r} in scenario {objective.scenario_id!r}"
            ) from exc
        if objective.deadline_s < scheduled.bundle.created_at_s:
            raise ValueError(
                "application deadline cannot precede bundle creation time"
            )

        scenario_report = benchmark.scenario(objective.scenario_id)
        for strategy_report in scenario_report.comparison.strategies:
            matched = next(
                (
                    item
                    for item in strategy_report.outcomes
                    if item.bundle_id == objective.bundle_id
                ),
                None,
            )
            if matched is None:
                raise KeyError(
                    f"strategy {strategy_report.strategy_id!r} has no outcome for "
                    f"bundle {objective.bundle_id!r}"
                )
            outcomes.append(
                DeadlineBundleOutcome(
                    scenario_id=objective.scenario_id,
                    strategy_id=strategy_report.strategy_id,
                    bundle_id=objective.bundle_id,
                    label=matched.label,
                    priority=matched.priority,
                    deadline_s=objective.deadline_s,
                    first_delivery_s=matched.first_delivery_s,
                )
            )

    aggregates: list[DeadlineStrategyAggregate] = []
    for benchmark_strategy in benchmark.strategies:
        strategy_outcomes = [
            item
            for item in outcomes
            if item.strategy_id == benchmark_strategy.strategy_id
        ]
        slacks = tuple(
            sorted(
                item.slack_s
                for item in strategy_outcomes
                if item.slack_s is not None
            )
        )
        aggregates.append(
            DeadlineStrategyAggregate(
                strategy_id=benchmark_strategy.strategy_id,
                deadline_opportunity_count=len(strategy_outcomes),
                delivered_before_deadline_count=sum(
                    item.delivered_before_deadline for item in strategy_outcomes
                ),
                delivered_late_count=sum(item.delivered_late for item in strategy_outcomes),
                undelivered_count=sum(not item.delivered for item in strategy_outcomes),
                delivery_slack_samples_s=slacks,
            )
        )

    return ApplicationDeadlineReport(
        outcomes=tuple(outcomes),
        strategies=tuple(aggregates),
        evidence_class=benchmark.evidence_class,
    )
