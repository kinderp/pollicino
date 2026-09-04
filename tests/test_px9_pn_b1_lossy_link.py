from __future__ import annotations

import pytest

from pollicino.net.bearer import (
    BearerBudget,
    BearerContactOutcome,
    ImpairmentAction,
    ScriptedImpairmentPlan,
    ScriptedInMemoryLink,
    run_bearer_contact,
)
from pollicino.net.catalog import BoundedReference
from pollicino.net.contact import MAX_CONTACT_BYTES, ContactBudget, ContactSelection
from pollicino.net.query import QueryRecord, ResultRecord
from px9_support import full_budget, memory_node, query, reference, result


def test_query_loss_before_apply_leaves_receiver_unchanged_then_recontact_delivers() -> None:
    sender, receiver = memory_node("sender"), memory_node("receiver")
    sender.query_results.add_query(query(1))
    before = receiver.query_results.canonical_state()
    lost = run_bearer_contact(
        sender,
        receiver,
        bearer=ScriptedInMemoryLink(
            ScriptedImpairmentPlan(default_left_to_right=ImpairmentAction.DROP)
        ),
        contact_budget=full_budget(),
    )
    assert lost.outcome is BearerContactOutcome.PARTIAL_NOT_DELIVERED
    assert lost.dropped_units == lost.bearer_attempts == 1
    assert lost.durable_records_committed == 0
    assert receiver.query_results.canonical_state() == before
    assert lost.remaining_missing_work == 1

    delivered = run_bearer_contact(
        sender,
        receiver,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
    )
    assert delivered.durable_records_committed == 1
    assert receiver.query_results.get_query(query(1).query_id) == query(1)


def test_loss_after_prior_commits_preserves_them_and_retries_only_missing() -> None:
    sender, receiver = memory_node("sender"), memory_node("receiver")
    sender.query_results.add_queries(query(index) for index in range(3))
    first = run_bearer_contact(
        sender,
        receiver,
        bearer=ScriptedInMemoryLink(
            ScriptedImpairmentPlan(
                left_to_right=(
                    ImpairmentAction.DELIVER,
                    ImpairmentAction.DELIVER,
                    ImpairmentAction.DROP,
                )
            )
        ),
        contact_budget=full_budget(),
    )
    assert first.durable_records_committed == 2
    assert first.dropped_units == 1
    assert receiver.query_results.query_count == 2
    second = run_bearer_contact(
        sender,
        receiver,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
    )
    assert second.bearer_attempts == second.durable_records_committed == 1
    # PX8 snapshots both directions at contact entry. Each of the two durable
    # records is therefore considered as known in both directions, but neither
    # causes a bearer attempt.
    assert second.records_skipped_already_known == 4
    assert receiver.query_results.canonical_state() == sender.query_results.canonical_state()


@pytest.mark.parametrize("kind", ("query", "result", "reference"))
def test_duplicate_complete_delivery_is_idempotent(kind: str) -> None:
    sender, receiver = memory_node("sender"), memory_node("receiver")
    selection = ContactSelection()
    if kind == "query":
        record = query(1)
        sender.query_results.add_query(record)
    elif kind == "result":
        record = result(1, 1)
        sender.query_results.add_result(record)
    else:
        record = reference(1)
        sender.catalog.add(record)
        selection = ContactSelection(right_wants_from_left=(record.logical_key,))
    report = run_bearer_contact(
        sender,
        receiver,
        bearer=ScriptedInMemoryLink(
            ScriptedImpairmentPlan(left_to_right=(ImpairmentAction.DUPLICATE,))
        ),
        contact_budget=full_budget(),
        selection=selection,
    )
    assert report.outcome is BearerContactOutcome.NO_MORE_ELIGIBLE_WORK
    assert report.bearer_attempts == report.durable_records_committed == 1
    assert report.delivered_presentations == 2
    assert report.duplicate_presentations == 1
    if kind == "query":
        assert receiver.query_results.query_count == 1
    elif kind == "result":
        assert receiver.query_results.result_count == 1
    else:
        assert len(receiver.catalog) == 1


@pytest.mark.parametrize(
    ("kind", "error_code"),
    (
        ("query", "QUERY_CONFLICT"),
        ("result", "RESULT_CONFLICT"),
        ("reference", "REFERENCE_CONFLICT"),
    ),
)
def test_conflicting_known_identity_fails_closed(kind: str, error_code: str) -> None:
    sender, receiver = memory_node("sender"), memory_node("receiver")
    selection = ContactSelection()
    if kind == "query":
        sender.query_results.add_query(QueryRecord(b"same", b"sender"))
        receiver.query_results.add_query(QueryRecord(b"same", b"receiver"))
        before = receiver.query_results.canonical_state()
    elif kind == "result":
        sender.query_results.add_result(ResultRecord(b"q", b"same", (b"sender",)))
        receiver.query_results.add_result(ResultRecord(b"q", b"same", (b"receiver",)))
        before = receiver.query_results.canonical_state()
    else:
        sender.catalog.add(BoundedReference(b"same", b"sender"))
        receiver.catalog.add(BoundedReference(b"same", b"receiver"))
        selection = ContactSelection(right_wants_from_left=(b"same",))
        before = receiver.catalog.canonical_state()
    report = run_bearer_contact(
        sender,
        receiver,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
        selection=selection,
    )
    assert report.outcome is BearerContactOutcome.ERROR
    assert report.error_code == error_code
    assert report.bearer_attempts == 0
    after = (
        receiver.catalog.canonical_state()
        if kind == "reference"
        else receiver.query_results.canonical_state()
    )
    assert after == before


def test_disconnect_returns_after_complete_record_boundaries() -> None:
    sender, receiver = memory_node("sender"), memory_node("receiver")
    sender.query_results.add_queries(query(index) for index in range(3))
    report = run_bearer_contact(
        sender,
        receiver,
        bearer=ScriptedInMemoryLink(
            ScriptedImpairmentPlan(
                left_to_right=(
                    ImpairmentAction.DELIVER,
                    ImpairmentAction.DISCONNECT,
                )
            )
        ),
        contact_budget=full_budget(),
    )
    assert report.outcome is BearerContactOutcome.DISCONNECTED
    assert report.durable_records_committed == 1
    assert report.disconnects == 1
    assert receiver.query_results.query_count == 1
    assert report.remaining_missing_work == 2


@pytest.mark.parametrize("failed_direction", ("left", "right"))
def test_directional_asymmetry_preserves_valid_partial_state(failed_direction: str) -> None:
    left, right = memory_node("left"), memory_node("right")
    left.query_results.add_query(query(1))
    right.query_results.add_query(query(2))
    left_action = ImpairmentAction.DROP if failed_direction == "left" else ImpairmentAction.DELIVER
    right_action = ImpairmentAction.DROP if failed_direction == "right" else ImpairmentAction.DELIVER
    report = run_bearer_contact(
        left,
        right,
        bearer=ScriptedInMemoryLink(
            ScriptedImpairmentPlan(
                default_left_to_right=left_action,
                default_right_to_left=right_action,
            )
        ),
        contact_budget=full_budget(),
    )
    assert report.outcome is BearerContactOutcome.PARTIAL_NOT_DELIVERED
    assert report.dropped_units == report.durable_records_committed == 1
    if failed_direction == "left":
        assert query(1).query_id not in right.query_results.sorted_query_ids()
        assert left.query_results.get_query(query(2).query_id) == query(2)
    else:
        assert right.query_results.get_query(query(1).query_id) == query(1)
        assert query(2).query_id not in left.query_results.sorted_query_ids()


def test_repeated_and_permanent_loss_never_claim_convergence_or_retry_internally() -> None:
    sender, receiver = memory_node("sender"), memory_node("receiver")
    sender.query_results.add_query(query(1))
    for _ in range(3):
        report = run_bearer_contact(
            sender,
            receiver,
            bearer=ScriptedInMemoryLink(
                ScriptedImpairmentPlan(default_left_to_right=ImpairmentAction.DROP)
            ),
            contact_budget=full_budget(),
        )
        assert report.outcome is BearerContactOutcome.PARTIAL_NOT_DELIVERED
        assert report.bearer_attempts == report.dropped_units == 1
        assert report.remaining_missing_work == 1
    assert receiver.query_results.query_count == 0
    delivered = run_bearer_contact(
        sender,
        receiver,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
    )
    assert delivered.outcome is BearerContactOutcome.NO_MORE_ELIGIBLE_WORK


def test_loss_consumes_contact_and_bearer_budgets_without_hidden_retry() -> None:
    sender, receiver = memory_node("sender"), memory_node("receiver")
    sender.query_results.add_queries(query(index) for index in range(3))
    contact_limited = run_bearer_contact(
        sender,
        receiver,
        bearer=ScriptedInMemoryLink(
            ScriptedImpairmentPlan(default_left_to_right=ImpairmentAction.DROP)
        ),
        contact_budget=ContactBudget(2, MAX_CONTACT_BYTES),
    )
    assert contact_limited.outcome is BearerContactOutcome.CONTACT_BUDGET_EXHAUSTED
    assert contact_limited.logical_records_attempted == contact_limited.bearer_attempts == 2
    assert contact_limited.dropped_units == 2
    assert receiver.query_results.query_count == 0

    attempt_limited = run_bearer_contact(
        sender,
        receiver,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
        bearer_budget=BearerBudget(max_attempts=1, max_trace_entries=1),
    )
    assert attempt_limited.outcome is BearerContactOutcome.BEARER_BUDGET_EXHAUSTED
    assert attempt_limited.bearer_attempts == 1
    assert receiver.query_results.query_count == 1


def test_byte_budget_counts_dropped_logical_unit_before_next_attempt() -> None:
    sender, receiver = memory_node("sender"), memory_node("receiver")
    sender.query_results.add_queries((query(1), query(2)))
    first_size = 6 + query(1).payload_bytes
    report = run_bearer_contact(
        sender,
        receiver,
        bearer=ScriptedInMemoryLink(
            ScriptedImpairmentPlan(default_left_to_right=ImpairmentAction.DROP)
        ),
        contact_budget=ContactBudget(2, first_size),
    )
    assert report.outcome is BearerContactOutcome.CONTACT_BUDGET_EXHAUSTED
    assert report.logical_bytes_attempted == first_size
    assert report.bearer_attempts == report.dropped_units == 1
