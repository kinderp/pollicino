import pytest

from pollicino.net import (
    DeliveryError,
    FRAME_HEADER_BYTES,
    FragmentFrame,
    ScarceLinkProfile,
    fragment_payload,
    reassemble_frames,
    transmit_exact,
)


def test_fragment_frame_round_trip_and_crc_fail_closed() -> None:
    frame = FragmentFrame(transfer_id=17, sequence=0, total=1, payload=b"hello")
    encoded = frame.encode()

    assert len(encoded) == FRAME_HEADER_BYTES + 5
    assert FragmentFrame.decode(encoded) == frame

    corrupted = encoded[:-1] + bytes([encoded[-1] ^ 0x01])
    with pytest.raises(ValueError, match="CRC"):
        FragmentFrame.decode(corrupted)


def test_fragmentation_reassembly_tolerates_identical_duplicates() -> None:
    payload = bytes(range(100))
    frames = fragment_payload(payload, transfer_id=99, max_frame_bytes=48)

    assert len(frames) == 4
    assert all(frame.wire_size <= 48 for frame in frames)
    assert reassemble_frames([frames[0], frames[1], frames[1], frames[2], frames[3]]) == payload


def test_reassembly_rejects_missing_or_conflicting_frames() -> None:
    frames = fragment_payload(b"abcdefghij", transfer_id=3, max_frame_bytes=22)

    with pytest.raises(ValueError, match="missing"):
        reassemble_frames(list(frames[:-1]))

    conflict = FragmentFrame(
        transfer_id=frames[0].transfer_id,
        sequence=frames[0].sequence,
        total=frames[0].total,
        payload=b"different",
    )
    with pytest.raises(ValueError, match="conflicting"):
        reassemble_frames([frames[0], conflict, *frames[1:]])


def test_clean_exact_transfer_has_predictable_accounting() -> None:
    payload = b"x" * 100
    profile = ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=1,
    )

    reconstructed, report = transmit_exact(payload, transfer_id=5, profile=profile)

    assert reconstructed == payload
    assert report.frame_count == 3
    assert report.payload_capacity_bytes == 46
    assert report.data_transmissions == 3
    assert report.retransmissions == 0
    assert report.duplicate_deliveries == 0
    assert report.ack_transmissions == 3
    assert report.data_wire_bytes == 154
    assert report.ack_wire_bytes == 24
    assert report.total_wire_bytes == 178
    assert report.nominal_serialization_seconds == pytest.approx(178 * 8 / 5000)
    assert report.success


def test_impairment_sequence_is_deterministic_and_exercises_retries() -> None:
    payload = bytes((index * 37 + 11) % 256 for index in range(160))
    profile = ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=2400,
        data_loss_ppm=200_000,
        ack_loss_ppm=100_000,
        max_retries=12,
        ack_bytes=8,
        seed=11,
    )

    first_data, first_report = transmit_exact(payload, transfer_id=44, profile=profile)
    second_data, second_report = transmit_exact(payload, transfer_id=44, profile=profile)

    assert first_data == second_data == payload
    assert first_report == second_report
    assert first_report.retransmissions > 0
    assert first_report.duplicate_deliveries > 0


def test_retry_exhaustion_fails_closed() -> None:
    profile = ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=1200,
        data_loss_ppm=1_000_000,
        max_retries=2,
        ack_bytes=8,
        seed=7,
    )

    with pytest.raises(DeliveryError, match="exceeded retry budget"):
        transmit_exact(b"cannot-arrive", transfer_id=9, profile=profile)


def test_profile_and_frame_budget_validation() -> None:
    with pytest.raises(ValueError, match="header"):
        ScarceLinkProfile(max_frame_bytes=FRAME_HEADER_BYTES, bitrate_bps=1000)

    with pytest.raises(ValueError, match="payload byte"):
        fragment_payload(b"x", transfer_id=1, max_frame_bytes=FRAME_HEADER_BYTES)
