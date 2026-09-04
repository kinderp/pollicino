from __future__ import annotations

import pytest

from pollicino.net.bearer import ImpairmentAction, ScriptedImpairmentPlan
from pollicino.net.endpoint import (
    B2ContactBudget,
    B2ContactOutcome,
    ScriptedEncodedMessageLink,
    run_independent_contact,
)
from px10_support import memory_endpoint, query


def _query_pair():
    left = memory_endpoint("left")
    right = memory_endpoint("right")
    left.query_results.add_query(query(1))
    return left, right


def test_metadata_loss_is_safe_and_fresh_contact_recovers() -> None:
    left, right = _query_pair()
    lost = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(
                left_to_right=(ImpairmentAction.DROP,),
            )
        ),
    )
    assert lost.outcome is B2ContactOutcome.PARTIAL_NOT_DELIVERED
    assert lost.drops == 1
    assert right.query_results.query_count == 0
    recovered = run_independent_contact(
        left.endpoint, right.endpoint, bearer=ScriptedEncodedMessageLink()
    )
    assert recovered.durable_commits == 1


def test_request_loss_is_safe_and_fresh_contact_recovers() -> None:
    left, right = _query_pair()
    lost = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(
                right_to_left=(ImpairmentAction.DROP,),
            )
        ),
    )
    assert lost.outcome is B2ContactOutcome.PARTIAL_NOT_DELIVERED
    assert lost.record_messages_sent == 0
    assert right.query_results.query_count == 0
    assert run_independent_contact(
        left.endpoint, right.endpoint, bearer=ScriptedEncodedMessageLink()
    ).durable_commits == 1


def test_record_loss_is_safe_and_fresh_contact_recovers() -> None:
    left, right = _query_pair()
    lost = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(
                left_to_right=(ImpairmentAction.DELIVER, ImpairmentAction.DROP),
            )
        ),
    )
    assert lost.outcome is B2ContactOutcome.PARTIAL_NOT_DELIVERED
    assert lost.record_messages_sent == lost.drops == 1
    assert right.query_results.query_count == 0
    recovered = run_independent_contact(
        left.endpoint, right.endpoint, bearer=ScriptedEncodedMessageLink()
    )
    assert recovered.durable_commits == 1


def test_duplicate_metadata_and_request_are_safe() -> None:
    left, right = _query_pair()
    metadata_duplicate = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(
                left_to_right=(ImpairmentAction.DUPLICATE,),
            )
        ),
    )
    assert metadata_duplicate.duplicate_presentations == 1
    assert right.query_results.query_count == 1
    assert metadata_duplicate.durable_commits == 1

    another_left, another_right = _query_pair()
    request_duplicate = run_independent_contact(
        another_left.endpoint,
        another_right.endpoint,
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(
                right_to_left=(ImpairmentAction.DUPLICATE,),
            )
        ),
    )
    assert request_duplicate.duplicate_presentations == 1
    assert another_right.query_results.query_count == 1
    assert request_duplicate.durable_commits == 1


def test_duplicate_record_is_native_idempotent() -> None:
    left, right = _query_pair()
    report = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(
                left_to_right=(ImpairmentAction.DELIVER, ImpairmentAction.DUPLICATE),
            )
        ),
    )
    assert report.duplicate_presentations == 1
    assert report.durable_commits == 1
    assert right.query_results.query_count == 1


def test_disconnect_after_complete_commit_preserves_partial_state() -> None:
    left, right = _query_pair()
    left.query_results.add_query(query(2))
    report = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(
                left_to_right=(
                    ImpairmentAction.DELIVER,
                    ImpairmentAction.DELIVER,
                    ImpairmentAction.DISCONNECT,
                )
            )
        ),
    )
    assert report.outcome is B2ContactOutcome.DISCONNECTED
    assert report.durable_commits == 1
    assert right.query_results.query_count == 1
    resumed = run_independent_contact(
        left.endpoint, right.endpoint, bearer=ScriptedEncodedMessageLink()
    )
    assert resumed.durable_commits == 1
    assert right.query_results.query_count == 2


def test_permanent_metadata_and_record_loss_are_bounded_not_converged() -> None:
    for record_loss in (False, True):
        left, right = _query_pair()
        left_actions = (
            (ImpairmentAction.DELIVER, ImpairmentAction.DROP)
            if record_loss
            else (ImpairmentAction.DROP,)
        )
        for _ in range(3):
            report = run_independent_contact(
                left.endpoint,
                right.endpoint,
                bearer=ScriptedEncodedMessageLink(
                    ScriptedImpairmentPlan(
                        left_to_right=left_actions,
                        default_left_to_right=ImpairmentAction.DROP,
                    )
                ),
            )
            assert report.outcome is B2ContactOutcome.PARTIAL_NOT_DELIVERED
            assert report.bearer_attempts <= 3
            assert right.query_results.query_count == 0


def test_directional_asymmetry_can_block_one_flow_without_corruption() -> None:
    left = memory_endpoint("left")
    right = memory_endpoint("right")
    left.query_results.add_query(query(1))
    right.query_results.add_query(query(2))
    report = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(
                left_to_right=(ImpairmentAction.DROP, ImpairmentAction.DELIVER),
                default_left_to_right=ImpairmentAction.DELIVER,
            )
        ),
    )
    assert report.outcome is B2ContactOutcome.PARTIAL_NOT_DELIVERED
    assert query(1).query_id not in right.query_results.sorted_query_ids()
    assert left.query_results.get_query(query(2).query_id) == query(2)


def test_total_bearer_budget_counts_control_and_prevents_hidden_chatter() -> None:
    left, right = _query_pair()
    report = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(),
        budget=B2ContactBudget(max_bearer_attempts=2, max_trace_entries=2),
    )
    assert report.outcome is B2ContactOutcome.BUDGET_EXHAUSTED
    assert report.control_messages_sent == report.bearer_attempts == 2
    assert report.record_messages_sent == 0
    assert right.query_results.query_count == 0


def test_control_and_record_budgets_are_independently_enforced() -> None:
    left, right = _query_pair()
    control_limited = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(),
        budget=B2ContactBudget(max_control_messages=1),
    )
    assert control_limited.outcome is B2ContactOutcome.BUDGET_EXHAUSTED
    assert control_limited.control_messages_sent == 1
    assert control_limited.record_messages_sent == 0
    assert right.query_results.query_count == 0

    record_limited = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(),
        budget=B2ContactBudget(max_record_bytes=1),
    )
    assert record_limited.outcome is B2ContactOutcome.BUDGET_EXHAUSTED
    assert record_limited.control_messages_sent == 2
    assert record_limited.record_messages_sent == 0
    assert right.query_results.query_count == 0


@pytest.mark.parametrize("field", ("max_control_messages", "max_record_messages", "max_bearer_attempts", "max_trace_entries"))
def test_zero_budget_dimension_is_rejected(field: str) -> None:
    values = {field: 0}
    with pytest.raises(ValueError):
        B2ContactBudget(**values)
