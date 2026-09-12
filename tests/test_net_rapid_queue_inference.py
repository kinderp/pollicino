import hashlib

import pytest

from pollicino.net.rapid_queue_inference import (
    RapidQueueEntry,
    RapidTransferOpportunityEstimator,
    estimate_queue_service_from_history,
    estimate_queue_service_meetings,
)


def _bundle(label: str) -> bytes:
    return hashlib.sha256(label.encode()).digest()


def test_transfer_opportunity_estimator_uses_observed_arithmetic_mean() -> None:
    estimator = RapidTransferOpportunityEstimator("a")

    first = estimator.observe("d", opportunity_bytes=100, observed_at_s=10)
    second = estimator.observe("d", opportunity_bytes=200, observed_at_s=20)
    third = estimator.observe("d", opportunity_bytes=150, observed_at_s=30)

    assert first.mean_opportunity_bytes == 100
    assert second.mean_opportunity_bytes == 150
    assert third.mean_opportunity_bytes == 150
    assert third.sample_count == 3
    assert estimator.estimate("d") == third


def test_queue_position_converts_bytes_ahead_into_meetings_needed() -> None:
    first = RapidQueueEntry(_bundle("first"), 80)
    second = RapidQueueEntry(_bundle("second"), 100)
    third = RapidQueueEntry(_bundle("third"), 40)
    queue = (first, second, third)

    one = estimate_queue_service_meetings(
        queue,
        bundle_id=first.bundle_id,
        expected_transfer_bytes_per_meeting=100,
    )
    two = estimate_queue_service_meetings(
        queue,
        bundle_id=second.bundle_id,
        expected_transfer_bytes_per_meeting=100,
    )
    three = estimate_queue_service_meetings(
        queue,
        bundle_id=third.bundle_id,
        expected_transfer_bytes_per_meeting=100,
    )

    assert one.bytes_ahead == 0
    assert one.meetings_needed == 1
    assert two.bytes_ahead == 80
    assert two.cumulative_bytes_through_bundle == 180
    assert two.meetings_needed == 2
    assert three.cumulative_bytes_through_bundle == 220
    assert three.meetings_needed == 3


def test_single_large_object_can_require_multiple_future_meetings() -> None:
    item = RapidQueueEntry(_bundle("large"), 350)
    estimate = estimate_queue_service_meetings(
        (item,),
        bundle_id=item.bundle_id,
        expected_transfer_bytes_per_meeting=128,
    )

    assert estimate.meetings_needed == 3


def test_history_based_queue_estimate_is_unknown_until_observed() -> None:
    item = RapidQueueEntry(_bundle("unknown"), 128)
    estimator = RapidTransferOpportunityEstimator("a")

    assert (
        estimate_queue_service_from_history(
            (item,),
            bundle_id=item.bundle_id,
            destination_id="d",
            opportunity_estimator=estimator,
        )
        is None
    )

    estimator.observe("d", opportunity_bytes=64, observed_at_s=10)
    estimate = estimate_queue_service_from_history(
        (item,),
        bundle_id=item.bundle_id,
        destination_id="d",
        opportunity_estimator=estimator,
    )
    assert estimate is not None
    assert estimate.expected_transfer_bytes_per_meeting == 64
    assert estimate.meetings_needed == 2


def test_queue_estimator_has_no_contact_duration_input_or_hidden_capacity_default() -> None:
    item = RapidQueueEntry(_bundle("explicit"), 100)

    low = estimate_queue_service_meetings(
        (item,),
        bundle_id=item.bundle_id,
        expected_transfer_bytes_per_meeting=25,
    )
    high = estimate_queue_service_meetings(
        (item,),
        bundle_id=item.bundle_id,
        expected_transfer_bytes_per_meeting=100,
    )

    assert low.meetings_needed == 4
    assert high.meetings_needed == 1


def test_queue_and_opportunity_validation_fail_closed() -> None:
    a = _bundle("a")
    with pytest.raises(ValueError, match="positive integer"):
        RapidQueueEntry(a, 0)
    with pytest.raises(ValueError, match="must not be empty"):
        estimate_queue_service_meetings(
            (), bundle_id=a, expected_transfer_bytes_per_meeting=10
        )
    with pytest.raises(ValueError, match="unique"):
        estimate_queue_service_meetings(
            (RapidQueueEntry(a, 10), RapidQueueEntry(a, 20)),
            bundle_id=a,
            expected_transfer_bytes_per_meeting=10,
        )
    with pytest.raises(KeyError, match="not present"):
        estimate_queue_service_meetings(
            (RapidQueueEntry(a, 10),),
            bundle_id=_bundle("missing"),
            expected_transfer_bytes_per_meeting=10,
        )

    estimator = RapidTransferOpportunityEstimator("a")
    with pytest.raises(ValueError, match="itself"):
        estimator.observe("a", opportunity_bytes=10, observed_at_s=1)
    with pytest.raises(ValueError, match="positive integer"):
        estimator.observe("d", opportunity_bytes=0, observed_at_s=1)
    estimator.observe("d", opportunity_bytes=10, observed_at_s=1)
    with pytest.raises(ValueError, match="increase"):
        estimator.observe("d", opportunity_bytes=10, observed_at_s=1)
