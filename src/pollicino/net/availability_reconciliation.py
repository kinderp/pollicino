from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import math
import struct
import zlib

from .store import AvailabilitySummary, MAX_CHUNKS


RESEARCH_AVAILABILITY_MAGIC = b"PNR2"
RESEARCH_AVAILABILITY_VERSION = 1
_RESEARCH_HEADER = struct.Struct(">4sBB32sH")
_U16 = struct.Struct(">H")
_RANGE = struct.Struct(">HH")


class AvailabilityResearchCodec(IntEnum):
    MISSING_U16 = 1
    AVAILABLE_U16 = 2
    MISSING_RANGES_U16 = 3
    AVAILABLE_RANGES_U16 = 4
    BITMAP_ZLIB = 5


@dataclass(frozen=True, slots=True)
class AvailabilityCodecCandidate:
    codec: AvailabilityResearchCodec
    encoded: bytes

    @property
    def encoded_bytes(self) -> int:
        return len(self.encoded)


def _indices_from_summary(summary: AvailabilitySummary) -> tuple[tuple[int, ...], tuple[int, ...]]:
    available = tuple(index for index in range(summary.chunk_count) if summary.has(index))
    missing = tuple(index for index in range(summary.chunk_count) if not summary.has(index))
    return available, missing


def _bitmap_from_indices(chunk_count: int, indices: tuple[int, ...]) -> bytes:
    if not 1 <= chunk_count <= MAX_CHUNKS:
        raise ValueError("chunk_count is out of range")
    bits = bytearray(math.ceil(chunk_count / 8))
    previous = -1
    for index in indices:
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < chunk_count:
            raise ValueError("availability index is out of range")
        if index <= previous:
            raise ValueError("availability indices must be strictly increasing")
        previous = index
        byte_index, bit_index = divmod(index, 8)
        bits[byte_index] |= 1 << bit_index
    return bytes(bits)


def _ranges(indices: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    if not indices:
        return ()
    result = []
    start = previous = indices[0]
    for index in indices[1:]:
        if index == previous + 1:
            previous = index
            continue
        result.append((start, previous - start + 1))
        start = previous = index
    result.append((start, previous - start + 1))
    return tuple(result)


def _encode_indices(indices: tuple[int, ...]) -> bytes:
    return b"".join(_U16.pack(index) for index in indices)


def _encode_ranges(indices: tuple[int, ...]) -> bytes:
    return b"".join(_RANGE.pack(start, length) for start, length in _ranges(indices))


def _header(summary: AvailabilitySummary, codec: AvailabilityResearchCodec) -> bytes:
    return _RESEARCH_HEADER.pack(
        RESEARCH_AVAILABILITY_MAGIC,
        RESEARCH_AVAILABILITY_VERSION,
        int(codec),
        summary.manifest_fingerprint,
        summary.chunk_count,
    )


def encode_availability_candidate(
    summary: AvailabilitySummary,
    codec: AvailabilityResearchCodec,
) -> bytes:
    """Encode one lossless research alternative to PNA1.

    This is deliberately not a production PNA2 wire contract. The one-byte
    codec discriminator is the only fixed-header field PNA1 does not already
    need, giving all candidate codecs a common 40-byte research envelope.
    """

    if not isinstance(summary, AvailabilitySummary):
        raise TypeError("summary must be AvailabilitySummary")
    if not isinstance(codec, AvailabilityResearchCodec):
        raise TypeError("codec must be AvailabilityResearchCodec")

    available, missing = _indices_from_summary(summary)
    if codec is AvailabilityResearchCodec.MISSING_U16:
        payload = _encode_indices(missing)
    elif codec is AvailabilityResearchCodec.AVAILABLE_U16:
        payload = _encode_indices(available)
    elif codec is AvailabilityResearchCodec.MISSING_RANGES_U16:
        payload = _encode_ranges(missing)
    elif codec is AvailabilityResearchCodec.AVAILABLE_RANGES_U16:
        payload = _encode_ranges(available)
    elif codec is AvailabilityResearchCodec.BITMAP_ZLIB:
        payload = zlib.compress(summary.available_bits, level=9)
    else:  # pragma: no cover - exhaustive enum guard
        raise ValueError("unsupported availability research codec")
    return _header(summary, codec) + payload


def _decode_indices(payload: bytes, *, chunk_count: int) -> tuple[int, ...]:
    if len(payload) % _U16.size:
        raise ValueError("u16 availability payload length is invalid")
    values = tuple(
        _U16.unpack_from(payload, offset)[0]
        for offset in range(0, len(payload), _U16.size)
    )
    _bitmap_from_indices(chunk_count, values)  # validates range/order/duplicates
    return values


def _decode_ranges(payload: bytes, *, chunk_count: int) -> tuple[int, ...]:
    if len(payload) % _RANGE.size:
        raise ValueError("range availability payload length is invalid")
    values = []
    previous_end = -1
    for offset in range(0, len(payload), _RANGE.size):
        start, length = _RANGE.unpack_from(payload, offset)
        if length == 0:
            raise ValueError("range length must be positive")
        end = start + length
        if start <= previous_end:
            raise ValueError("availability ranges must be ordered and non-overlapping")
        if end > chunk_count:
            raise ValueError("availability range exceeds chunk_count")
        values.extend(range(start, end))
        previous_end = end - 1
    return tuple(values)


def decode_availability_candidate(data: bytes) -> AvailabilitySummary:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if len(data) < _RESEARCH_HEADER.size:
        raise ValueError("research availability data is shorter than its header")
    magic, version, codec_value, fingerprint, chunk_count = _RESEARCH_HEADER.unpack_from(data)
    if magic != RESEARCH_AVAILABILITY_MAGIC:
        raise ValueError("invalid research availability magic")
    if version != RESEARCH_AVAILABILITY_VERSION:
        raise ValueError("unsupported research availability version")
    if not 1 <= chunk_count <= MAX_CHUNKS:
        raise ValueError("research availability chunk_count is out of range")
    try:
        codec = AvailabilityResearchCodec(codec_value)
    except ValueError as exc:
        raise ValueError("unsupported research availability codec") from exc
    payload = data[_RESEARCH_HEADER.size :]

    if codec is AvailabilityResearchCodec.BITMAP_ZLIB:
        try:
            available_bits = zlib.decompress(payload)
        except zlib.error as exc:
            raise ValueError("invalid compressed availability bitmap") from exc
        return AvailabilitySummary(
            manifest_fingerprint=fingerprint,
            chunk_count=chunk_count,
            available_bits=available_bits,
        )

    if codec in {
        AvailabilityResearchCodec.MISSING_U16,
        AvailabilityResearchCodec.AVAILABLE_U16,
    }:
        indices = _decode_indices(payload, chunk_count=chunk_count)
    else:
        indices = _decode_ranges(payload, chunk_count=chunk_count)

    if codec in {
        AvailabilityResearchCodec.AVAILABLE_U16,
        AvailabilityResearchCodec.AVAILABLE_RANGES_U16,
    }:
        available = indices
    else:
        missing = set(indices)
        available = tuple(index for index in range(chunk_count) if index not in missing)

    return AvailabilitySummary(
        manifest_fingerprint=fingerprint,
        chunk_count=chunk_count,
        available_bits=_bitmap_from_indices(chunk_count, tuple(available)),
    )


def availability_codec_candidates(
    summary: AvailabilitySummary,
) -> tuple[AvailabilityCodecCandidate, ...]:
    if not isinstance(summary, AvailabilitySummary):
        raise TypeError("summary must be AvailabilitySummary")
    return tuple(
        AvailabilityCodecCandidate(codec=codec, encoded=encode_availability_candidate(summary, codec))
        for codec in AvailabilityResearchCodec
    )


def smallest_availability_candidate(
    summary: AvailabilitySummary,
) -> AvailabilityCodecCandidate:
    """Return the smallest research candidate with deterministic codec tie-break.

    This helper is for benchmark reporting only. It does not select a production
    PNA2 format and does not modify PNA1 negotiation.
    """

    candidates = availability_codec_candidates(summary)
    return min(candidates, key=lambda item: (item.encoded_bytes, int(item.codec)))
