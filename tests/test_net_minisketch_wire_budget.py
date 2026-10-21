import hashlib
import math
import random

from pollicino.net.availability_wire_benchmark import benchmark_availability_wire
from pollicino.net.link import ScarceLinkProfile
from pollicino.net.minisketch_wire_budget import (
    find_minisketch_capacity_break_even,
    model_minisketch_success_wire,
)
from pollicino.net.store import AvailabilitySummary, MAX_CHUNKS


def _profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=201,
    )


def _summary(indices, *, fingerprint: bytes) -> AvailabilitySummary:
    bits = bytearray(math.ceil(MAX_CHUNKS / 8))
    for index in indices:
        byte_index, bit_index = divmod(index, 8)
        bits[byte_index] |= 1 << bit_index
    return AvailabilitySummary(
        manifest_fingerprint=fingerprint,
        chunk_count=MAX_CHUNKS,
        available_bits=bytes(bits),
    )


def _left_partial_cache() -> AvailabilitySummary:
    rng = random.Random(20260827)
    universe = list(range(MAX_CHUNKS))
    common = set(rng.sample(universe, 50_000))
    remaining = [index for index in universe if index not in common]
    left_only = set(rng.sample(remaining, 10))
    fingerprint = hashlib.sha256(b"minisketch-wire-budget").digest()
    return _summary(common | left_only, fingerprint=fingerprint)


def test_success_wire_matches_native_checkpoint_capacity_32() -> None:
    cost = model_minisketch_success_wire(
        capacity=32,
        request_count=10,
        profile=_profile(),
    )
    assert cost.raw_sketch_bytes == 64
    assert cost.sketch_message_bytes == 104
    assert cost.request_message_bytes == 60
    assert cost.total_wire_bytes == 294


def test_break_even_leaves_large_headroom_over_twenty_element_difference() -> None:
    left = _left_partial_cache()
    profile = _profile()
    absolute = benchmark_availability_wire(left, profile=profile).best
    assert absolute.representation_id == "bitmap_zlib"

    report = find_minisketch_capacity_break_even(
        absolute_wire_bytes=absolute.total_wire_bytes,
        request_count=10,
        profile=profile,
    )
    assert report.largest_cheaper_capacity is not None
    assert report.first_not_cheaper_capacity is not None
    assert report.largest_cheaper_capacity >= 20
    assert report.largest_cheaper is not None
    assert report.first_not_cheaper is not None
    assert report.largest_cheaper.total_wire_bytes < absolute.total_wire_bytes
    assert report.first_not_cheaper.total_wire_bytes >= absolute.total_wire_bytes
    assert report.first_not_cheaper_capacity == report.largest_cheaper_capacity + 1


def test_break_even_is_not_assumed_to_equal_manifest_or_difference_size() -> None:
    profile = _profile()
    report = find_minisketch_capacity_break_even(
        absolute_wire_bytes=1_000,
        request_count=0,
        profile=profile,
        max_capacity=2_000,
    )
    assert report.first_not_cheaper_capacity is not None
    assert 1 < report.first_not_cheaper_capacity < 2_000
