from __future__ import annotations

import pytest

from pollicino.net.compact_reconciliation import (
    B2C_VERSION,
    CompactBoundsError,
    CompactDecodeError,
    CompactDecodeStatus,
    FingerprintRequestMessage,
    MAX_COMPACT_CAPACITY,
    MAX_COMPACT_MESSAGE_BYTES,
    build_summary,
    decode_compact_message,
    decode_difference,
    encode_compact_message,
)
from pollicino.net.endpoint import MAX_B2_MESSAGE_BYTES, RecordKind


def _identities(count: int, *, start: int = 0) -> tuple[bytes, ...]:
    return tuple(index.to_bytes(4, "big") for index in range(start, start + count))


@pytest.mark.parametrize("capacity", (1, 10, 32, 100, 1_000))
def test_summary_encoding_is_canonical_and_decodes_at_capacity(capacity: int) -> None:
    identities = _identities(capacity)
    summary = build_summary(RecordKind.QUERY, tuple(reversed(identities)), capacity)
    encoded = encode_compact_message(summary)
    assert encoded == encode_compact_message(build_summary(RecordKind.QUERY, identities, capacity))
    assert decode_compact_message(encoded) == summary
    decoded = decode_difference(summary, ())
    assert decoded.status is CompactDecodeStatus.DECODED
    assert len(decoded.source_only_fingerprints) == capacity


def test_largest_summary_remains_one_complete_b1_unit() -> None:
    encoded = encode_compact_message(
        build_summary(RecordKind.QUERY, _identities(10_000), MAX_COMPACT_CAPACITY)
    )
    assert len(encoded) <= MAX_COMPACT_MESSAGE_BYTES <= MAX_B2_MESSAGE_BYTES


def test_capacity_overflow_is_detected_not_silently_incomplete() -> None:
    summary = build_summary(RecordKind.QUERY, _identities(500), 10)
    decoded = decode_difference(summary, ())
    assert decoded.status is CompactDecodeStatus.CAPACITY_EXCEEDED
    assert not decoded.decode_success
    assert decoded.source_only_fingerprints == ()


def test_corrupt_truncated_unknown_version_and_unknown_type_fail_closed() -> None:
    encoded = encode_compact_message(build_summary(RecordKind.QUERY, _identities(10), 10))
    corrupt = bytearray(encoded)
    corrupt[-1] ^= 1
    unknown_version = bytearray(encoded)
    unknown_version[4] = B2C_VERSION + 1
    unknown_type = bytearray(encoded)
    unknown_type[5] = 255
    for candidate in (bytes(corrupt), encoded[:-1], bytes(unknown_version), bytes(unknown_type)):
        with pytest.raises(CompactDecodeError):
            decode_compact_message(candidate)


def test_parameter_bounds_are_enforced() -> None:
    with pytest.raises(CompactBoundsError):
        build_summary(RecordKind.QUERY, (), 0)
    with pytest.raises(CompactBoundsError):
        build_summary(RecordKind.QUERY, (), MAX_COMPACT_CAPACITY + 1)
    with pytest.raises(CompactBoundsError):
        FingerprintRequestMessage(RecordKind.QUERY, ())
