from __future__ import annotations

from dataclasses import replace

import pytest

from pollicino.net.bearer import (
    BearerAttemptResult,
    BearerContactOutcome,
    CompleteRecordUnit,
    ImpairmentAction,
    LinkDirection,
    ScriptedInMemoryLink,
    run_bearer_contact,
)
from pollicino.net.query import QueryRecord
from px9_support import full_budget, memory_node, query


class SubstitutingBearer:
    def attempt(self, unit: CompleteRecordUnit) -> BearerAttemptResult:
        changed = replace(
            unit,
            record=QueryRecord(unit.record.query_id, b"substituted"),
        )
        return BearerAttemptResult(ImpairmentAction.DELIVER, (changed,), True)


class InvalidResultBearer:
    def attempt(self, unit: CompleteRecordUnit) -> object:
        return object()


def test_bad_bearer_cannot_substitute_complete_record() -> None:
    sender, receiver = memory_node("sender"), memory_node("receiver")
    sender.query_results.add_query(query(1))
    before = receiver.query_results.canonical_state()
    report = run_bearer_contact(
        sender,
        receiver,
        bearer=SubstitutingBearer(),
        contact_budget=full_budget(),
    )
    assert report.outcome is BearerContactOutcome.ERROR
    assert report.error_code == "BEARERCONTRACTERROR"
    assert receiver.query_results.canonical_state() == before


def test_bad_bearer_result_fails_closed_without_receiver_mutation() -> None:
    sender, receiver = memory_node("sender"), memory_node("receiver")
    sender.query_results.add_query(query(1))
    before = receiver.query_results.canonical_state()
    report = run_bearer_contact(
        sender,
        receiver,
        bearer=InvalidResultBearer(),
        contact_budget=full_budget(),
    )
    assert report.outcome is BearerContactOutcome.ERROR
    assert report.error_code == "BEARERCONTRACTERROR"
    assert receiver.query_results.canonical_state() == before


def test_complete_unit_rejects_nonpositive_accounted_size() -> None:
    with pytest.raises(ValueError):
        CompleteRecordUnit(
            direction=LinkDirection.LEFT_TO_RIGHT,
            kind="query",
            identity=b"q",
            record=QueryRecord(b"q", b"payload"),
            logical_bytes=0,
        )


def test_receiver_quota_failure_preserves_prior_complete_commits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pollicino.net.query as query_module

    sender, receiver = memory_node("sender"), memory_node("receiver")
    sender.query_results.add_queries((query(1), query(2)))
    monkeypatch.setattr(query_module, "MAX_STORED_QUERIES", 1)
    report = run_bearer_contact(
        sender,
        receiver,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
    )
    assert report.outcome is BearerContactOutcome.ERROR
    assert report.error_code == "QUERY_RESULT_BOUNDS_ERROR"
    assert receiver.query_results.query_count == 1
    assert receiver.query_results.get_query(query(1).query_id) == query(1)
