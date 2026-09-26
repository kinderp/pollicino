import math

import pytest

from pollicino.net.rapid_deadline_utility import (
    RapidReplicaEstimate,
    deadline_delivery_probability,
    rapid_deadline_marginal_utility,
)


def test_exponential_deadline_probability_matches_closed_form() -> None:
    one = RapidReplicaEstimate("a", mean_direct_meeting_seconds=100.0)
    two = RapidReplicaEstimate("b", mean_direct_meeting_seconds=100.0)

    p_one = deadline_delivery_probability(50.0, (one,))
    p_two = deadline_delivery_probability(50.0, (one, two))

    assert p_one == pytest.approx(1.0 - math.exp(-0.5))
    assert p_two == pytest.approx(1.0 - math.exp(-1.0))
    assert p_two > p_one


def test_marginal_utility_decreases_when_useful_replicas_already_exist() -> None:
    a = RapidReplicaEstimate("a", 100.0)
    b = RapidReplicaEstimate("b", 100.0)
    c = RapidReplicaEstimate("c", 100.0)

    first_extra = rapid_deadline_marginal_utility(
        remaining_useful_seconds=50.0,
        existing_replicas=(a,),
        candidate_replica=b,
        transfer_bytes=64,
    )
    second_extra = rapid_deadline_marginal_utility(
        remaining_useful_seconds=50.0,
        existing_replicas=(a, b),
        candidate_replica=c,
        transfer_bytes=64,
    )

    assert first_extra.marginal_utility > second_extra.marginal_utility > 0
    assert first_extra.marginal_utility_per_byte > second_extra.marginal_utility_per_byte


def test_faster_candidate_has_more_deadline_value() -> None:
    existing = (RapidReplicaEstimate("source", 200.0),)
    fast = RapidReplicaEstimate("fast", 40.0)
    slow = RapidReplicaEstimate("slow", 200.0)

    fast_utility = rapid_deadline_marginal_utility(
        remaining_useful_seconds=60.0,
        existing_replicas=existing,
        candidate_replica=fast,
        transfer_bytes=64,
    )
    slow_utility = rapid_deadline_marginal_utility(
        remaining_useful_seconds=60.0,
        existing_replicas=existing,
        candidate_replica=slow,
        transfer_bytes=64,
    )

    assert fast_utility.marginal_utility > slow_utility.marginal_utility


def test_marginal_utility_per_byte_penalizes_larger_transfer() -> None:
    existing = (RapidReplicaEstimate("source", 100.0),)
    candidate = RapidReplicaEstimate("candidate", 80.0)

    small = rapid_deadline_marginal_utility(
        remaining_useful_seconds=50.0,
        existing_replicas=existing,
        candidate_replica=candidate,
        transfer_bytes=64,
    )
    large = rapid_deadline_marginal_utility(
        remaining_useful_seconds=50.0,
        existing_replicas=existing,
        candidate_replica=candidate,
        transfer_bytes=256,
    )

    assert small.marginal_utility == pytest.approx(large.marginal_utility)
    assert small.marginal_utility_per_byte == pytest.approx(
        4 * large.marginal_utility_per_byte
    )


def test_queue_pressure_reduces_effective_delivery_hazard() -> None:
    free = RapidReplicaEstimate("free", 100.0, meetings_needed=1)
    queued = RapidReplicaEstimate("queued", 100.0, meetings_needed=4)

    assert free.effective_hazard_per_second == pytest.approx(0.01)
    assert queued.effective_hazard_per_second == pytest.approx(0.0025)
    assert deadline_delivery_probability(50.0, (free,)) > deadline_delivery_probability(
        50.0, (queued,)
    )


def test_missed_deadline_has_zero_utility() -> None:
    existing = (RapidReplicaEstimate("source", 100.0),)
    candidate = RapidReplicaEstimate("candidate", 50.0)

    result = rapid_deadline_marginal_utility(
        remaining_useful_seconds=0.0,
        existing_replicas=existing,
        candidate_replica=candidate,
        transfer_bytes=64,
    )

    assert result.probability_before == 0.0
    assert result.probability_after == 0.0
    assert result.marginal_utility == 0.0
    assert result.marginal_utility_per_byte == 0.0


def test_rapid_utility_validation_is_fail_closed() -> None:
    with pytest.raises(ValueError, match="positive"):
        RapidReplicaEstimate("a", 0)
    with pytest.raises(ValueError, match="positive integer"):
        RapidReplicaEstimate("a", 10, meetings_needed=0)
    with pytest.raises(ValueError, match="unique"):
        deadline_delivery_probability(
            10,
            (RapidReplicaEstimate("a", 10), RapidReplicaEstimate("a", 20)),
        )
    with pytest.raises(ValueError, match="already holds"):
        rapid_deadline_marginal_utility(
            remaining_useful_seconds=10,
            existing_replicas=(RapidReplicaEstimate("a", 10),),
            candidate_replica=RapidReplicaEstimate("a", 20),
            transfer_bytes=10,
        )
    with pytest.raises(ValueError, match="positive integer"):
        rapid_deadline_marginal_utility(
            remaining_useful_seconds=10,
            existing_replicas=(),
            candidate_replica=RapidReplicaEstimate("a", 20),
            transfer_bytes=0,
        )
