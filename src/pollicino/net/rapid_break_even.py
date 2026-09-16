from __future__ import annotations

from dataclasses import dataclass

from .rapid_control_wire import RapidControlWireBreakdown, rapid_modeled_total_wire_bytes
from .rapid_schedule import RapidScheduleReport
from .routing_compare import RoutingStrategyReport


@dataclass(frozen=True, slots=True)
class RapidWireCostComparison:
    baseline_strategy_id: str
    baseline_wire_bytes: int
    rapid_transfer_wire_bytes: int
    rapid_control_wire_bytes: int
    rapid_modeled_total_wire_bytes: int
    delta_vs_baseline_bytes: int
    evidence_class: str = "model_synthetic"

    @property
    def rapid_is_cheaper(self) -> bool:
        return self.delta_vs_baseline_bytes < 0

    @property
    def break_even(self) -> bool:
        return self.delta_vs_baseline_bytes == 0

    @property
    def baseline_is_cheaper(self) -> bool:
        return self.delta_vs_baseline_bytes > 0

    @property
    def governed_transfer_savings_before_control(self) -> int:
        return self.baseline_wire_bytes - self.rapid_transfer_wire_bytes


def compare_rapid_wire_cost(
    rapid: RapidScheduleReport,
    *,
    baseline: RoutingStrategyReport,
    control: RapidControlWireBreakdown,
) -> RapidWireCostComparison:
    """Compare one RAPID model result with one baseline using explicit control bytes.

    Positive ``delta_vs_baseline_bytes`` means RAPID is more expensive. Negative
    means the modeled RAPID total is cheaper. This remains a model-byte result;
    no physical airtime/energy inference is performed.
    """

    if not isinstance(rapid, RapidScheduleReport):
        raise TypeError("rapid must be RapidScheduleReport")
    if not isinstance(baseline, RoutingStrategyReport):
        raise TypeError("baseline must be RoutingStrategyReport")
    if not isinstance(control, RapidControlWireBreakdown):
        raise TypeError("control must be RapidControlWireBreakdown")
    rapid_total = rapid_modeled_total_wire_bytes(rapid, control=control)
    return RapidWireCostComparison(
        baseline_strategy_id=baseline.strategy_id,
        baseline_wire_bytes=baseline.total_wire_bytes,
        rapid_transfer_wire_bytes=rapid.total_wire_bytes_excluding_rapid_control,
        rapid_control_wire_bytes=control.control_wire_bytes,
        rapid_modeled_total_wire_bytes=rapid_total,
        delta_vs_baseline_bytes=rapid_total - baseline.total_wire_bytes,
    )
