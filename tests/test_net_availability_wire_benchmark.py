import hashlib
import math

from pollicino.net.availability_wire_benchmark import (
    PNA1_BASELINE_ID,
    benchmark_availability_wire,
)
from pollicino.net.link import ScarceLinkProfile
from pollicino.net.store import AvailabilitySummary, MAX_CHUNKS


def _summary(chunk_count: int, available_indices) -> AvailabilitySummary:
    bits = bytearray(math.ceil(chunk_count / 8))
    for index in available_indices:
        byte_index, bit_index = divmod(index, 8)
        bits[byte_index] |= 1 << bit_index
    return AvailabilitySummary(
        manifest_fingerprint=hashlib.sha256(b"availability-wire").digest(),
        chunk_count=chunk_count,
        available_bits=bytes(bits),
    )


def _no_loss() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=171,
    )


def _impaired() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        data_loss_ppm=50_000,
        ack_loss_ppm=50_000,
        ack_bytes=8,
        max_retries=5,
        seed=172,
    )


def test_sparse_missing_state_reduces_frames_ack_and_wire() -> None:
    missing = set(range(100, 140, 2))  # twenty isolated missing chunks
    summary = _summary(
        MAX_CHUNKS,
        (index for index in range(MAX_CHUNKS) if index not in missing),
    )
    report = benchmark_availability_wire(summary, profile=_no_loss())

    assert report.pna1.source_bytes == 8231
    assert report.best.representation_id == "missing_u16"
    assert report.best.source_bytes == 80
    assert report.best.frame_count == 2
    assert report.pna1.frame_count > 100
    assert report.best.ack_transmissions == report.best.frame_count
    assert report.best.total_wire_bytes < report.pna1.total_wire_bytes


def test_one_contiguous_hole_fits_one_exact_pnf1_frame() -> None:
    missing = set(range(20_000, 24_096))
    summary = _summary(
        MAX_CHUNKS,
        (index for index in range(MAX_CHUNKS) if index not in missing),
    )
    report = benchmark_availability_wire(summary, profile=_no_loss())

    assert report.best.representation_id == "missing_ranges_u16"
    assert report.best.source_bytes == 44
    assert report.best.frame_count == 1
    # 44 source bytes + one 18-byte PNF1 header + one 8-byte ACK.
    assert report.best.total_wire_bytes == 70
    assert report.pna1.total_wire_bytes > 10_000


def test_pna1_remains_best_for_high_entropy_availability() -> None:
    bitmap_bytes = math.ceil(MAX_CHUNKS / 8)
    raw = bytearray()
    counter = 0
    while len(raw) < bitmap_bytes:
        raw.extend(hashlib.sha256(counter.to_bytes(4, "big")).digest())
        counter += 1
    raw = raw[:bitmap_bytes]
    raw[-1] &= 0x7F
    summary = AvailabilitySummary(
        manifest_fingerprint=hashlib.sha256(b"availability-wire-noisy").digest(),
        chunk_count=MAX_CHUNKS,
        available_bits=bytes(raw),
    )
    report = benchmark_availability_wire(summary, profile=_no_loss())

    assert report.best.representation_id == PNA1_BASELINE_ID
    assert report.best.source_bytes == len(summary.encode()) == 8231
    assert all(item.exact for item in report.all_results)


def test_shorter_lossless_codec_keeps_advantage_under_deterministic_impairment() -> None:
    missing = set(range(500, 520))
    summary = _summary(
        MAX_CHUNKS,
        (index for index in range(MAX_CHUNKS) if index not in missing),
    )
    report = benchmark_availability_wire(summary, profile=_impaired())

    assert all(item.exact for item in report.all_results)
    assert report.best.representation_id == "missing_ranges_u16"
    assert report.best.frame_count == 1
    assert report.best.total_wire_bytes < report.pna1.total_wire_bytes
    # Retries remain explicit MODEL_SYNTHETIC evidence rather than being hidden
    # inside a byte-size proxy.
    assert report.pna1.data_transmissions >= report.pna1.frame_count
    assert report.best.data_transmissions >= report.best.frame_count
