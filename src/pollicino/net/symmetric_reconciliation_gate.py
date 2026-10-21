from __future__ import annotations

from dataclasses import dataclass

from .availability_reconciliation import availability_codec_candidates
from .store import AvailabilitySummary


@dataclass(frozen=True, slots=True)
class AbsoluteAvailabilityCost:
    pna1_bytes: int
    best_alternative_bytes: int
    best_alternative_id: str

    @property
    def best_absolute_bytes(self) -> int:
        return min(self.pna1_bytes, self.best_alternative_bytes)

    @property
    def best_absolute_id(self) -> str:
        if self.pna1_bytes <= self.best_alternative_bytes:
            return "pna1-bitmap"
        return self.best_alternative_id


@dataclass(frozen=True, slots=True)
class SymmetricPartialCacheGateReport:
    chunk_count: int
    left_available_count: int
    right_available_count: int
    left_only_count: int
    right_only_count: int
    symmetric_difference_count: int
    left_absolute: AbsoluteAvailabilityCost
    right_absolute: AbsoluteAvailabilityCost
    sketch_capacity: int
    modeled_sketch_bytes: int
    modeled_one_way_request_bytes: int
    modeled_one_way_control_bytes: int
    evidence_class: str = "model_theoretical"

    @property
    def best_two_absolute_summaries_bytes(self) -> int:
        return (
            self.left_absolute.best_absolute_bytes
            + self.right_absolute.best_absolute_bytes
        )


def _available_indices(summary: AvailabilitySummary) -> set[int]:
    return {
        index
        for index in range(summary.chunk_count)
        if summary.has(index)
    }


def _absolute_cost(summary: AvailabilitySummary) -> AbsoluteAvailabilityCost:
    candidates = availability_codec_candidates(summary)
    best = min(candidates, key=lambda item: (item.encoded_bytes, int(item.codec)))
    return AbsoluteAvailabilityCost(
        pna1_bytes=len(summary.encode()),
        best_alternative_bytes=best.encoded_bytes,
        best_alternative_id=best.codec.name.lower(),
    )


def model_symmetric_partial_cache_gate(
    left: AvailabilitySummary,
    right: AvailabilitySummary,
    *,
    sketch_capacity: int,
    research_envelope_bytes: int = 40,
    request_envelope_bytes: int = 40,
) -> SymmetricPartialCacheGateReport:
    """Compare absolute availability with a minisketch-sized theoretical model.

    This does not implement minisketch. It uses only the documented size law
    for a b-bit sketch of capacity c: b*c bits. Current chunk indices fit in 16
    bits after an index+1 mapping, so the modeled sketch payload is 2*c bytes.

    For one-way LEFT -> RIGHT synchronization, RIGHT can classify every decoded
    symmetric-difference index using its own local set and return the LEFT-only
    indices it wants. The request is conservatively modeled as a 40-byte common
    envelope plus 2 bytes per LEFT-only index.

    The result is a gate experiment, not a production PNA2/minisketch format.
    """

    if not isinstance(left, AvailabilitySummary) or not isinstance(
        right, AvailabilitySummary
    ):
        raise TypeError("left/right must be AvailabilitySummary values")
    if left.manifest_fingerprint != right.manifest_fingerprint:
        raise ValueError("partial-cache summaries must target the same manifest")
    if left.chunk_count != right.chunk_count:
        raise ValueError("partial-cache summaries must have the same chunk_count")
    for name, value in (
        ("sketch_capacity", sketch_capacity),
        ("research_envelope_bytes", research_envelope_bytes),
        ("request_envelope_bytes", request_envelope_bytes),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")

    left_set = _available_indices(left)
    right_set = _available_indices(right)
    left_only = left_set - right_set
    right_only = right_set - left_set
    difference = left_only | right_only
    if sketch_capacity < len(difference):
        raise ValueError(
            "sketch_capacity is below the actual symmetric difference in this gate model"
        )

    sketch_bytes = research_envelope_bytes + 2 * sketch_capacity
    request_bytes = request_envelope_bytes + 2 * len(left_only)
    return SymmetricPartialCacheGateReport(
        chunk_count=left.chunk_count,
        left_available_count=len(left_set),
        right_available_count=len(right_set),
        left_only_count=len(left_only),
        right_only_count=len(right_only),
        symmetric_difference_count=len(difference),
        left_absolute=_absolute_cost(left),
        right_absolute=_absolute_cost(right),
        sketch_capacity=sketch_capacity,
        modeled_sketch_bytes=sketch_bytes,
        modeled_one_way_request_bytes=request_bytes,
        modeled_one_way_control_bytes=sketch_bytes + request_bytes,
    )
