import hashlib

import pytest

from pollicino.net import (
    AvailabilitySummary,
    ChunkManifest,
    PollicinoStore,
    ScarceLinkProfile,
    availability_for,
    build_chunk_manifest,
    reconstruct_from_store,
    sync_missing_chunks,
)


def clean_profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=1,
    )


def unique_chunks(count: int, chunk_size: int = 64) -> bytes:
    parts = []
    for index in range(count):
        seed = hashlib.sha256(f"chunk-{index}".encode()).digest()
        parts.append((seed * ((chunk_size + 31) // 32))[:chunk_size])
    return b"".join(parts)


def test_chunk_manifest_round_trip_and_store_reconstruction() -> None:
    data = unique_chunks(4)
    manifest, chunks = build_chunk_manifest(data, chunk_size=64)
    encoded = manifest.encode()

    assert ChunkManifest.decode(encoded) == manifest
    assert ChunkManifest.decode(encoded).encode() == encoded

    store = PollicinoStore()
    for chunk in chunks:
        store.put(chunk)
    assert reconstruct_from_store(manifest, store) == data

    with pytest.raises(ValueError, match="length mismatch|shorter"):
        ChunkManifest.decode(encoded[:-1])


def test_availability_summary_tracks_content_addresses_not_positions() -> None:
    repeated = b"A" * 64
    other = b"B" * 64
    data = repeated + other + repeated
    manifest, _ = build_chunk_manifest(data, chunk_size=64)
    store = PollicinoStore()
    store.put(repeated)

    summary = availability_for(manifest, store)
    assert summary.has(0)
    assert not summary.has(1)
    assert summary.has(2)
    assert AvailabilitySummary.decode(summary.encode()) == summary


def test_sync_transfers_only_missing_chunks_and_reconstructs_exactly() -> None:
    data = unique_chunks(8)
    manifest, chunks = build_chunk_manifest(data, chunk_size=64)
    sender = PollicinoStore()
    receiver = PollicinoStore()
    for chunk in chunks[:4]:
        receiver.put(chunk)

    reconstructed, report = sync_missing_chunks(
        data,
        chunk_size=64,
        sender_store=sender,
        receiver_store=receiver,
        profile=clean_profile(),
        transfer_id_base=100,
        manifest_on_scarce=True,
    )

    assert reconstructed == data
    assert report.exact
    assert report.chunk_count == 8
    assert report.cached_chunk_count == 4
    assert report.cached_source_bytes == 256
    assert report.missing_chunk_count == 4
    assert report.missing_source_bytes == 256
    assert report.manifest_wire_bytes > len(manifest.encode())
    assert report.availability_wire_bytes > 0
    assert report.chunk_wire_bytes > 0
    assert len(receiver) == 8


def test_fully_cached_pre_resolved_manifest_sends_no_chunk_payload() -> None:
    data = unique_chunks(5)
    _manifest, chunks = build_chunk_manifest(data, chunk_size=64)
    sender = PollicinoStore()
    receiver = PollicinoStore()
    for chunk in chunks:
        receiver.put(chunk)

    reconstructed, report = sync_missing_chunks(
        data,
        chunk_size=64,
        sender_store=sender,
        receiver_store=receiver,
        profile=clean_profile(),
        transfer_id_base=200,
        manifest_on_scarce=False,
    )

    assert reconstructed == data
    assert report.cached_chunk_count == 5
    assert report.missing_chunk_count == 0
    assert report.missing_source_bytes == 0
    assert report.manifest_wire_bytes == 0
    assert report.chunk_wire_bytes == 0
    assert report.total_scarce_wire_bytes == report.availability_wire_bytes
    assert report.total_scarce_if_manifest_pre_resolved == report.availability_wire_bytes


def test_missing_store_chunk_fails_reconstruction() -> None:
    data = unique_chunks(2)
    manifest, chunks = build_chunk_manifest(data, chunk_size=64)
    store = PollicinoStore()
    store.put(chunks[0])
    with pytest.raises(LookupError, match="not present"):
        reconstruct_from_store(manifest, store)


def test_availability_unused_bits_fail_closed() -> None:
    fingerprint = bytes(range(32))
    with pytest.raises(ValueError, match="unused"):
        AvailabilitySummary(
            manifest_fingerprint=fingerprint,
            chunk_count=9,
            available_bits=b"\x00\x80",
        )
