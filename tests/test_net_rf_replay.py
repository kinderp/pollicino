import pytest

from pollicino.net import DeliveryError, RFReplayTrace, RFTraceSample, ScarceLinkProfile
from pollicino.net.rf_replay import RFReplayExhausted, RFReplayTransmitter


def profile(*, max_retries: int = 3) -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=42,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=max_retries,
        seed=1,
    )


def trace(*samples: RFTraceSample) -> RFReplayTrace:
    return RFReplayTrace(
        source="physical.json",
        lab="HW-006",
        schema="pollicino-hw006-checkpoint-v1",
        checkpoint="one-wall",
        environment="indoor",
        samples=samples,
    )


def sample(sequence: int, success: bool, failure_class: str | None = None) -> RFTraceSample:
    # PNF1 header is 18 bytes; the test payload below is 24 bytes -> 42-byte frame.
    return RFTraceSample(
        sequence=sequence,
        success=success,
        failure_class=failure_class,
        frame_bytes=42,
    )


def test_physical_replay_drives_pnf1_retry_without_resolving_timeout_cause() -> None:
    oracle = RFReplayTransmitter(
        trace(
            sample(1, False, "timeout_ambiguous_untethered"),
            sample(2, True),
        )
    )

    payload = b"x" * 24
    reconstructed, report = oracle.transmit_exact(
        payload,
        transfer_id=5,
        profile=profile(),
    )

    assert reconstructed == payload
    assert report.frame_count == 1
    assert report.data_transmissions == 2
    assert report.retransmissions == 1
    assert report.data_wire_bytes_exact == 84
    assert report.confirmed_ack_transmissions == 1
    assert report.confirmed_ack_wire_bytes_lower_bound == 8
    assert report.total_wire_bytes_lower_bound == 92
    assert report.trace_samples_consumed == 2
    assert report.failure_class_counts == {"timeout_ambiguous_untethered": 1}
    assert report.delivery_unknown_failures == 1
    assert report.wire_accounting == "local_data_exact_remote_ack_lower_bound"
    assert oracle.position == 2


def test_frame_size_mismatch_fails_closed_without_consuming_sample() -> None:
    mismatched = RFTraceSample(
        sequence=1,
        success=True,
        failure_class=None,
        frame_bytes=60,
    )
    oracle = RFReplayTransmitter(trace(mismatched))

    with pytest.raises(ValueError, match="frame-size mismatch"):
        oracle.transmit_exact(b"x" * 24, transfer_id=1, profile=profile())
    assert oracle.position == 0


def test_explicit_frame_size_extrapolation_is_possible_but_not_implicit() -> None:
    mismatched = RFTraceSample(
        sequence=1,
        success=True,
        failure_class=None,
        frame_bytes=60,
    )
    oracle = RFReplayTransmitter(trace(mismatched), strict_frame_bytes=False)
    reconstructed, report = oracle.transmit_exact(
        b"x" * 24,
        transfer_id=1,
        profile=profile(),
    )

    assert reconstructed == b"x" * 24
    assert report.success
    assert oracle.snapshot()["strict_frame_bytes"] is False


def test_trace_exhaustion_requires_explicit_synthetic_repeat() -> None:
    oracle = RFReplayTransmitter(trace(sample(1, False, "timeout")))
    with pytest.raises(RFReplayExhausted, match="trace exhausted"):
        oracle.transmit_exact(b"x" * 24, transfer_id=1, profile=profile(max_retries=2))

    repeated = RFReplayTransmitter(
        trace(
            sample(1, False, "timeout_ambiguous_untethered"),
            sample(2, True),
        ),
        repeat=True,
    )
    payload = b"y" * 48  # two 42-byte PNF1 frames at 24 payload bytes each.
    reconstructed, report = repeated.transmit_exact(
        payload,
        transfer_id=2,
        profile=profile(max_retries=2),
    )
    assert reconstructed == payload
    assert report.frame_count == 2
    assert report.data_transmissions == 4
    assert report.retransmissions == 2
    assert repeated.position == 4


def test_retry_budget_exhaustion_remains_delivery_error() -> None:
    oracle = RFReplayTransmitter(
        trace(
            sample(1, False, "timeout_ambiguous_untethered"),
            sample(2, False, "timeout_ambiguous_untethered"),
        )
    )
    with pytest.raises(DeliveryError, match="retry budget"):
        oracle.transmit_exact(
            b"x" * 24,
            transfer_id=1,
            profile=profile(max_retries=1),
        )
