from pollicino.net import ScarceLinkProfile
from pollicino.net.link import TransferReport
from pollicino.net.rf_replay import RFReplayTransferReport
from pollicino.net.trc import classify_transfer_wire


def profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=42,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=1,
    )


def test_deterministic_transfer_trc_does_not_double_count_retransmission() -> None:
    payload = b"x" * 24  # one 42-byte encoded PNF1 frame
    report = TransferReport(
        source_bytes=24,
        reconstructed_bytes=24,
        frame_count=1,
        payload_capacity_bytes=24,
        data_transmissions=2,
        retransmissions=1,
        duplicate_deliveries=1,
        ack_transmissions=2,
        data_wire_bytes=84,
        ack_wire_bytes=16,
        total_wire_bytes=100,
        nominal_serialization_seconds=0.16,
        success=True,
    )

    breakdown = classify_transfer_wire(
        payload,
        transfer_id=10,
        profile=profile(),
        report=report,
    )

    assert breakdown.primary_data_wire_bytes == 42
    assert breakdown.primary_ack_wire_bytes == 8
    assert breakdown.retransmission_data_wire_bytes == 42
    assert breakdown.retransmission_ack_wire_bytes == 8
    assert breakdown.primary_wire_bytes == 50
    assert breakdown.retransmission_wire_bytes == 50
    assert breakdown.accounted_wire_bytes == 100
    assert breakdown.accounted_bits == 800
    assert breakdown.accounting == "deterministic_model_exact"


def test_physical_replay_trc_keeps_unknown_remote_response_out_of_lower_bound() -> None:
    payload = b"x" * 24
    report = RFReplayTransferReport(
        source_bytes=24,
        reconstructed_bytes=24,
        frame_count=1,
        payload_capacity_bytes=24,
        data_transmissions=2,
        retransmissions=1,
        data_wire_bytes_exact=84,
        confirmed_ack_transmissions=1,
        confirmed_ack_wire_bytes_lower_bound=8,
        total_wire_bytes_lower_bound=92,
        nominal_serialization_seconds_lower_bound=0.1472,
        trace_samples_consumed=2,
        trace_start_position=0,
        trace_end_position=2,
        failure_classes=(("timeout_ambiguous_untethered", 1),),
        delivery_unknown_failures=1,
        success=True,
    )

    breakdown = classify_transfer_wire(
        payload,
        transfer_id=11,
        profile=profile(),
        report=report,
    )

    assert breakdown.primary_data_wire_bytes == 42
    assert breakdown.primary_ack_wire_bytes == 8
    assert breakdown.retransmission_data_wire_bytes == 42
    assert breakdown.retransmission_ack_wire_bytes == 0
    assert breakdown.accounted_wire_bytes == 92
    assert breakdown.unknown_remote_failure_count == 1
    assert breakdown.accounting == "local_data_exact_remote_ack_lower_bound"
