import hashlib
import math
import random

import pytest

from pollicino.net.store import AvailabilitySummary, MAX_CHUNKS
from pollicino.net.symmetric_reconciliation_gate import (
    model_symmetric_partial_cache_gate,
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


def _near_identical_partial_caches():
    rng = random.Random(20260827)
    universe = list(range(MAX_CHUNKS))
    common = set(rng.sample(universe, 50_000))
    remaining = [index for index in universe if index not in common]
    left_unique = set(rng.sample(remaining, 10))
    remaining_after_left = [index for index in remaining if index not in left_unique]
    right_unique = set(rng.sample(remaining_after_left, 10))
    fingerprint = hashlib.sha256(b"shared-partial-manifest").digest()
    return (
        _summary(common | left_unique, fingerprint=fingerprint),
        _summary(common | right_unique, fingerprint=fingerprint),
    )


def test_symmetric_difference_can_be_tiny_when_absolute_caches_are_large_and_partial() -> None:
    left, right = _near_identical_partial_caches()
    report = model_symmetric_partial_cache_gate(
        left,
        right,
        sketch_capacity=32,  # conservative headroom over actual diff=20
    )

    assert report.left_available_count == 50_010
    assert report.right_available_count == 50_010
    assert report.left_only_count == 10
    assert report.right_only_count == 10
    assert report.symmetric_difference_count == 20

    # 16-bit sketch-size law: 40-byte research envelope + 2*32 bytes.
    assert report.modeled_sketch_bytes == 104
    # One-way LEFT->RIGHT request: 40-byte envelope + ten requested uint16 indices.
    assert report.modeled_one_way_request_bytes == 60
    assert report.modeled_one_way_control_bytes == 164

    # These pseudo-random partial-cache bitmaps are deliberately a regime where
    # absolute state remains much larger than the inter-peer difference.
    assert report.left_absolute.best_absolute_bytes > 1_000
    assert report.right_absolute.best_absolute_bytes > 1_000
    assert report.best_two_absolute_summaries_bytes > 20 * report.modeled_one_way_control_bytes


def test_gate_does_not_pretend_an_under_capacity_sketch_can_decode() -> None:
    left, right = _near_identical_partial_caches()
    with pytest.raises(ValueError, match="below the actual symmetric difference"):
        model_symmetric_partial_cache_gate(left, right, sketch_capacity=19)


def test_gate_requires_same_manifest_identity() -> None:
    left, right = _near_identical_partial_caches()
    mismatched = AvailabilitySummary(
        manifest_fingerprint=hashlib.sha256(b"other-manifest").digest(),
        chunk_count=right.chunk_count,
        available_bits=right.available_bits,
    )
    with pytest.raises(ValueError, match="same manifest"):
        model_symmetric_partial_cache_gate(left, mismatched, sketch_capacity=32)
