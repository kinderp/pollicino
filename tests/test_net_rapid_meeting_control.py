import pytest

from pollicino.net.rapid_meeting_control import (
    RapidMeetingControlState,
    exchange_rapid_meeting_metadata,
)


def _observe_pair(
    left: RapidMeetingControlState,
    right: RapidMeetingControlState,
    *times: int,
) -> None:
    for now_s in times:
        left.observe_direct_encounter(right.node_id, now_s=now_s)
        right.observe_direct_encounter(left.node_id, now_s=now_s)


def test_direct_intermeeting_mean_uses_observed_history() -> None:
    a = RapidMeetingControlState("a")
    b = RapidMeetingControlState("b")

    _observe_pair(a, b, 0, 100, 220)
    edge = a.edge("a", "b")

    assert edge is not None
    assert edge.sample_count == 2
    assert edge.mean_intermeeting_seconds == pytest.approx(110.0)
    assert edge.observed_at_s == 220


def test_metadata_exchange_enables_three_hop_local_estimate() -> None:
    a = RapidMeetingControlState("a")
    b = RapidMeetingControlState("b")
    c = RapidMeetingControlState("c")
    d = RapidMeetingControlState("d")

    _observe_pair(a, b, 0, 100)  # mean 100
    _observe_pair(b, c, 0, 60)   # mean 60
    _observe_pair(c, d, 0, 40)   # mean 40

    # Propagate C-D to B, then B's knowledge to A.
    exchange_rapid_meeting_metadata(b, c)
    report = exchange_rapid_meeting_metadata(a, b)

    assert report.total_sent_entry_count > 0
    assert a.expected_meeting_seconds("a", "d", max_hops=2) is None
    assert a.expected_meeting_seconds("a", "d", max_hops=3) == pytest.approx(200.0)


def test_delta_exchange_does_not_echo_unchanged_metadata() -> None:
    a = RapidMeetingControlState("a")
    b = RapidMeetingControlState("b")
    d = RapidMeetingControlState("d")

    _observe_pair(a, b, 0, 100)
    _observe_pair(b, d, 0, 50)

    first = exchange_rapid_meeting_metadata(a, b)
    second = exchange_rapid_meeting_metadata(a, b)

    # Bootstrap has no previous metadata watermark: A sends A-B while B sends
    # both its A-B estimate and B-D estimate. The shared A-B entry is a real
    # initial control duplication in this model, not silently optimized away.
    assert first.total_sent_entry_count == 3
    assert second.total_sent_entry_count == 0

    _observe_pair(b, d, 100)  # new B-D estimate generation
    third = exchange_rapid_meeting_metadata(a, b)
    assert third.left_sent_entry_count == 0
    assert third.right_sent_entry_count == 1
    assert third.left_learned_entry_count == 1

    fourth = exchange_rapid_meeting_metadata(a, b)
    assert fourth.total_sent_entry_count == 0


def test_newer_meeting_estimate_wins_over_stale_gossip() -> None:
    a = RapidMeetingControlState("a")
    b = RapidMeetingControlState("b")

    # A has a newer two-sample estimate; B knows only the older first interval.
    a.observe_direct_encounter("b", now_s=0)
    a.observe_direct_encounter("b", now_s=100)
    b.observe_direct_encounter("a", now_s=0)
    b.observe_direct_encounter("a", now_s=100)
    a.observe_direct_encounter("b", now_s=220)

    before = a.edge("a", "b")
    assert before is not None and before.observed_at_s == 220

    exchange_rapid_meeting_metadata(a, b)
    after = a.edge("a", "b")
    b_after = b.edge("a", "b")

    assert after == before
    assert b_after == before


def test_unknown_path_and_validation_fail_closed() -> None:
    a = RapidMeetingControlState("a")
    b = RapidMeetingControlState("b")

    assert a.expected_meeting_seconds("a", "d") is None
    assert a.expected_meeting_seconds("a", "a") == 0.0

    with pytest.raises(ValueError, match="increase"):
        a.observe_direct_encounter("b", now_s=10)
        a.observe_direct_encounter("b", now_s=10)
    with pytest.raises(ValueError, match="positive integer"):
        a.expected_meeting_seconds("a", "b", max_hops=0)
    with pytest.raises(ValueError, match="distinct"):
        exchange_rapid_meeting_metadata(a, a)
