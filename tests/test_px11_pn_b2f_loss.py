from __future__ import annotations

import pytest

from pollicino.net.bearer import ImpairmentAction, LinkDirection, ScriptedImpairmentPlan
from pollicino.net.endpoint import (
    B2ContactBudget,
    B2ContactOutcome,
    EncodedBearerAttemptResult,
    ScriptedEncodedMessageLink,
)
from pollicino.net.fair_reconciliation import FairIndependentEndpoint, run_fair_contact
from px10_support import query
from px11_support import fair_memory_endpoint


def _endpoint(fixture, label: str) -> FairIndependentEndpoint:
    return FairIndependentEndpoint(fixture.catalog, fixture.query_results, label)


def _contact(sender, receiver, plan=ScriptedImpairmentPlan()):
    return run_fair_contact(
        _endpoint(sender, "sender"),
        _endpoint(receiver, "receiver"),
        bearer=ScriptedEncodedMessageLink(plan),
    )


@pytest.mark.parametrize(
    "plan",
    (
        ScriptedImpairmentPlan(left_to_right=(ImpairmentAction.DROP,)),
        ScriptedImpairmentPlan(right_to_left=(ImpairmentAction.DROP,)),
        ScriptedImpairmentPlan(
            right_to_left=(
                ImpairmentAction.DELIVER,
                ImpairmentAction.DROP,
            )
        ),
        ScriptedImpairmentPlan(
            left_to_right=(
                ImpairmentAction.DELIVER,
                ImpairmentAction.DROP,
            )
        ),
        ScriptedImpairmentPlan(
            left_to_right=(
                ImpairmentAction.DELIVER,
                ImpairmentAction.DELIVER,
                ImpairmentAction.DROP,
            )
        ),
    ),
)
def test_metadata_request_advertisement_or_record_loss_is_safe_and_recoverable(
    plan: ScriptedImpairmentPlan,
) -> None:
    sender = fair_memory_endpoint("sender")
    receiver = fair_memory_endpoint("receiver")
    sender.query_results.add_query(query(1))
    first = _contact(sender, receiver, plan)
    assert first.outcome is B2ContactOutcome.PARTIAL_NOT_DELIVERED
    assert receiver.query_results.query_count == 0
    second = _contact(sender, receiver)
    assert second.durable_commits == 1
    assert receiver.query_results.get_query(query(1).query_id) == query(1)


def test_duplicate_and_delayed_record_remain_idempotent() -> None:
    for action, duplicates, delays in (
        (ImpairmentAction.DUPLICATE, 1, 0),
        (ImpairmentAction.DELAY_DELIVER, 0, 1),
    ):
        sender = fair_memory_endpoint("sender")
        receiver = fair_memory_endpoint("receiver")
        sender.query_results.add_query(query(1))
        report = _contact(
            sender,
            receiver,
            ScriptedImpairmentPlan(
                left_to_right=(
                    ImpairmentAction.DELIVER,
                    ImpairmentAction.DELIVER,
                    action,
                )
            ),
        )
        assert receiver.query_results.query_count == 1
        assert report.durable_commits == 1
        assert report.duplicate_presentations == duplicates
        assert report.delayed_units == delays


def test_duplicate_directory_metadata_is_safe() -> None:
    sender = fair_memory_endpoint("sender")
    receiver = fair_memory_endpoint("receiver")
    sender.query_results.add_query(query(1))
    report = _contact(
        sender,
        receiver,
        ScriptedImpairmentPlan(left_to_right=(ImpairmentAction.DUPLICATE,)),
    )
    assert receiver.query_results.query_count == 1
    assert report.durable_commits == 1
    assert report.duplicate_presentations >= 1


def test_sender_uncertainty_commit_is_not_retransferred_as_missing() -> None:
    sender = fair_memory_endpoint("sender")
    receiver = fair_memory_endpoint("receiver")
    sender.query_results.add_query(query(1))
    uncertain = _contact(
        sender,
        receiver,
        ScriptedImpairmentPlan(
            left_to_right=(
                ImpairmentAction.DELIVER,
                ImpairmentAction.DELIVER,
                ImpairmentAction.DELIVER_UNCERTAIN,
            )
        ),
    )
    assert uncertain.outcome is B2ContactOutcome.SENDER_UNCERTAIN
    assert uncertain.durable_commits == 1
    assert receiver.query_results.query_count == 1

    fresh = _contact(sender, receiver)
    assert fresh.record_messages_sent == 0
    assert fresh.durable_commits == 0
    assert fresh.pages_repeated == 2


def test_disconnect_after_complete_control_work_returns_finitely_and_recontacts() -> None:
    sender = fair_memory_endpoint("sender")
    receiver = fair_memory_endpoint("receiver")
    sender.query_results.add_queries(query(index) for index in range(20))
    interrupted = _contact(
        sender,
        receiver,
        ScriptedImpairmentPlan(
            left_to_right=(
                ImpairmentAction.DELIVER,
                ImpairmentAction.DELIVER,
                ImpairmentAction.DISCONNECT,
            )
        ),
    )
    assert interrupted.outcome is B2ContactOutcome.DISCONNECTED
    assert interrupted.bearer_attempts == 5
    assert receiver.query_results.query_count == 0
    recovered = _contact(sender, receiver)
    assert recovered.durable_commits == 20


def test_directional_asymmetry_does_not_corrupt_and_other_lane_progresses() -> None:
    left = fair_memory_endpoint("left")
    right = fair_memory_endpoint("right")
    left.query_results.add_query(query(1))
    right.query_results.add_query(query(2))
    report = run_fair_contact(
        _endpoint(left, "left"),
        _endpoint(right, "right"),
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(left_to_right=(ImpairmentAction.DROP,))
        ),
    )
    assert report.drops == 1
    assert left.query_results.query_count == 2
    assert right.query_results.query_count == 1
    assert report.progress_right_to_left == 1


def test_permanent_loss_returns_control_without_false_progress() -> None:
    sender = fair_memory_endpoint("sender")
    receiver = fair_memory_endpoint("receiver")
    sender.query_results.add_queries(query(index) for index in range(1_000))
    report = run_fair_contact(
        _endpoint(sender, "sender"),
        _endpoint(receiver, "receiver"),
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(
                default_left_to_right=ImpairmentAction.DROP,
                default_right_to_left=ImpairmentAction.DROP,
            )
        ),
        budget=B2ContactBudget(max_bearer_attempts=10),
    )
    assert report.outcome is B2ContactOutcome.PARTIAL_NOT_DELIVERED
    assert report.bearer_attempts <= 10
    assert report.durable_commits == 0
    assert receiver.query_results.query_count == 0


def test_large_multipage_loss_then_deliverable_contacts_have_no_starvation() -> None:
    sender = fair_memory_endpoint("sender")
    receiver = fair_memory_endpoint("receiver")
    sender.query_results.add_queries(query(index) for index in range(1_000))
    first = _contact(
        sender,
        receiver,
        ScriptedImpairmentPlan(
            left_to_right=(
                ImpairmentAction.DELIVER,
                ImpairmentAction.DELIVER,
                ImpairmentAction.DROP,
            )
        ),
    )
    assert first.drops == 1
    contacts = 1
    while receiver.query_results.query_count < 1_000:
        assert contacts < 20
        _contact(sender, receiver)
        contacts += 1
    assert receiver.query_results.canonical_state() == sender.query_results.canonical_state()


class _CorruptFirstBearer:
    def __init__(self) -> None:
        self.used = False

    def attempt(self, direction: LinkDirection, encoded: bytes):
        if not self.used:
            self.used = True
            damaged = bytearray(encoded)
            damaged[-1] ^= 1
            return EncodedBearerAttemptResult(
                ImpairmentAction.DELIVER, (bytes(damaged),), True
            )
        return EncodedBearerAttemptResult(ImpairmentAction.DELIVER, (encoded,), True)


def test_corrupt_metadata_fails_closed_without_receiver_mutation() -> None:
    sender = fair_memory_endpoint("sender")
    receiver = fair_memory_endpoint("receiver")
    sender.query_results.add_query(query(1))
    report = run_fair_contact(
        _endpoint(sender, "sender"),
        _endpoint(receiver, "receiver"),
        bearer=_CorruptFirstBearer(),
    )
    assert report.outcome is B2ContactOutcome.ERROR
    assert report.error_code == "B2_DECODE_ERROR"
    assert receiver.query_results.query_count == 0


def test_conflicting_page_reaches_native_fail_closed_rule() -> None:
    sender = fair_memory_endpoint("sender")
    receiver = fair_memory_endpoint("receiver")
    sender.query_results.add_query(query(1, b"value-a"))
    receiver.query_results.add_query(query(1, b"value-b"))
    before = receiver.query_results.canonical_state()
    report = _contact(sender, receiver)
    assert report.outcome is B2ContactOutcome.ERROR
    assert report.error_code == "QUERY_CONFLICT"
    assert receiver.query_results.canonical_state() == before
