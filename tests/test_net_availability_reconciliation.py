import hashlib
import math

from pollicino.net.availability_reconciliation import (
    AvailabilityResearchCodec,
    availability_codec_candidates,
    decode_availability_candidate,
    encode_availability_candidate,
    smallest_availability_candidate,
)
from pollicino.net.store import AvailabilitySummary, MAX_CHUNKS


def _summary(chunk_count: int, available_indices) -> AvailabilitySummary:
    bits = bytearray(math.ceil(chunk_count / 8))
    for index in available_indices:
        byte_index, bit_index = divmod(index, 8)
        bits[byte_index] |= 1 << bit_index
    return AvailabilitySummary(
        manifest_fingerprint=hashlib.sha256(f"manifest-{chunk_count}".encode()).digest(),
        chunk_count=chunk_count,
        available_bits=bytes(bits),
    )


def test_all_research_codecs_roundtrip_exact_availability() -> None:
    patterns = (
        _summary(17, ()),
        _summary(17, range(17)),
        _summary(17, (0, 1, 2, 8, 16)),
        _summary(257, tuple(index for index in range(257) if index % 7 != 0)),
    )
    for summary in patterns:
        for candidate in availability_codec_candidates(summary):
            assert decode_availability_candidate(candidate.encoded) == summary


def test_max_pcm1_sparse_missing_threshold_is_measured_against_real_pna1() -> None:
    # Current PCM1/PNA1 maximum: 65,535 chunks. PNA1 is exactly
    # 39 + ceil(65,535 / 8) = 8,231 bytes.
    chunk_count = MAX_CHUNKS
    pna1_bytes = 39 + math.ceil(chunk_count / 8)
    assert pna1_bytes == 8231

    missing_4095 = set(range(0, 8190, 2))  # 4,095 sparse missing indices
    available_4095 = tuple(
        index for index in range(chunk_count) if index not in missing_4095
    )
    summary_4095 = _summary(chunk_count, available_4095)
    sparse_4095 = encode_availability_candidate(
        summary_4095,
        AvailabilityResearchCodec.MISSING_U16,
    )
    assert len(sparse_4095) == 40 + 2 * 4095 == 8230
    assert len(sparse_4095) < pna1_bytes

    missing_4096 = set(range(0, 8192, 2))
    available_4096 = tuple(
        index for index in range(chunk_count) if index not in missing_4096
    )
    summary_4096 = _summary(chunk_count, available_4096)
    sparse_4096 = encode_availability_candidate(
        summary_4096,
        AvailabilityResearchCodec.MISSING_U16,
    )
    assert len(sparse_4096) == 40 + 2 * 4096 == 8232
    assert len(sparse_4096) > pna1_bytes


def test_sparse_and_range_modes_win_in_different_regimes() -> None:
    chunk_count = MAX_CHUNKS

    scattered_missing = tuple(range(100, 140, 2))  # 20 isolated indices
    scattered_missing_set = set(scattered_missing)
    mostly_complete = _summary(
        chunk_count,
        tuple(index for index in range(chunk_count) if index not in scattered_missing_set),
    )
    best_sparse = smallest_availability_candidate(mostly_complete)
    assert best_sparse.codec is AvailabilityResearchCodec.MISSING_U16
    assert best_sparse.encoded_bytes == 40 + 20 * 2

    contiguous_missing = set(range(20_000, 24_096))
    one_hole = _summary(
        chunk_count,
        tuple(index for index in range(chunk_count) if index not in contiguous_missing),
    )
    best_range = smallest_availability_candidate(one_hole)
    assert best_range.codec is AvailabilityResearchCodec.MISSING_RANGES_U16
    assert best_range.encoded_bytes == 44  # 40-byte envelope + one u16 start/length pair

    only_twenty_available = _summary(
        chunk_count,
        tuple(range(0, 40, 2)),
    )
    available_u16 = encode_availability_candidate(
        only_twenty_available,
        AvailabilityResearchCodec.AVAILABLE_U16,
    )
    assert len(available_u16) == 40 + 20 * 2
    assert decode_availability_candidate(available_u16) == only_twenty_available

    # The first validation disproved the expectation that sparse indices must
    # be smallest here. A 65,535-bit map containing only 20 one-bits is highly
    # structured, so lossless zlib can compress the bitmap below the 80-byte
    # available-u16 representation. Preserve that observed result rather than
    # forcing the initially expected codec to win.
    best_available = smallest_availability_candidate(only_twenty_available)
    assert best_available.codec is AvailabilityResearchCodec.BITMAP_ZLIB
    assert best_available.encoded_bytes < len(available_u16)
    assert decode_availability_candidate(best_available.encoded) == only_twenty_available


def test_compressed_bitmap_is_useful_only_when_bitmap_has_structure() -> None:
    chunk_count = MAX_CHUNKS
    pna1_bytes = len(_summary(chunk_count, ()).encode())
    assert pna1_bytes == 8231

    empty = _summary(chunk_count, ())
    compressed_empty = encode_availability_candidate(
        empty,
        AvailabilityResearchCodec.BITMAP_ZLIB,
    )
    assert len(compressed_empty) < pna1_bytes
    assert decode_availability_candidate(compressed_empty) == empty

    # Deterministic high-entropy bitmap: zlib should not be assumed to help.
    bitmap_bytes = math.ceil(chunk_count / 8)
    raw = bytearray()
    counter = 0
    while len(raw) < bitmap_bytes:
        raw.extend(hashlib.sha256(counter.to_bytes(4, "big")).digest())
        counter += 1
    raw = raw[:bitmap_bytes]
    raw[-1] &= 0x7F  # one unused bit for 65,535 chunks must remain zero
    noisy = AvailabilitySummary(
        manifest_fingerprint=hashlib.sha256(b"noisy-manifest").digest(),
        chunk_count=chunk_count,
        available_bits=bytes(raw),
    )
    compressed_noisy = encode_availability_candidate(
        noisy,
        AvailabilityResearchCodec.BITMAP_ZLIB,
    )
    assert decode_availability_candidate(compressed_noisy) == noisy
    assert len(compressed_noisy) > len(noisy.encode())
