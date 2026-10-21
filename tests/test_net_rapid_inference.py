import hashlib

import pytest

from pollicino.net.rapid_inference import infer_rapid_deadline_replication
from pollicino.net.rapid_meeting_control import (
    RapidMeetingControlState,
    exchange_rapid_meeting_metadata,
)
from pollicino.net.rapid_replica_control import (
    RapidReplicaControlState,
    exchange_rapid_replica_metadata,
)


def _bundle(label: str) -> bytes:
    return hashlib.sha256(label.encode()).digest()


def _observe_pair(
    left: RapidMeetingControlState,
    right: RapidMeetingControlState,
    *times: int,
) -> None:
    for now_s in times:
        left.observe_direct_encounter(right.node_id, now_s=now_s)
        right.observe_direct_encounter(left.node_id, now_s=now_s)


def _meeting_knowledge() -> RapidMeetingControlState:
    a = RapidMeetingControlState("a")
    b = RapidMeetingControlState("b")
    d_for_a = RapidMeetingControlState("d")
    d_for_b = RapidMeetingControlState("d-b-shadow")

    # A has a direct observed mean meeting time of 100 s to D.
    _observe_pair(a, d_for_a, 0, 100)

    # B's control state learns an edge named B-D with 40 s mean. Use a
    # destination state with the canonical real destination ID for that edge.
    b_destination = RapidMeetingControlState("d")
    _observe_pair(b, b_destination, 0, 40)

    # Gossip B's B-D edge into A's local knowledge. No oracle topology is used.
    exchange_rapid_meeting_metadata(a, b)
    return a


def _simple_meeting_knowledge() -> RapidMeetingControlState:
    a = RapidMeetingControlState("a")
    d = RapidMeetingControlState("d")
    _observe_pair(a, d, 0, 100)
    b = RapidMeetingControlState("b")
    d2 = RapidMeetingControlState("d")
    _observe_pair(b, d2, 0, 40)
    exchange_rapid_meeting_metadata(a, b)
    return a


def test_complete_local_knowledge_produces_positive_candidate_utility() -> None:
    bundle_id = _bundle("complete")
    meeting = _simple_meeting_knowledge()
    replicas = RapidReplicaControlState("a")
    replicas.advertise_local_replica(bundle_id, present=True, now_s=100)

    before_meeting_edges = meeting.edges
    before_replica_state = replicas.replica_advertisements
    report = infer_rapid_deadline_replication(
        bundle_id=bundle_id,
        destination_id="d",
        candidate_id="b",
        now_s=100,
        application_deadline_s=160,
        transfer_bytes=64,
        meeting_state=meeting,
        replica_state=replicas,
        meetings_needed_by_carrier={"a": 1, "b": 1},
    )

    assert report.known_replica_carriers == ("a",)
    assert report.knowledge_complete
    assert report.usable_for_replication_ranking
    assert report.utility is not None
    assert report.utility.marginal_utility > 0
    assert report.candidate_replica_estimate is not None
    assert report.candidate_replica_estimate.mean_direct_meeting_seconds == 40
    assert report.existing_replica_estimates[0].mean_direct_meeting_seconds == 100
    assert meeting.edges == before_meeting_edges
    assert replicas.replica_advertisements == before_replica_state


def test_known_replica_with_missing_inference_data_blocks_optimistic_utility() -> None:
    bundle_id = _bundle("missing")
    meeting = _simple_meeting_knowledge()
    replicas = RapidReplicaControlState("a")
    replicas.advertise_local_replica(bundle_id, present=True, now_s=100)
    c = RapidReplicaControlState("c")
    c.advertise_local_replica(bundle_id, present=True, now_s=100)
    exchange_rapid_replica_metadata(c, replicas)

    report = infer_rapid_deadline_replication(
        bundle_id=bundle_id,
        destination_id="d",
        candidate_id="b",
        now_s=100,
        application_deadline_s=160,
        transfer_bytes=64,
        meeting_state=meeting,
        replica_state=replicas,
        meetings_needed_by_carrier={"a": 1, "b": 1},
    )

    assert report.known_replica_carriers == ("a", "c")
    assert "c" in report.missing_meeting_carriers
    assert "c" in report.missing_queue_carriers
    assert not report.knowledge_complete
    assert report.utility is None
    assert not report.usable_for_replication_ranking


def test_final_delivery_ack_forces_zero_marginal_utility_without_other_estimates() -> None:
    bundle_id = _bundle("delivered")
    meeting = RapidMeetingControlState("a")
    replicas = RapidReplicaControlState("a")
    destination = RapidReplicaControlState("d")
    destination.acknowledge_local_delivery(bundle_id, delivered_at_s=120)
    exchange_rapid_replica_metadata(destination, replicas)

    report = infer_rapid_deadline_replication(
        bundle_id=bundle_id,
        destination_id="d",
        candidate_id="b",
        now_s=130,
        application_deadline_s=200,
        transfer_bytes=64,
        meeting_state=meeting,
        replica_state=replicas,
        meetings_needed_by_carrier={},
    )

    assert report.delivered_already
    assert report.utility is not None
    assert report.utility.probability_before == 1.0
    assert report.utility.probability_after == 1.0
    assert report.utility.marginal_utility == 0.0
    assert not report.usable_for_replication_ranking


def test_candidate_that_already_has_complete_replica_is_not_rankable() -> None:
    bundle_id = _bundle("candidate-has")
    meeting = _simple_meeting_knowledge()
    a = RapidReplicaControlState("a")
    b = RapidReplicaControlState("b")
    a.advertise_local_replica(bundle_id, present=True, now_s=100)
    b.advertise_local_replica(bundle_id, present=True, now_s=100)
    exchange_rapid_replica_metadata(a, b)

    report = infer_rapid_deadline_replication(
        bundle_id=bundle_id,
        destination_id="d",
        candidate_id="b",
        now_s=100,
        application_deadline_s=200,
        transfer_bytes=64,
        meeting_state=meeting,
        replica_state=a,
        meetings_needed_by_carrier={"a": 1, "b": 1},
    )

    assert report.candidate_already_has_replica
    assert report.utility is None
    assert not report.usable_for_replication_ranking


def test_passed_deadline_returns_zero_utility_without_inventing_missing_knowledge() -> None:
    bundle_id = _bundle("late")
    report = infer_rapid_deadline_replication(
        bundle_id=bundle_id,
        destination_id="d",
        candidate_id="b",
        now_s=200,
        application_deadline_s=200,
        transfer_bytes=64,
        meeting_state=RapidMeetingControlState("a"),
        replica_state=RapidReplicaControlState("a"),
        meetings_needed_by_carrier={},
    )

    assert report.deadline_passed
    assert report.utility is not None
    assert report.utility.marginal_utility == 0
    assert not report.usable_for_replication_ranking


def test_inference_validation_fails_closed() -> None:
    with pytest.raises(ValueError, match="32 bytes"):
        infer_rapid_deadline_replication(
            bundle_id=b"short",
            destination_id="d",
            candidate_id="b",
            now_s=0,
            application_deadline_s=1,
            transfer_bytes=1,
            meeting_state=RapidMeetingControlState("a"),
            replica_state=RapidReplicaControlState("a"),
            meetings_needed_by_carrier={},
        )

    bundle_id = _bundle("validation")
    with pytest.raises(ValueError, match="positive integer"):
        infer_rapid_deadline_replication(
            bundle_id=bundle_id,
            destination_id="d",
            candidate_id="b",
            now_s=0,
            application_deadline_s=1,
            transfer_bytes=0,
            meeting_state=RapidMeetingControlState("a"),
            replica_state=RapidReplicaControlState("a"),
            meetings_needed_by_carrier={},
        )
