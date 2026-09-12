from __future__ import annotations

import random

import pytest

from pollicino.net.fragmentation import (
    ConflictingFragmentError,
    CrossMessageFragmentError,
    EphemeralFragmentReassembler,
    FragmentBoundsError,
    FragmentDecodeError,
    FragmentFrame,
    fragment_message,
)
from px15_support import compact_summary


def _frames(mtu: int = 128):
    message = compact_summary()
    return message, fragment_message(message, max_frame_bytes=mtu)


def _reassemble(frames, mtu=128):
    receiver = EphemeralFragmentReassembler(max_frame_bytes=mtu)
    completed = []
    for frame in frames:
        result = receiver.add(frame.encode() if isinstance(frame, FragmentFrame) else frame)
        if result.complete_message is not None:
            completed.append(result.complete_message)
    return receiver, completed


def test_reverse_and_seeded_random_order_roundtrip() -> None:
    message, frames = _frames()
    _, reverse = _reassemble(reversed(frames))
    shuffled = list(frames); random.Random(150042).shuffle(shuffled)
    _, random_result = _reassemble(shuffled)
    assert reverse == random_result == [message]


def test_identical_duplicates_are_idempotent() -> None:
    message, frames = _frames()
    stream = [frames[0], frames[0], *frames[1:]]
    _, completed = _reassemble(stream)
    assert completed == [message]


@pytest.mark.parametrize("missing", (0, 5, 10))
def test_first_middle_or_final_loss_is_incomplete(missing: int) -> None:
    _message, frames = _frames()
    receiver, completed = _reassemble(
        frame for index, frame in enumerate(frames) if index != missing
    )
    assert completed == [] and receiver.incomplete


def test_multiple_fragment_loss_is_incomplete() -> None:
    _message, frames = _frames()
    receiver, completed = _reassemble(
        frame for index, frame in enumerate(frames) if index not in (0, 4, 10)
    )
    assert completed == [] and receiver.buffered_fragments == len(frames) - 3


def test_conflicting_duplicate_fails_closed() -> None:
    _message, frames = _frames()
    first = frames[0]
    changed = FragmentFrame(
        first.message_id, first.total_length, first.index, first.count,
        bytes((first.payload[0] ^ 1,)) + first.payload[1:],
    )
    receiver = EphemeralFragmentReassembler(max_frame_bytes=128)
    receiver.add(first.encode())
    with pytest.raises(ConflictingFragmentError):
        receiver.add(changed.encode())


def test_cross_message_contamination_is_rejected() -> None:
    one = fragment_message(compact_summary(), max_frame_bytes=128)
    altered = bytearray(compact_summary()); altered[-1] ^= 1
    # Use a second structurally valid compact summary from another state.
    from pollicino.net.compact_reconciliation import CompactIndependentEndpoint
    from pollicino.net.endpoint import RecordKind
    from px10_support import memory_endpoint, query
    endpoint = memory_endpoint("other"); endpoint.query_results.add_queries((query(1), query(2)))
    other_message = CompactIndependentEndpoint(endpoint.catalog, endpoint.query_results).summary_message(RecordKind.QUERY, 10)
    two = fragment_message(other_message, max_frame_bytes=128)
    receiver = EphemeralFragmentReassembler(max_frame_bytes=128)
    receiver.add(one[0].encode())
    with pytest.raises(CrossMessageFragmentError):
        receiver.add(two[0].encode())


def test_impossible_count_and_payload_shape_rejected() -> None:
    _message, frames = _frames()
    first = frames[0]
    wrong_count = FragmentFrame(
        first.message_id, first.total_length, 0, first.count + 1, first.payload
    )
    receiver = EphemeralFragmentReassembler(max_frame_bytes=128)
    with pytest.raises(FragmentBoundsError):
        receiver.add(wrong_count.encode())
    short = FragmentFrame(
        first.message_id, first.total_length, first.index, first.count, first.payload[:-1]
    )
    with pytest.raises(FragmentBoundsError):
        receiver.add(short.encode())


def test_complete_message_digest_remains_authoritative() -> None:
    message, frames = _frames()
    changed = list(frames)
    final = changed[-1]
    payload = bytes((final.payload[0] ^ 1,)) + final.payload[1:]
    changed[-1] = FragmentFrame(
        final.message_id, final.total_length, final.index, final.count, payload
    )
    receiver = EphemeralFragmentReassembler(max_frame_bytes=128)
    with pytest.raises(FragmentDecodeError, match="identity"):
        for frame in changed:
            receiver.add(frame.encode())


def test_discard_removes_all_ephemeral_progress() -> None:
    _message, frames = _frames()
    receiver = EphemeralFragmentReassembler(max_frame_bytes=128)
    receiver.add(frames[0].encode())
    assert receiver.incomplete
    receiver.discard()
    assert not receiver.incomplete and receiver.buffered_bytes == 0
