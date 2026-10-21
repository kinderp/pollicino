from pollicino.net.destination_queue_service import estimate_destination_queue_service
from pollicino.net.rapid_deadline_utility import (
    RapidReplicaEstimate,
    rapid_deadline_marginal_utility,
)


OBJECT_BYTES = 64
DEADLINE_REMAINING_S = 120.0
CANDIDATE_MEAN_S = 60.0


def _candidate() -> RapidReplicaEstimate:
    return RapidReplicaEstimate(
        carrier_id="c",
        mean_direct_meeting_seconds=CANDIDATE_MEAN_S,
        meetings_needed=1,
    )


def test_queue_service_and_replica_count_cannot_distinguish_equal_objects() -> None:
    # The current source/candidate service situation is intentionally identical
    # for both objects. Each object also has exactly one existing complete replica.
    candidate_service_x = estimate_destination_queue_service(
        mean_interval_seconds=CANDIDATE_MEAN_S,
        mean_opportunity_bytes=OBJECT_BYTES,
        bytes_ahead=0,
        object_bytes=OBJECT_BYTES,
    )
    candidate_service_y = estimate_destination_queue_service(
        mean_interval_seconds=CANDIDATE_MEAN_S,
        mean_opportunity_bytes=OBJECT_BYTES,
        bytes_ahead=0,
        object_bytes=OBJECT_BYTES,
    )

    assert candidate_service_x == candidate_service_y
    assert candidate_service_x.service_seconds == 60.0
    assert 1 == 1  # one existing replica for each object; count alone ties


def test_existing_replica_quality_changes_marginal_value_of_same_candidate() -> None:
    # Object X already has one very strong replica: B reaches D every ~20 s.
    x_existing = RapidReplicaEstimate(
        carrier_id="b-fast",
        mean_direct_meeting_seconds=20.0,
        meetings_needed=1,
    )
    # Object Y also has one replica, but its carrier reaches D only every ~200 s.
    y_existing = RapidReplicaEstimate(
        carrier_id="b-slow",
        mean_direct_meeting_seconds=200.0,
        meetings_needed=1,
    )

    x = rapid_deadline_marginal_utility(
        remaining_useful_seconds=DEADLINE_REMAINING_S,
        existing_replicas=(x_existing,),
        candidate_replica=_candidate(),
        transfer_bytes=OBJECT_BYTES,
    )
    y = rapid_deadline_marginal_utility(
        remaining_useful_seconds=DEADLINE_REMAINING_S,
        existing_replicas=(y_existing,),
        candidate_replica=_candidate(),
        transfer_bytes=OBJECT_BYTES,
    )

    assert x.probability_before > y.probability_before
    assert x.marginal_utility > 0
    assert y.marginal_utility > 0
    assert y.marginal_utility > x.marginal_utility
    assert y.marginal_utility_per_byte > x.marginal_utility_per_byte


def test_replica_quality_is_only_discriminator_in_gate() -> None:
    # Both decisions intentionally share object size, candidate, deadline,
    # candidate queue state and existing replica count. Only the delivery quality
    # of the already-existing replica differs.
    assert OBJECT_BYTES == 64
    assert DEADLINE_REMAINING_S == 120.0
    assert CANDIDATE_MEAN_S == 60.0

    fast = RapidReplicaEstimate("fast", 20.0, 1)
    slow = RapidReplicaEstimate("slow", 200.0, 1)
    assert fast.meetings_needed == slow.meetings_needed == 1
    assert fast.mean_direct_meeting_seconds < slow.mean_direct_meeting_seconds
