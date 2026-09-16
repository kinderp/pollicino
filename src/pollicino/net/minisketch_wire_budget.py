from __future__ import annotations

from dataclasses import dataclass

from .link import ScarceLinkProfile, TransferReport, transmit_exact
from .minisketch_capacity_host import modeled_raw_sketch_bytes


@dataclass(frozen=True, slots=True)
class MinisketchSuccessWireCost:
    capacity: int
    raw_sketch_bytes: int
    sketch_message_bytes: int
    request_count: int
    request_message_bytes: int
    sketch_wire_bytes: int
    request_wire_bytes: int
    total_wire_bytes: int
    evidence_class: str = "model_synthetic"


@dataclass(frozen=True, slots=True)
class MinisketchBreakEvenReport:
    absolute_wire_bytes: int
    request_count: int
    largest_cheaper_capacity: int | None
    first_not_cheaper_capacity: int | None
    largest_cheaper: MinisketchSuccessWireCost | None
    first_not_cheaper: MinisketchSuccessWireCost | None
    evidence_class: str = "model_synthetic"


def _wire(payload: bytes, *, transfer_id: int, profile: ScarceLinkProfile) -> TransferReport:
    received, report = transmit_exact(
        payload,
        transfer_id=transfer_id,
        profile=profile,
    )
    if received != payload:
        raise AssertionError("deterministic wire-budget transfer was not exact")
    return report


def model_minisketch_success_wire(
    *,
    capacity: int,
    request_count: int,
    profile: ScarceLinkProfile,
    sketch_envelope_bytes: int = 40,
    request_envelope_bytes: int = 40,
    transfer_id_base: int = 700,
) -> MinisketchSuccessWireCost:
    """Model successful sketch+request wire for one chosen capacity.

    The sketch payload length is the actual upstream 16-bit serialization size
    (2 bytes/capacity). Content bytes are irrelevant to deterministic PNF1
    framing, so this helper uses zero-filled research envelopes rather than
    requiring libminisketch to be installed.
    """

    for name, value in (
        ("capacity", capacity),
        ("request_count", request_count),
        ("sketch_envelope_bytes", sketch_envelope_bytes),
        ("request_envelope_bytes", request_envelope_bytes),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    if capacity <= 0:
        raise ValueError("capacity must be positive")
    if not isinstance(profile, ScarceLinkProfile):
        raise TypeError("profile must be ScarceLinkProfile")
    if isinstance(transfer_id_base, bool) or not isinstance(transfer_id_base, int):
        raise TypeError("transfer_id_base must be an integer")
    if not 0 <= transfer_id_base < 0xFFFFFFFF:
        raise ValueError("transfer_id_base must leave room for two transfers")

    raw_sketch_bytes = modeled_raw_sketch_bytes(capacity)
    sketch_message_bytes = sketch_envelope_bytes + raw_sketch_bytes
    request_message_bytes = request_envelope_bytes + 2 * request_count
    sketch_payload = bytes(sketch_message_bytes)
    request_payload = bytes(request_message_bytes)
    sketch_report = _wire(
        sketch_payload,
        transfer_id=transfer_id_base,
        profile=profile,
    )
    request_report = _wire(
        request_payload,
        transfer_id=transfer_id_base + 1,
        profile=profile,
    )
    return MinisketchSuccessWireCost(
        capacity=capacity,
        raw_sketch_bytes=raw_sketch_bytes,
        sketch_message_bytes=sketch_message_bytes,
        request_count=request_count,
        request_message_bytes=request_message_bytes,
        sketch_wire_bytes=sketch_report.total_wire_bytes,
        request_wire_bytes=request_report.total_wire_bytes,
        total_wire_bytes=sketch_report.total_wire_bytes + request_report.total_wire_bytes,
    )


def find_minisketch_capacity_break_even(
    *,
    absolute_wire_bytes: int,
    request_count: int,
    profile: ScarceLinkProfile,
    min_capacity: int = 1,
    max_capacity: int = 65_535,
) -> MinisketchBreakEvenReport:
    """Find the first capacity whose successful sketch path is not cheaper.

    This is a wire-budget bound, not a decode-capacity estimator. It tells a
    future adaptive protocol how far it could over-provision/extend a sketch
    before a successful sketch+request exchange would cost at least as much as
    the already-known best absolute availability response.
    """

    if (
        isinstance(absolute_wire_bytes, bool)
        or not isinstance(absolute_wire_bytes, int)
        or absolute_wire_bytes <= 0
    ):
        raise ValueError("absolute_wire_bytes must be a positive integer")
    if isinstance(request_count, bool) or not isinstance(request_count, int) or request_count < 0:
        raise ValueError("request_count must be a non-negative integer")
    if not isinstance(profile, ScarceLinkProfile):
        raise TypeError("profile must be ScarceLinkProfile")
    for name, value in (("min_capacity", min_capacity), ("max_capacity", max_capacity)):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    if min_capacity > max_capacity:
        raise ValueError("min_capacity cannot exceed max_capacity")

    # Cost is monotonic with capacity for this deterministic prefix-fragmentation
    # model: increasing capacity only appends source bytes/frames. Binary search
    # the first point that is not strictly cheaper than the absolute baseline.
    low = min_capacity
    high = max_capacity
    first_not: int | None = None
    while low <= high:
        mid = (low + high) // 2
        cost = model_minisketch_success_wire(
            capacity=mid,
            request_count=request_count,
            profile=profile,
        )
        if cost.total_wire_bytes < absolute_wire_bytes:
            low = mid + 1
        else:
            first_not = mid
            high = mid - 1

    if first_not is None:
        largest_capacity = max_capacity
        largest = model_minisketch_success_wire(
            capacity=largest_capacity,
            request_count=request_count,
            profile=profile,
        )
        return MinisketchBreakEvenReport(
            absolute_wire_bytes=absolute_wire_bytes,
            request_count=request_count,
            largest_cheaper_capacity=largest_capacity,
            first_not_cheaper_capacity=None,
            largest_cheaper=largest,
            first_not_cheaper=None,
        )

    first_cost = model_minisketch_success_wire(
        capacity=first_not,
        request_count=request_count,
        profile=profile,
    )
    largest_capacity = first_not - 1
    largest = None
    if largest_capacity >= min_capacity:
        largest = model_minisketch_success_wire(
            capacity=largest_capacity,
            request_count=request_count,
            profile=profile,
        )
    return MinisketchBreakEvenReport(
        absolute_wire_bytes=absolute_wire_bytes,
        request_count=request_count,
        largest_cheaper_capacity=(
            largest_capacity if largest is not None else None
        ),
        first_not_cheaper_capacity=first_not,
        largest_cheaper=largest,
        first_not_cheaper=first_cost,
    )
