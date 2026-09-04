from __future__ import annotations

import hashlib
import struct

import pytest

from pollicino.net.catalog import BoundedReference, MAX_LOGICAL_KEY_BYTES, MAX_REFERENCE_BYTES
from pollicino.net.endpoint import (
    AdvertisementMessage,
    AdvertisedIdentity,
    B2BoundsError,
    B2DecodeError,
    B2MessageType,
    EXPERIMENTAL_B2_ENCODING,
    MAX_B2_IDENTITIES_PER_MESSAGE,
    MAX_B2_MESSAGE_BYTES,
    RecordKind,
    RecordMessage,
    ReferenceSelectionMessage,
    RequestMessage,
    decode_message,
    encode_message,
    record_digest,
)
from pollicino.net.query import (
    MAX_QUERY_ID_BYTES,
    MAX_QUERY_PAYLOAD_BYTES,
    MAX_RESULT_ID_BYTES,
    MAX_RESULT_KEYS,
    QueryRecord,
    ResultIdentity,
    ResultRecord,
)


def _messages():
    query = QueryRecord(b"query", b"opaque")
    result = ResultRecord(b"query", b"result", (b"a", b"b"))
    reference = BoundedReference(b"key", b"opaque-reference")
    return (
        AdvertisementMessage(
            RecordKind.QUERY,
            (AdvertisedIdentity(query.query_id, record_digest(RecordKind.QUERY, query)),),
        ),
        RequestMessage(RecordKind.RESULT, (result.identity,)),
        RecordMessage(RecordKind.QUERY, query),
        RecordMessage(RecordKind.RESULT, result),
        RecordMessage(RecordKind.REFERENCE, reference),
        ReferenceSelectionMessage((reference.logical_key,)),
    )


@pytest.mark.parametrize("message", _messages())
def test_every_b2_message_round_trips_canonically(message) -> None:
    first = encode_message(message)
    decoded = decode_message(first)
    assert decoded == message
    assert encode_message(decoded) == first
    assert len(first) <= MAX_B2_MESSAGE_BYTES
    assert EXPERIMENTAL_B2_ENCODING == "pollicino.experimental-b2.v1"


def test_canonical_encoding_sorts_identity_pages() -> None:
    first = RequestMessage(RecordKind.QUERY, (b"z", b"a"))
    second = RequestMessage(RecordKind.QUERY, (b"a", b"z"))
    assert first == second
    assert encode_message(first) == encode_message(second)


def test_corruption_and_truncation_fail_closed() -> None:
    encoded = bytearray(encode_message(_messages()[0]))
    encoded[-1] ^= 0x01
    with pytest.raises(B2DecodeError, match="integrity"):
        decode_message(bytes(encoded))
    with pytest.raises(B2DecodeError):
        decode_message(bytes(encoded[:-1]))


def test_unknown_magic_version_and_type_fail_deterministically() -> None:
    encoded = bytearray(encode_message(_messages()[0]))
    bad_magic = bytearray(encoded)
    bad_magic[0] ^= 0x01
    with pytest.raises(B2DecodeError, match="magic"):
        decode_message(bytes(bad_magic))
    bad_version = bytearray(encoded)
    bad_version[4] = 99
    with pytest.raises(B2DecodeError, match="version"):
        decode_message(bytes(bad_version))
    bad_type = bytearray(encoded)
    bad_type[5] = 99
    with pytest.raises(B2DecodeError, match="type"):
        decode_message(bytes(bad_type))


def test_header_body_length_is_authoritative_even_with_recomputed_digest() -> None:
    encoded = encode_message(_messages()[0])
    header = struct.Struct(">4sBBI32s")
    magic, version, message_type, body_length, _ = header.unpack_from(encoded)
    body = encoded[header.size:] + b"extra"
    changed = header.pack(
        magic, version, message_type, body_length, hashlib.sha256(body).digest()
    ) + body
    with pytest.raises(B2DecodeError, match="length"):
        decode_message(changed)


def test_identity_page_bound_is_hard() -> None:
    identities = tuple(index.to_bytes(2, "big") for index in range(1, 102))
    RequestMessage(RecordKind.QUERY, identities[:MAX_B2_IDENTITIES_PER_MESSAGE])
    with pytest.raises(B2BoundsError):
        RequestMessage(RecordKind.QUERY, identities)


def test_maximum_native_records_fit_one_complete_b2_message() -> None:
    query = QueryRecord(b"q" * MAX_QUERY_ID_BYTES, b"x" * MAX_QUERY_PAYLOAD_BYTES)
    result = ResultRecord(
        b"q" * MAX_QUERY_ID_BYTES,
        b"r" * MAX_RESULT_ID_BYTES,
        tuple(index.to_bytes(2, "big") + b"k" * (MAX_LOGICAL_KEY_BYTES - 2) for index in range(MAX_RESULT_KEYS)),
    )
    reference = BoundedReference(
        b"k" * MAX_LOGICAL_KEY_BYTES, b"r" * MAX_REFERENCE_BYTES
    )
    for kind, record in (
        (RecordKind.QUERY, query),
        (RecordKind.RESULT, result),
        (RecordKind.REFERENCE, reference),
    ):
        encoded = encode_message(RecordMessage(kind, record))
        assert len(encoded) <= MAX_B2_MESSAGE_BYTES
        assert decode_message(encoded) == RecordMessage(kind, record)


def test_duplicate_identity_and_digest_bounds_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicates"):
        RequestMessage(RecordKind.QUERY, (b"same", b"same"))
    with pytest.raises(B2BoundsError):
        AdvertisedIdentity(b"id", b"short")
