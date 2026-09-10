from __future__ import annotations

import hashlib

import pytest

from pollicino.net.endpoint import B2DecodeError, MAX_B2_MESSAGE_BYTES, RecordKind
from pollicino.net.fair_reconciliation import (
    B2F_MAGIC,
    B2F_VERSION,
    DirectoryMessage,
    FairContactSelection,
    MAX_B2F_DESCRIPTORS_PER_MESSAGE,
    MAX_B2F_MESSAGE_BYTES,
    PageDescriptor,
    PageRequestMessage,
    ReferenceDirectoryRequestMessage,
    decode_fair_message,
    encode_fair_message,
)


def _page(index: int) -> PageDescriptor:
    first = (index * 100).to_bytes(4, "big")
    last = (index * 100 + 99).to_bytes(4, "big")
    return PageDescriptor(100, first, last, hashlib.sha256(first + last).digest())


@pytest.mark.parametrize(
    "message",
    (
        DirectoryMessage(RecordKind.QUERY, (_page(0), _page(1))),
        PageRequestMessage(RecordKind.QUERY, (_page(0),)),
        ReferenceDirectoryRequestMessage(),
    ),
)
def test_b2f_encoding_is_canonical_and_round_trips(message) -> None:
    first = encode_fair_message(message)
    second = encode_fair_message(decode_fair_message(first))
    assert first == second
    assert decode_fair_message(first) == message


def test_maximal_directory_fits_in_inherited_complete_message_unit() -> None:
    pages = tuple(_page(index) for index in range(MAX_B2F_DESCRIPTORS_PER_MESSAGE))
    encoded = encode_fair_message(DirectoryMessage(RecordKind.QUERY, pages))
    assert len(encoded) <= MAX_B2F_MESSAGE_BYTES <= MAX_B2_MESSAGE_BYTES


@pytest.mark.parametrize("mutation", ("corrupt", "truncate", "version", "type"))
def test_invalid_b2f_envelope_fails_closed(mutation: str) -> None:
    encoded = bytearray(
        encode_fair_message(DirectoryMessage(RecordKind.QUERY, (_page(0),)))
    )
    if mutation == "corrupt":
        encoded[-1] ^= 1
    elif mutation == "truncate":
        encoded.pop()
    elif mutation == "version":
        encoded[4] = B2F_VERSION + 1
    else:
        encoded[5] = 255
    with pytest.raises(B2DecodeError):
        decode_fair_message(bytes(encoded))


def test_wrong_magic_fails_closed() -> None:
    encoded = bytearray(encode_fair_message(ReferenceDirectoryRequestMessage()))
    encoded[:4] = b"NOPE"
    assert bytes(encoded[:4]) != B2F_MAGIC
    with pytest.raises(B2DecodeError):
        decode_fair_message(bytes(encoded))


def test_contact_policy_can_select_catalog_bound_but_not_more() -> None:
    keys = tuple(index.to_bytes(4, "big") for index in range(10_000))
    assert len(FairContactSelection(left_wants_from_right=keys).left_wants_from_right) == 10_000
    with pytest.raises(Exception):
        FairContactSelection(left_wants_from_right=keys + (b"overflow",))
