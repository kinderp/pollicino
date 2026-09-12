from __future__ import annotations

import hashlib
import struct

import pytest

from pollicino.net.catalog import BoundedReference
from pollicino.net.compact_reconciliation import CompactIndependentEndpoint
from pollicino.net.endpoint import (
    AdvertisedIdentity,
    AdvertisementMessage,
    MAX_B2_MESSAGE_BYTES,
    RecordKind,
    RecordMessage,
    ReferenceSelectionMessage,
    encode_message,
)
from pollicino.net.fragmentation import (
    B4_FRAGMENT_MAGIC,
    BoundedFragmentStreamReader,
    FRAGMENT_HEADER_BYTES,
    FragmentBoundsError,
    FragmentDecodeError,
    FragmentFrame,
    IncompleteFragmentStreamError,
    MAX_FRAGMENTS_PER_MESSAGE,
    MAX_REASSEMBLY_BYTES,
    MIN_FRAGMENT_FRAME_BYTES,
    fragment_message,
)
from pollicino.net.query import QueryRecord, ResultIdentity
from px10_support import memory_endpoint, query


MTUS = (64, 128, 256, 512, 1024, 1500, 4096)


def compact_summary(capacity: int = 10) -> bytes:
    endpoint = memory_endpoint("compact")
    endpoint.query_results.add_query(query(1))
    return CompactIndependentEndpoint(endpoint.catalog, endpoint.query_results).summary_message(
        RecordKind.QUERY, capacity
    )


def maximum_message() -> bytes:
    entries = tuple(
        AdvertisedIdentity(
            ResultIdentity(index.to_bytes(2, "big") + bytes(126), bytes(128)),
            bytes((index % 251,)) * 32,
        )
        for index in range(100)
    )
    return encode_message(AdvertisementMessage(RecordKind.RESULT, entries))


def messages() -> tuple[bytes, ...]:
    return (
        encode_message(ReferenceSelectionMessage((b"key",))),
        compact_summary(),
        compact_summary(1000),
        encode_message(RecordMessage(RecordKind.QUERY, QueryRecord(b"q", bytes(4096)))),
        encode_message(RecordMessage(RecordKind.REFERENCE, BoundedReference(b"k", bytes(4096)))),
        maximum_message(),
    )


def test_fragment_contract_bounds_are_derived_from_b2() -> None:
    assert FRAGMENT_HEADER_BYTES == 52
    assert MIN_FRAGMENT_FRAME_BYTES == 53
    assert MAX_REASSEMBLY_BYTES == MAX_B2_MESSAGE_BYTES == 29_245
    assert MAX_FRAGMENTS_PER_MESSAGE == 2_438


@pytest.mark.parametrize("mtu", MTUS)
def test_real_protocol_messages_roundtrip_every_registered_mtu(mtu: int) -> None:
    for encoded in messages():
        frames = fragment_message(encoded, max_frame_bytes=mtu)
        assert all(len(frame.encode()) <= mtu for frame in frames)
        assert b"".join(frame.payload for frame in frames) == encoded
        assert all(frame.message_id == hashlib.sha256(encoded).digest() for frame in frames)


def test_maximum_lawful_message_reaches_exact_inherited_bound() -> None:
    encoded = maximum_message()
    assert len(encoded) == MAX_B2_MESSAGE_BYTES
    assert len(fragment_message(encoded, max_frame_bytes=64)) == MAX_FRAGMENTS_PER_MESSAGE


def test_capacity_10_compact_probe_is_797_bytes() -> None:
    encoded = compact_summary()
    assert len(encoded) == 797
    counts = {
        mtu: len(fragment_message(encoded, max_frame_bytes=mtu)) for mtu in MTUS
    }
    assert counts == {64: 67, 128: 11, 256: 4, 512: 2, 1024: 1, 1500: 1, 4096: 1}
    assert len(compact_summary(1000)) == 28_517


def _query_with_encoded_size(size: int) -> bytes:
    # B2 query record with one-byte ID has 50 bytes of fixed envelope/body.
    return encode_message(
        RecordMessage(RecordKind.QUERY, QueryRecord(b"q", bytes(size - 50)))
    )


def test_one_fragment_and_one_byte_over_payload_boundary() -> None:
    payload_capacity = 128 - FRAGMENT_HEADER_BYTES
    assert len(fragment_message(_query_with_encoded_size(payload_capacity), max_frame_bytes=128)) == 1
    assert len(fragment_message(_query_with_encoded_size(payload_capacity + 1), max_frame_bytes=128)) == 2


def test_exact_two_fragment_boundary() -> None:
    payload_capacity = 128 - FRAGMENT_HEADER_BYTES
    frames = fragment_message(_query_with_encoded_size(2 * payload_capacity), max_frame_bytes=128)
    assert len(frames) == 2
    assert all(len(frame.encode()) == 128 for frame in frames)


def test_minimum_mtu_and_too_small_mtu() -> None:
    assert fragment_message(messages()[0], max_frame_bytes=MIN_FRAGMENT_FRAME_BYTES)
    with pytest.raises(FragmentBoundsError):
        fragment_message(messages()[0], max_frame_bytes=FRAGMENT_HEADER_BYTES)


def test_frame_crc_rejects_payload_corruption() -> None:
    frame = bytearray(fragment_message(compact_summary(), max_frame_bytes=128)[0].encode())
    frame[-1] ^= 1
    with pytest.raises(FragmentDecodeError, match="CRC"):
        FragmentFrame.decode(bytes(frame), max_frame_bytes=128)


@pytest.mark.parametrize("offset", (0, 4, 5))
def test_unknown_magic_version_or_type_fails(offset: int) -> None:
    frame = bytearray(fragment_message(compact_summary(), max_frame_bytes=1024)[0].encode())
    frame[offset] = 255
    with pytest.raises(FragmentDecodeError):
        FragmentFrame.decode(bytes(frame), max_frame_bytes=1024)


def test_fragment_stream_handles_one_byte_reads_and_concatenation() -> None:
    encoded = b"".join(frame.encode() for frame in fragment_message(compact_summary(), max_frame_bytes=128))
    reader = BoundedFragmentStreamReader(max_frame_bytes=128)
    recovered = []
    for value in encoded:
        recovered.extend(reader.feed(bytes((value,))))
    reader.close()
    assert len(recovered) == 11


@pytest.mark.parametrize("cut", (1, FRAGMENT_HEADER_BYTES - 1, FRAGMENT_HEADER_BYTES + 1))
def test_truncated_fragment_stream_fails(cut: int) -> None:
    encoded = fragment_message(compact_summary(), max_frame_bytes=128)[0].encode()
    reader = BoundedFragmentStreamReader(max_frame_bytes=128)
    assert reader.feed(encoded[:cut]) == ()
    with pytest.raises(IncompleteFragmentStreamError):
        reader.close()


def test_oversized_total_rejected_after_bounded_header() -> None:
    header = struct.pack(
        ">4sBB32sIHHHI",
        B4_FRAGMENT_MAGIC, 1, 1, bytes(32), MAX_B2_MESSAGE_BYTES + 1,
        0, 1, 1, 0,
    )
    reader = BoundedFragmentStreamReader(max_frame_bytes=64)
    with pytest.raises(FragmentBoundsError):
        reader.feed(header)
    assert reader.maximum_buffer_bytes == FRAGMENT_HEADER_BYTES
