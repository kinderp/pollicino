from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .link import ScarceLinkProfile, transmit_exact
from .minisketch_capacity_host import modeled_raw_sketch_bytes


@dataclass(frozen=True, slots=True)
class IncrementalSketchStepCost:
    max_elements: int
    serialized_capacity: int
    new_raw_bytes: int
    cumulative_raw_bytes: int
    increment_message_bytes: int
    increment_wire_bytes: int
    cumulative_sketch_wire_bytes: int


@dataclass(frozen=True, slots=True)
class IncrementalSketchBudgetReport:
    steps: tuple[IncrementalSketchStepCost, ...]
    request_count_reserve: int
    request_wire_bytes: int
    absolute_wire_bytes: int
    evidence_class: str = "model_synthetic"

    @property
    def cumulative_total_wire_bytes(self) -> int:
        if not self.steps:
            return self.request_wire_bytes
        return self.steps[-1].cumulative_sketch_wire_bytes + self.request_wire_bytes

    @property
    def cheaper_than_absolute(self) -> bool:
        return self.cumulative_total_wire_bytes < self.absolute_wire_bytes


def model_incremental_sketch_budget(
    capacities: Sequence[int],
    *,
    request_count_reserve: int,
    absolute_wire_bytes: int,
    profile: ScarceLinkProfile,
    envelope_bytes: int = 40,
    request_envelope_bytes: int = 40,
    transfer_id_base: int = 800,
) -> IncrementalSketchBudgetReport:
    """Account prefix-only sketch extensions plus a reserved final request.

    ``capacities`` are actual serialized capacities, not expected difference
    counts. Raw sketch bytes are never retransmitted: each step sends only the
    suffix between the previous and new serialization lengths. Every extension
    still pays its own research envelope and PNF1 ACK/framing cost.

    ``request_count_reserve`` lets a future protocol reserve either the actual
    known test request count or a conservative bound such as the current sketch
    capacity when the LEFT/RIGHT split is unknown before decode.
    """

    capacities = tuple(capacities)
    if not capacities:
        raise ValueError("at least one incremental capacity is required")
    previous = 0
    for capacity in capacities:
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= previous:
            raise ValueError("capacities must be strictly increasing positive integers")
        previous = capacity
    for name, value in (
        ("request_count_reserve", request_count_reserve),
        ("absolute_wire_bytes", absolute_wire_bytes),
        ("envelope_bytes", envelope_bytes),
        ("request_envelope_bytes", request_envelope_bytes),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    if absolute_wire_bytes <= 0:
        raise ValueError("absolute_wire_bytes must be positive")
    if not isinstance(profile, ScarceLinkProfile):
        raise TypeError("profile must be ScarceLinkProfile")

    previous_raw = 0
    cumulative_wire = 0
    steps = []
    for offset, capacity in enumerate(capacities):
        cumulative_raw = modeled_raw_sketch_bytes(capacity)
        new_raw = cumulative_raw - previous_raw
        payload = bytes(envelope_bytes + new_raw)
        received, transfer = transmit_exact(
            payload,
            transfer_id=transfer_id_base + offset,
            profile=profile,
        )
        if received != payload:
            raise AssertionError("incremental sketch budget transfer was not exact")
        cumulative_wire += transfer.total_wire_bytes
        steps.append(
            IncrementalSketchStepCost(
                max_elements=capacity,
                serialized_capacity=capacity,
                new_raw_bytes=new_raw,
                cumulative_raw_bytes=cumulative_raw,
                increment_message_bytes=len(payload),
                increment_wire_bytes=transfer.total_wire_bytes,
                cumulative_sketch_wire_bytes=cumulative_wire,
            )
        )
        previous_raw = cumulative_raw

    request_payload = bytes(
        request_envelope_bytes + 2 * request_count_reserve
    )
    received, request_transfer = transmit_exact(
        request_payload,
        transfer_id=transfer_id_base + len(capacities),
        profile=profile,
    )
    if received != request_payload:
        raise AssertionError("incremental request budget transfer was not exact")
    return IncrementalSketchBudgetReport(
        steps=tuple(steps),
        request_count_reserve=request_count_reserve,
        request_wire_bytes=request_transfer.total_wire_bytes,
        absolute_wire_bytes=absolute_wire_bytes,
    )


def largest_safe_incremental_prefix(
    capacities: Sequence[int],
    *,
    conservative_request_per_capacity: bool,
    fixed_request_count: int,
    absolute_wire_bytes: int,
    profile: ScarceLinkProfile,
) -> IncrementalSketchBudgetReport | None:
    """Return the longest prefix whose cumulative modeled total beats absolute.

    With ``conservative_request_per_capacity=True``, each candidate prefix
    reserves a final request containing as many uint16 indices as the largest
    sketch capacity in that prefix. This models the worst LEFT-only split before
    reconciliation is decoded. Otherwise ``fixed_request_count`` is used.
    """

    capacities = tuple(capacities)
    best: IncrementalSketchBudgetReport | None = None
    for end in range(1, len(capacities) + 1):
        prefix = capacities[:end]
        request_reserve = (
            prefix[-1]
            if conservative_request_per_capacity
            else fixed_request_count
        )
        report = model_incremental_sketch_budget(
            prefix,
            request_count_reserve=request_reserve,
            absolute_wire_bytes=absolute_wire_bytes,
            profile=profile,
        )
        if not report.cheaper_than_absolute:
            break
        best = report
    return best
