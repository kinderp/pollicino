import pytest

from pollicino.net import (
    PollicinoStore,
    RFReplayTrace,
    RFReplayTransmitter,
    RFTraceSample,
    ScarceLinkProfile,
    sync_missing_chunks_step,
)


def profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=2,
        seed=1,
    )


def physical_trace() -> RFReplayTrace:
    return RFReplayTrace(
        source="hw006-42b.json",
        lab="HW-006",
        schema="pollicino-hw006-checkpoint-v1",
        checkpoint="one-wall",
        environment="indoor",
        samples=(
            RFTraceSample(sequence=1, success=True, failure_class=None, frame_bytes=42),
            RFTraceSample(
                sequence=2,
                success=False,
                failure_class="timeout_ambiguous_untethered",
                frame_bytes=42,
            ),
            RFTraceSample(sequence=3, success=True, failure_class=None, frame_bytes=42),
        ),
    )


def test_resumable_session_can_be_driven_by_explicit_rf_extrapolation() -> None:
    data = b"z" * 20
    sender = PollicinoStore()
    receiver = PollicinoStore()
    replay = RFReplayTransmitter(physical_trace(), strict_frame_bytes=False)

    reconstructed, state, report = sync_missing_chunks_step(
        data,
        chunk_size=20,
        sender_store=sender,
        receiver_store=receiver,
        profile=profile(),
        transfer_id_base=900,
        max_chunks=1,
        manifest_on_scarce=False,
        transmitter=replay.transmit_exact,
    )

    assert reconstructed == data
    assert state.completed
    assert state.wire_accounting == "local_data_exact_remote_ack_lower_bound"
    assert report.wire_accounting == state.wire_accounting
    assert report.retransmissions == 1
    assert report.retransmission_data_wire_bytes > 0
    assert report.retransmission_ack_wire_bytes == 0
    assert report.unknown_remote_failure_count == 1
    assert report.breakdown_wire_bytes == report.step_wire_bytes
    assert state.cumulative_breakdown_wire_bytes == state.cumulative_wire_bytes
    assert state.cumulative_unknown_remote_failure_count == 1
    assert replay.position == 3
    assert report.cumulative_wire_bytes == report.step_wire_bytes


def test_strict_42_byte_trace_rejects_differently_sized_session_control_frame() -> None:
    data = b"z" * 20
    replay = RFReplayTransmitter(physical_trace(), strict_frame_bytes=True)

    with pytest.raises(ValueError, match="frame-size mismatch"):
        sync_missing_chunks_step(
            data,
            chunk_size=20,
            sender_store=PollicinoStore(),
            receiver_store=PollicinoStore(),
            profile=profile(),
            transfer_id_base=901,
            max_chunks=1,
            manifest_on_scarce=False,
            transmitter=replay.transmit_exact,
        )

    assert replay.position == 0
