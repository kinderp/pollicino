from __future__ import annotations

import random
import struct

import pytest

from pollicino.net.compact_reconciliation import (
    CompactDecodeError,
    CompactIndependentEndpoint,
)
from pollicino.net.endpoint import (
    B2DecodeError,
    B2_MAGIC,
    MAX_B2_MESSAGE_BYTES,
    RecordKind,
    RecordMessage,
    encode_message,
)
from pollicino.net.process_io import (
    BoundedMessageStreamReader,
    IncompleteProcessMessageError,
    MAX_PROCESS_IO_MESSAGE_BYTES,
    PROCESS_IO_EXTRA_WIRE_BYTES,
    PROCESS_STREAM_HEADER_BYTES,
    ProcessIOBoundsError,
    ProcessIOError,
    validate_complete_message,
)
from px10_support import memory_endpoint, query
from px14_support import parse_stream, split_bytes


def _record(index: int = 1) -> bytes:
    return encode_message(RecordMessage(RecordKind.QUERY, query(index)))


def test_existing_envelope_is_the_only_stream_boundary() -> None:
    assert PROCESS_STREAM_HEADER_BYTES == struct.calcsize(">4sBBI32s") == 42
    assert PROCESS_IO_EXTRA_WIRE_BYTES == 0
    assert MAX_PROCESS_IO_MESSAGE_BYTES == MAX_B2_MESSAGE_BYTES


@pytest.mark.parametrize("sizes", ((65536,), (1,), (42, 1), (2, 3, 5, 7, 11)))
def test_arbitrary_segmentation_recovers_identical_message(sizes) -> None:
    encoded = _record()
    assert parse_stream(encoded, sizes) == (encoded,)


def test_seeded_random_segmentation_is_deterministic() -> None:
    randomizer = random.Random(140031)
    sizes = tuple(randomizer.randint(1, 31) for _ in range(20))
    assert parse_stream(_record(), sizes) == (_record(),)


def test_many_concatenated_messages_decode_once_each() -> None:
    messages = tuple(_record(index) for index in range(1, 20))
    assert parse_stream(b"".join(messages), (65536,)) == messages


def test_message_boundary_can_share_one_chunk() -> None:
    messages = (_record(1), _record(2), _record(3))
    reader = BoundedMessageStreamReader()
    assert reader.feed(b"".join(messages)) == messages
    reader.close()
    assert reader.complete_messages == 3


def test_clean_eof_after_complete_message_is_valid() -> None:
    reader = BoundedMessageStreamReader()
    assert reader.feed(_record()) == (_record(),)
    reader.close()
    reader.close()


@pytest.mark.parametrize("cut", (1, 41, 42, 43, -1))
def test_eof_mid_message_is_fail_closed(cut) -> None:
    encoded = _record()
    stop = len(encoded) - 1 if cut == -1 else cut
    reader = BoundedMessageStreamReader()
    assert reader.feed(encoded[:stop]) == ()
    with pytest.raises(IncompleteProcessMessageError):
        reader.close()


def test_declared_oversize_rejected_before_body_buffering() -> None:
    header = struct.pack(
        ">4sBBI32s", B2_MAGIC, 1, 1, MAX_B2_MESSAGE_BYTES, bytes(32)
    )
    reader = BoundedMessageStreamReader()
    with pytest.raises(ProcessIOBoundsError):
        reader.feed(header)
    assert reader.maximum_buffer_bytes == PROCESS_STREAM_HEADER_BYTES


def test_unknown_magic_rejected_at_header() -> None:
    reader = BoundedMessageStreamReader()
    with pytest.raises(ProcessIOError):
        reader.feed(struct.pack(">4sBBI32s", b"NOPE", 1, 1, 0, bytes(32)))


def test_body_corruption_reaches_existing_integrity_authority() -> None:
    encoded = bytearray(_record())
    encoded[-1] ^= 1
    frame = parse_stream(bytes(encoded))[0]
    with pytest.raises(B2DecodeError):
        validate_complete_message(frame)


@pytest.mark.parametrize("header_offset", (4, 5))
def test_unknown_version_or_type_fails_in_existing_decoder(header_offset) -> None:
    encoded = bytearray(_record())
    encoded[header_offset] = 255
    with pytest.raises(B2DecodeError):
        validate_complete_message(parse_stream(bytes(encoded))[0])


def test_compact_message_uses_the_same_stream_reader() -> None:
    endpoint = memory_endpoint("local")
    endpoint.query_results.add_query(query(1))
    encoded = CompactIndependentEndpoint(
        endpoint.catalog, endpoint.query_results
    ).summary_message(RecordKind.QUERY, 10)
    assert parse_stream(encoded, (1,)) == (encoded,)
    assert validate_complete_message(encoded) is not None


def test_stream_message_count_is_bounded() -> None:
    reader = BoundedMessageStreamReader(max_messages=1)
    with pytest.raises(ProcessIOBoundsError):
        reader.feed(_record(1) + _record(2))
