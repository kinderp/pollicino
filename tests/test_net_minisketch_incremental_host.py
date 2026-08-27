import os

import pytest

from pollicino.net.availability_wire_benchmark import benchmark_availability_wire
from pollicino.net.link import transmit_exact
from pollicino.net.minisketch_host import MINISKETCH_LIBRARY_ENV
from pollicino.net.minisketch_incremental_host import (
    attempt_decode_minisketch_prefix,
    serialize_availability_minisketch,
)
from test_net_minisketch_host import _partial_caches, _profile


pytestmark = pytest.mark.skipif(
    not os.environ.get(MINISKETCH_LIBRARY_ENV),
    reason="optional libminisketch host prototype is not installed",
)


def test_large_sketch_serialization_prefix_is_a_valid_smaller_sketch() -> None:
    left, right, left_only, right_only = _partial_caches()
    expected = tuple(sorted((*left_only, *right_only)))

    cap32 = serialize_availability_minisketch(left, capacity=32)
    cap20 = serialize_availability_minisketch(left, capacity=20)
    cap16 = serialize_availability_minisketch(left, capacity=16)
    cap8 = serialize_availability_minisketch(left, capacity=8)

    assert cap8.serialized_bytes == 16
    assert cap16.serialized_bytes == 32
    assert cap20.serialized_bytes == 40
    assert cap32.serialized_bytes == 64
    assert cap32.serialized[:16] == cap8.serialized
    assert cap32.serialized[:32] == cap16.serialized
    assert cap32.serialized[:40] == cap20.serialized

    # An exact-capacity prefix decodes the actual 20-element difference.
    exact = attempt_decode_minisketch_prefix(
        cap32.serialized[:40],
        right,
        capacity=20,
    )
    assert exact.native_decode_succeeded
    assert exact.decoded_indices == expected
    assert exact.left_only_indices == left_only
    assert exact.right_only_indices == right_only

    # Under-capacity attempts cannot possibly produce the complete 20-element
    # ground-truth set because the API is asked for at most 8/16 elements. It may
    # return explicit failure or a false decode; neither is accepted as exact.
    for capacity, byte_count in ((8, 16), (16, 32)):
        attempt = attempt_decode_minisketch_prefix(
            cap32.serialized[:byte_count],
            right,
            capacity=capacity,
        )
        assert not (
            attempt.native_decode_succeeded
            and attempt.decoded_indices == expected
        )


def test_doubling_extension_reuses_raw_prefix_and_stays_below_absolute_wire() -> None:
    left, right, left_only, right_only = _partial_caches()
    expected = tuple(sorted((*left_only, *right_only)))
    cap32 = serialize_availability_minisketch(left, capacity=32)

    # A simple unknown-difference policy: start at capacity 8, then double to 16
    # and 32. Upstream guidance allows a largest sketch to be sent incrementally;
    # only the newly exposed serialization bytes are sent on each extension.
    steps = (
        (8, cap32.serialized[:16]),
        (16, cap32.serialized[16:32]),
        (32, cap32.serialized[32:64]),
    )
    accumulated = b""
    final = None
    profile = _profile()
    incremental_wire = 0
    for transfer_id, (capacity, increment) in enumerate(steps, start=300):
        accumulated += increment
        message = b"PNX2" + bytes(36) + increment
        received, wire = transmit_exact(
            message,
            transfer_id=transfer_id,
            profile=profile,
        )
        assert received == message
        incremental_wire += wire.total_wire_bytes
        attempt = attempt_decode_minisketch_prefix(
            accumulated,
            right,
            capacity=capacity,
        )
        if attempt.native_decode_succeeded and attempt.decoded_indices == expected:
            final = attempt
            break

    assert final is not None
    assert final.capacity == 32
    assert final.left_only_indices == left_only
    assert len(accumulated) == 64
    # Raw sketch bytes are never retransmitted: 16 + 16 + 32 == final 64 bytes.
    assert sum(len(increment) for _capacity, increment in steps) == len(cap32.serialized)

    request = (
        b"PNQ2"
        + bytes(36)
        + b"".join(index.to_bytes(2, "big") for index in final.left_only_indices)
    )
    _, request_wire = transmit_exact(
        request,
        transfer_id=400,
        profile=profile,
    )
    incremental_total = incremental_wire + request_wire.total_wire_bytes

    one_shot = b"PNM2" + bytes(36) + cap32.serialized
    _, one_shot_wire = transmit_exact(
        one_shot,
        transfer_id=401,
        profile=profile,
    )
    one_shot_total = one_shot_wire.total_wire_bytes + request_wire.total_wire_bytes

    absolute = benchmark_availability_wire(left, profile=profile)
    assert incremental_total > one_shot_total  # extra extension headers/ACKs cost bytes
    assert incremental_total < absolute.best.total_wire_bytes
    assert absolute.best.total_wire_bytes > 20 * incremental_total
