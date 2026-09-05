import hashlib
import math
import os
import random

import pytest

from pollicino.net.availability_wire_benchmark import benchmark_availability_wire
from pollicino.net.link import ScarceLinkProfile, transmit_exact
from pollicino.net.minisketch_host import (
    MINISKETCH_LIBRARY_ENV,
    MINISKETCH_UPSTREAM_COMMIT,
    MinisketchUnavailable,
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
    fingerprint = hashlib.sha256(b"native-minisketch-manifest").digest()
    return (
        _summary(common | left_only, fingerprint=fingerprint),
        _summary(common | right_only, fingerprint=fingerprint),
        tuple(sorted(left_only)),
        tuple(sorted(right_only)),
    )


def _profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=191,
    )


def test_upstream_libminisketch_decodes_exact_partial_cache_difference() -> None:
    left, right, left_only, right_only = _partial_caches()
    result = reconcile_partial_caches_with_minisketch(
        left,
        right,
        capacity=32,
    )

    assert result.upstream_commit == MINISKETCH_UPSTREAM_COMMIT
    assert result.bits == 16
    assert result.capacity == 32
    # Upstream size law b*c bits: 16 * 32 / 8 = 64 raw serialized bytes.
    assert result.serialized_sketch_bytes == 64
    assert result.left_only_indices == left_only
    assert result.right_only_indices == right_only
    assert result.symmetric_difference_indices == tuple(sorted((*left_only, *right_only)))
    assert result.timings.build_left_ns > 0
    assert result.timings.build_right_ns > 0
    assert result.timings.serialize_left_ns >= 0
    assert result.timings.merge_decode_ns > 0


def test_actual_sketch_plus_request_is_far_smaller_than_best_absolute_wire() -> None:
    left, right, left_only, _right_only = _partial_caches()
    result = reconcile_partial_caches_with_minisketch(
        left,
        right,
        capacity=32,
    )
    profile = _profile()

    # Keep the same conservative 40-byte research envelope used by PNR2 gate
    # modeling, but put the ACTUAL upstream 64-byte serialized sketch inside it.
    sketch_message = b"PNM2" + bytes(36) + result.serialized_sketch
    request_message = (
        b"PNQ2"
        + bytes(36)
        + b"".join(index.to_bytes(2, "big") for index in result.left_only_indices)
    )
    assert len(sketch_message) == 104
    assert len(request_message) == 60

    sketch_received, sketch_wire = transmit_exact(
        sketch_message,
        transfer_id=100,
        profile=profile,
    )
    request_received, request_wire = transmit_exact(
        request_message,
        transfer_id=101,
        profile=profile,
    )
    assert sketch_received == sketch_message
    assert request_received == request_message
    assert sketch_wire.frame_count == 3
    assert request_wire.frame_count == 2
    native_reconciliation_wire = sketch_wire.total_wire_bytes + request_wire.total_wire_bytes

    absolute = benchmark_availability_wire(left, profile=profile)
    assert absolute.best.representation_id == "bitmap_zlib"
    assert native_reconciliation_wire < absolute.best.total_wire_bytes
    assert absolute.best.total_wire_bytes > 20 * native_reconciliation_wire


def test_adapter_fails_cleanly_for_missing_library_path() -> None:
    left, right, _left_only, _right_only = _partial_caches()
    with pytest.raises(MinisketchUnavailable):
        reconcile_partial_caches_with_minisketch(
            left,
            right,
            capacity=32,
            library_path="/definitely/not/a/libminisketch.so",
        )
