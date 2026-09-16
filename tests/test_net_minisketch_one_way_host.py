import hashlib
import math
import os
import random

import pytest

from pollicino.net.availability_wire_benchmark import benchmark_availability_wire
from pollicino.net.link import ScarceLinkProfile, transmit_exact
from pollicino.net.minisketch_host import MINISKETCH_LIBRARY_ENV
from pollicino.net.minisketch_one_way_host import (
    reconcile_receiver_availability_at_source,
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


def _source_receiver():
    rng = random.Random(20260827)
    universe = list(range(MAX_CHUNKS))
    common = set(rng.sample(universe, 50_000))
    remaining = [index for index in universe if index not in common]
    source_only = set(rng.sample(remaining, 10))
    remaining = [index for index in remaining if index not in source_only]
    receiver_only = set(rng.sample(remaining, 10))
    fingerprint = hashlib.sha256(b"one-way-native-minisketch").digest()
    return (
        _summary(common | source_only, fingerprint=fingerprint),
        _summary(common | receiver_only, fingerprint=fingerprint),
        tuple(sorted(source_only)),
        tuple(sorted(receiver_only)),
    )


def _profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=221,
    )


def test_receiver_sketch_tells_source_exactly_which_chunks_receiver_lacks() -> None:
    source, receiver, source_only, receiver_only = _source_receiver()
    result = reconcile_receiver_availability_at_source(
        source,
        receiver,
        capacity=32,
    )

    assert result.serialized_sketch_bytes == 64
    assert result.source_only_indices == source_only
    assert result.receiver_only_indices == receiver_only

    # The source needs no second request to classify the difference: source-only
    # indices are directly the useful source->receiver transfer candidates.
    assert all(source.has(index) and not receiver.has(index) for index in result.source_only_indices)
    assert all(receiver.has(index) and not source.has(index) for index in result.receiver_only_indices)


def test_one_way_receiver_sketch_removes_request_round_trip_and_wire() -> None:
    source, receiver, source_only, _receiver_only = _source_receiver()
    result = reconcile_receiver_availability_at_source(
        source,
        receiver,
        capacity=32,
    )
    profile = _profile()

    sketch_message = b"PNM2" + bytes(36) + result.serialized_receiver_sketch
    assert len(sketch_message) == 104
    received, sketch_wire = transmit_exact(
        sketch_message,
        transfer_id=500,
        profile=profile,
    )
    assert received == sketch_message
    assert sketch_wire.frame_count == 3
    assert sketch_wire.total_wire_bytes == 182

    receiver_absolute = benchmark_availability_wire(receiver, profile=profile)
    assert receiver_absolute.best.representation_id == "bitmap_zlib"
    assert receiver_absolute.best.total_wire_bytes > 50 * sketch_wire.total_wire_bytes

    # Previous conservative native checkpoint used sketch + ten-index request.
    request_message = (
        b"PNQ2" + bytes(36)
        + b"".join(index.to_bytes(2, "big") for index in source_only)
    )
    _, request_wire = transmit_exact(
        request_message,
        transfer_id=501,
        profile=profile,
    )
    assert request_wire.total_wire_bytes == 112
    assert sketch_wire.total_wire_bytes + request_wire.total_wire_bytes == 294
    assert sketch_wire.total_wire_bytes < 294
