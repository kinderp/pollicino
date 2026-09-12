import hashlib
import math
import random

from pollicino.net.availability_wire_benchmark import benchmark_availability_wire
from pollicino.net.link import ScarceLinkProfile
from pollicino.net.minisketch_incremental_budget import (
    largest_safe_incremental_prefix,
    model_incremental_sketch_budget,
)
from pollicino.net.store import AvailabilitySummary, MAX_CHUNKS


CAPACITIES = (8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096)


def _profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=211,
    )


def _left_partial_cache() -> AvailabilitySummary:
    rng = random.Random(20260827)
    universe = list(range(MAX_CHUNKS))
    common = set(rng.sample(universe, 50_000))
    remaining = [index for index in universe if index not in common]
    left_only = set(rng.sample(remaining, 10))
    bits = bytearray(math.ceil(MAX_CHUNKS / 8))
    for index in common | left_only:
        byte_index, bit_index = divmod(index, 8)
        bits[byte_index] |= 1 << bit_index
    return AvailabilitySummary(
        manifest_fingerprint=hashlib.sha256(b"incremental-budget").digest(),
        chunk_count=MAX_CHUNKS,
        available_bits=bytes(bits),
    )


def test_known_test_request_count_keeps_doubling_safe_through_2048() -> None:
    profile = _profile()
    absolute = benchmark_availability_wire(
        _left_partial_cache(),
        profile=profile,
    ).best
    safe = largest_safe_incremental_prefix(
        CAPACITIES,
        conservative_request_per_capacity=False,
        fixed_request_count=10,
        absolute_wire_bytes=absolute.total_wire_bytes,
        profile=profile,
    )
    assert safe is not None
    assert safe.steps[-1].serialized_capacity == 2048
    assert safe.cumulative_total_wire_bytes < absolute.total_wire_bytes

    next_step = model_incremental_sketch_budget(
        CAPACITIES[:10],
        request_count_reserve=10,
        absolute_wire_bytes=absolute.total_wire_bytes,
        profile=profile,
    )
    assert next_step.steps[-1].serialized_capacity == 4096
    assert not next_step.cheaper_than_absolute


def test_unknown_left_right_split_can_reserve_worst_case_request_and_still_reach_1024() -> None:
    profile = _profile()
    absolute = benchmark_availability_wire(
        _left_partial_cache(),
        profile=profile,
    ).best
    safe = largest_safe_incremental_prefix(
        CAPACITIES,
        conservative_request_per_capacity=True,
        fixed_request_count=0,
        absolute_wire_bytes=absolute.total_wire_bytes,
        profile=profile,
    )
    assert safe is not None
    assert safe.steps[-1].serialized_capacity == 1024
    assert safe.request_count_reserve == 1024
    assert safe.cumulative_total_wire_bytes < absolute.total_wire_bytes

    unsafe = model_incremental_sketch_budget(
        CAPACITIES[:9],
        request_count_reserve=2048,
        absolute_wire_bytes=absolute.total_wire_bytes,
        profile=profile,
    )
    assert unsafe.steps[-1].serialized_capacity == 2048
    assert not unsafe.cheaper_than_absolute


def test_actual_twenty_element_case_succeeds_far_before_any_budget_stop() -> None:
    profile = _profile()
    absolute = benchmark_availability_wire(
        _left_partial_cache(),
        profile=profile,
    ).best
    first_three = model_incremental_sketch_budget(
        (8, 16, 32),
        request_count_reserve=10,
        absolute_wire_bytes=absolute.total_wire_bytes,
        profile=profile,
    )
    assert first_three.steps[-1].serialized_capacity == 32
    assert first_three.cumulative_total_wire_bytes == 452
    assert first_three.cumulative_total_wire_bytes * 20 < absolute.total_wire_bytes
