import hashlib
import math
import os
import random

import pytest

from pollicino.net.minisketch_capacity_host import (
    compute_host_minisketch_capacity,
    compute_host_minisketch_max_elements,
    modeled_raw_sketch_bytes,
)
from pollicino.net.minisketch_host import (
    MINISKETCH_LIBRARY_ENV,
    reconcile_partial_caches_with_minisketch,
)
from pollicino.net.store import AvailabilitySummary, MAX_CHUNKS


pytestmark = pytest.mark.skipif(
    not os.environ.get(MINISKETCH_LIBRARY_ENV),
    reason="optional libminisketch host prototype is not installed",
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


def _partial_caches():
    rng = random.Random(20260827)
    universe = list(range(MAX_CHUNKS))
    common = set(rng.sample(universe, 50_000))
    remaining = [index for index in universe if index not in common]
    left_only = set(rng.sample(remaining, 10))
    remaining = [index for index in remaining if index not in left_only]
    right_only = set(rng.sample(remaining, 10))
    fingerprint = hashlib.sha256(b"minisketch-capacity-host").digest()
    return (
        _summary(common | left_only, fingerprint=fingerprint),
        _summary(common | right_only, fingerprint=fingerprint),
        tuple(sorted(left_only)),
        tuple(sorted(right_only)),
    )


def test_upstream_capacity_grows_with_false_positive_target() -> None:
    capacities = [
        compute_host_minisketch_capacity(20, fpbits=fpbits)
        for fpbits in (0, 16, 32, 64)
    ]
    assert capacities == sorted(capacities)
    assert capacities[0] == 20
    assert all(capacity >= 20 for capacity in capacities)
    assert [modeled_raw_sketch_bytes(value) for value in capacities] == [
        2 * value for value in capacities
    ]


def test_capacity_inverse_preserves_requested_decodable_count() -> None:
    for max_elements in (8, 16, 20, 32):
        for fpbits in (16, 32, 64):
            capacity = compute_host_minisketch_capacity(
                max_elements,
                fpbits=fpbits,
            )
            supported = compute_host_minisketch_max_elements(
                capacity,
                fpbits=fpbits,
            )
            assert supported >= max_elements


def test_fp_protected_capacity_still_decodes_real_twenty_element_difference() -> None:
    left, right, left_only, right_only = _partial_caches()
    expected = tuple(sorted((*left_only, *right_only)))
    capacity = compute_host_minisketch_capacity(20, fpbits=32)
    result = reconcile_partial_caches_with_minisketch(
        left,
        right,
        capacity=capacity,
    )

    assert result.symmetric_difference_indices == expected
    assert result.left_only_indices == left_only
    assert result.right_only_indices == right_only
    assert result.serialized_sketch_bytes == modeled_raw_sketch_bytes(capacity)
