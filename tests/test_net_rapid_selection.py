import hashlib

import pytest

from pollicino.net.rapid_deadline_utility import RapidDeadlineUtility
from pollicino.net.rapid_inference import RapidDeadlineInferenceReport
from pollicino.net.rapid_selection import select_rapid_deadline_candidate


def _bundle(label: str) -> bytes:
    return hashlib.sha256(label.encode()).digest()


def _inference(
    label: str,
    *,
    deadline: int,
    transfer_bytes: int,
    marginal: float,
    candidate_id: str = "b",
    destination_id: str = "d",
    now_s: int = 100,
    missing_meeting: tuple[str, ...] = (),
    missing_queue: tuple[str, ...] = (),
    delivered: bool = False,
    candidate_has: bool = False,
    deadline_passed: bool = False,
) -> RapidDeadlineInferenceReport:
    # Use zero as the synthetic baseline so tests that intentionally construct
    # equal marginal-utility/byte ratios are not perturbed by unrelated float
    # subtraction error from a non-zero probability_before value.
    before = 0.0
    after = marginal
    return RapidDeadlineInferenceReport(
        bundle_id=_bundle(label),
        destination_id=destination_id,
        candidate_id=candidate_id,
        now_s=now_s,
        application_deadline_s=deadline,
        transfer_bytes=transfer_bytes,
        known_replica_carriers=("a",),
        existing_replica_estimates=(),
        candidate_replica_estimate=None,
        missing_meeting_carriers=missing_meeting,
        missing_queue_carriers=missing_queue,
        delivered_already=delivered,
        candidate_already_has_replica=candidate_has,
        deadline_passed=deadline_passed,
        utility=RapidDeadlineUtility(
            remaining_useful_seconds=max(0, deadline - now_s),
            transfer_bytes=transfer_bytes,
            probability_before=before,
            probability_after=after,
        ),
    )


def test_selection_uses_marginal_utility_per_byte_not_raw_utility() -> None:
    high_raw = _inference(
        "high-raw",
        deadline=200,
        transfer_bytes=100,
        marginal=0.4,
    )
    efficient = _inference(
        "efficient",
        deadline=200,
        transfer_bytes=50,
        marginal=0.3,
    )

    decision = select_rapid_deadline_candidate((high_raw, efficient))

    assert decision.selected_bundle_id == efficient.bundle_id
    assert decision.ranked_items[0].marginal_utility == pytest.approx(0.3)
    assert decision.ranked_items[0].marginal_utility_per_byte == pytest.approx(0.006)
    assert decision.ranked_items[1].marginal_utility_per_byte == pytest.approx(0.004)


def test_equal_score_prefers_earlier_deadline_then_smaller_transfer() -> None:
    late = _inference("late", deadline=220, transfer_bytes=100, marginal=0.4)
    early_large = _inference(
        "early-large", deadline=180, transfer_bytes=100, marginal=0.4
    )
    early_small = _inference(
        "early-small", deadline=180, transfer_bytes=50, marginal=0.2
    )

    decision = select_rapid_deadline_candidate((late, early_large, early_small))

    assert decision.ranked_items[0].bundle_id == early_small.bundle_id
    assert decision.ranked_items[1].bundle_id == early_large.bundle_id
    assert decision.ranked_items[2].bundle_id == late.bundle_id


def test_incomplete_or_nonbeneficial_reports_are_not_ranked() -> None:
    incomplete = _inference(
        "incomplete",
        deadline=200,
        transfer_bytes=50,
        marginal=0.4,
        missing_queue=("a",),
    )
    zero = _inference("zero", deadline=200, transfer_bytes=50, marginal=0.0)
    delivered = _inference(
        "delivered",
        deadline=200,
        transfer_bytes=50,
        marginal=0.4,
        delivered=True,
    )
    already_has = _inference(
        "already",
        deadline=200,
        transfer_bytes=50,
        marginal=0.4,
        candidate_has=True,
    )
    passed = _inference(
        "passed",
        deadline=100,
        transfer_bytes=50,
        marginal=0.0,
        deadline_passed=True,
    )

    decision = select_rapid_deadline_candidate(
        (incomplete, zero, delivered, already_has, passed)
    )

    assert decision.selected is None
    assert decision.ranked_items == ()


def test_selection_requires_one_consistent_encounter_context() -> None:
    first = _inference("one", deadline=200, transfer_bytes=50, marginal=0.1)
    other_peer = _inference(
        "two",
        deadline=200,
        transfer_bytes=50,
        marginal=0.1,
        candidate_id="c",
    )
    with pytest.raises(ValueError, match="same candidate"):
        select_rapid_deadline_candidate((first, other_peer))

    duplicate = RapidDeadlineInferenceReport(
        **{
            field: getattr(first, field)
            for field in first.__dataclass_fields__
        }
    )
    with pytest.raises(ValueError, match="unique bundle"):
        select_rapid_deadline_candidate((first, duplicate))


def test_selection_requires_nonempty_typed_inputs() -> None:
    with pytest.raises(ValueError, match="at least one"):
        select_rapid_deadline_candidate(())
    with pytest.raises(TypeError, match="RapidDeadlineInferenceReport"):
        select_rapid_deadline_candidate((object(),))  # type: ignore[arg-type]
