from __future__ import annotations

from pathlib import Path

import pytest

from pollicino.net.bearer import ImpairmentAction, ScriptedImpairmentPlan
from pollicino.net.compact_reconciliation import (
    CompactContactOutcome,
    CompactDecodeStatus,
    CompactIndependentEndpoint,
    run_compact_contact,
)
from pollicino.net.endpoint import RecordKind, ScriptedEncodedMessageLink
from pollicino.net.endpoint import EncodedBearerAttemptResult
from pollicino.net.bearer import LinkDirection
from pollicino.net.fair_reconciliation import FairIndependentEndpoint, run_fair_contact
from px10_support import memory_endpoint, persistent_endpoint, query, reference, reopen_endpoint, result


def _compact(fixture) -> CompactIndependentEndpoint:
    return CompactIndependentEndpoint(fixture.catalog, fixture.query_results)


def _contact(source, receiver, *, kind=RecordKind.QUERY, capacity=10, plan=ScriptedImpairmentPlan(), attempts=100, selected=()):
    return run_compact_contact(
        _compact(source), _compact(receiver), kind=kind, capacity=capacity,
        bearer=ScriptedEncodedMessageLink(plan), max_attempts=attempts,
        selected_references=selected,
    )


def test_lossless_query_result_and_explicit_reference_transfer() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_query(query(1))
    source.query_results.add_result(result(1, 1))
    ref = reference(1)
    source.catalog.add(ref)
    assert _contact(source, receiver).durable_commits == 1
    assert _contact(source, receiver, kind=RecordKind.RESULT).durable_commits == 1
    assert len(receiver.catalog) == 0
    report = _contact(source, receiver, kind=RecordKind.REFERENCE, selected=(ref.logical_key,))
    assert report.durable_commits == 1
    assert receiver.catalog.get(ref.logical_key) == ref


@pytest.mark.parametrize("action", (ImpairmentAction.DROP, ImpairmentAction.DISCONNECT))
def test_summary_loss_or_disconnect_is_safe_and_fresh_contact_recovers(action) -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_query(query(1))
    first = _contact(source, receiver, plan=ScriptedImpairmentPlan(left_to_right=(action,)))
    assert first.durable_commits == 0
    assert receiver.query_results.query_count == 0
    second = _contact(source, receiver)
    assert second.durable_commits == 1


@pytest.mark.parametrize(
    "plan",
    (
        ScriptedImpairmentPlan(right_to_left=(ImpairmentAction.DROP,)),
        ScriptedImpairmentPlan(left_to_right=(ImpairmentAction.DELIVER, ImpairmentAction.DROP)),
        ScriptedImpairmentPlan(
            right_to_left=(ImpairmentAction.DELIVER, ImpairmentAction.DROP)
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
def test_control_or_record_loss_never_causes_false_equality_and_recontact_recovers(plan) -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_query(query(1))
    impaired = _contact(source, receiver, capacity=1, plan=plan)
    assert impaired.outcome is CompactContactOutcome.PARTIAL_NOT_DELIVERED
    assert receiver.query_results.query_count == 0
    recovered = _contact(source, receiver, capacity=1)
    assert recovered.durable_commits == 1


def test_duplicate_control_and_record_are_idempotent() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_query(query(1))
    report = _contact(
        source, receiver,
        plan=ScriptedImpairmentPlan(
            left_to_right=(ImpairmentAction.DUPLICATE, ImpairmentAction.DELIVER, ImpairmentAction.DUPLICATE)
        ),
    )
    assert report.duplicates >= 1
    assert report.durable_commits == 1
    assert receiver.query_results.query_count == 1


def test_sender_uncertainty_after_commit_is_resolved_by_fresh_reconciliation() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_query(query(1))
    uncertain = _contact(
        source, receiver,
        plan=ScriptedImpairmentPlan(
            left_to_right=(
                ImpairmentAction.DELIVER,
                ImpairmentAction.DELIVER,
                ImpairmentAction.DELIVER_UNCERTAIN,
            )
        ),
    )
    assert uncertain.outcome is CompactContactOutcome.SENDER_UNCERTAIN
    assert receiver.query_results.query_count == 1
    fresh = _contact(source, receiver)
    assert fresh.outcome is CompactContactOutcome.EQUAL
    assert fresh.record_messages == 0
    assert fresh.durable_commits == 0


def test_capacity_failure_is_detected_and_does_not_claim_equality() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_queries(query(index) for index in range(100))
    report = _contact(source, receiver, capacity=1)
    assert report.outcome is CompactContactOutcome.FALLBACK_REQUIRED
    assert report.decode_status is CompactDecodeStatus.CAPACITY_EXCEEDED
    assert report.durable_commits == 0
    assert receiver.query_results.query_count == 0


def test_detected_capacity_failure_can_use_unchanged_px11_exact_fallback() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_queries(query(index) for index in range(100))
    compact = _contact(source, receiver, capacity=1)
    assert compact.fallback_required
    exact_commits = 0
    for _ in range(2):
        exact = run_fair_contact(
            FairIndependentEndpoint(source.catalog, source.query_results),
            FairIndependentEndpoint(receiver.catalog, receiver.query_results),
            bearer=ScriptedEncodedMessageLink(),
        )
        exact_commits += exact.durable_commits
    assert exact_commits == 100
    assert receiver.query_results.canonical_state() == source.query_results.canonical_state()


def test_conflicting_same_identity_is_discovered_and_native_store_fails_closed() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_query(query(1, b"source"))
    receiver.query_results.add_query(query(1, b"receiver"))
    before = receiver.query_results.canonical_state()
    report = _contact(source, receiver, capacity=2)
    assert report.outcome is CompactContactOutcome.ERROR
    assert report.error_code == "QUERYCONFLICTERROR"
    assert receiver.query_results.canonical_state() == before


class _CorruptFirstBearer:
    def attempt(self, direction: LinkDirection, encoded: bytes) -> EncodedBearerAttemptResult:
        corrupted = bytearray(encoded)
        corrupted[-1] ^= 1
        return EncodedBearerAttemptResult(ImpairmentAction.DELIVER, (bytes(corrupted),), True)


def test_corrupt_summary_fails_without_native_mutation() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_query(query(1))
    report = run_compact_contact(
        _compact(source), _compact(receiver), kind=RecordKind.QUERY, capacity=1,
        bearer=_CorruptFirstBearer(),
    )
    assert report.outcome is CompactContactOutcome.ERROR
    assert report.error_code == "COMPACTDECODEERROR"
    assert receiver.query_results.query_count == 0


def test_repeated_finite_contacts_preserve_static_fairness() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_queries(query(index) for index in range(1_000))
    contacts = 0
    while receiver.query_results.query_count < 1_000:
        report = _contact(source, receiver, capacity=1_000, attempts=50)
        contacts += 1
        assert report.outcome in (CompactContactOutcome.BUDGET_EXHAUSTED, CompactContactOutcome.DISCOVERED)
        assert contacts <= 25
    assert receiver.query_results.canonical_state() == source.query_results.canonical_state()


def test_query_and_result_cross_semantic_blind_mule_with_fresh_endpoints() -> None:
    a = memory_endpoint("a")
    b = memory_endpoint("b")
    c = memory_endpoint("c")
    a.query_results.add_query(query(1))
    assert _contact(a, c, capacity=1).durable_commits == 1
    assert _contact(c, b, capacity=1).durable_commits == 1
    b.query_results.add_result(result(1, 1))
    assert _contact(b, c, kind=RecordKind.RESULT, capacity=1).durable_commits == 1
    assert _contact(c, a, kind=RecordKind.RESULT, capacity=1).durable_commits == 1
    assert a.query_results.get_result(result(1, 1).identity) == result(1, 1)


def test_bounded_partial_progress_restarts_without_compact_session_state(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    source = persistent_endpoint(source_root, "source")
    receiver = persistent_endpoint(receiver_root, "receiver")
    source.query_results.add_queries(query(index) for index in range(105))
    first = _contact(source, receiver, capacity=105, attempts=20)
    assert first.outcome is CompactContactOutcome.BUDGET_EXHAUSTED
    assert 0 < receiver.query_results.query_count < 105
    source.close()
    receiver.close()
    source = reopen_endpoint(source_root, "source")
    receiver = reopen_endpoint(receiver_root, "receiver")
    contacts = 1
    while receiver.query_results.query_count < 105:
        report = _contact(source, receiver, capacity=105, attempts=20)
        contacts += 1
        assert contacts <= 10
    assert receiver.query_results.query_count == 105
    assert receiver.query_results.canonical_state() == source.query_results.canonical_state()
    source.close()
    receiver.close()


def test_permanent_loss_returns_finitely_without_false_convergence() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_query(query(1))
    report = _contact(
        source, receiver,
        plan=ScriptedImpairmentPlan(default_left_to_right=ImpairmentAction.DROP),
    )
    assert report.outcome is CompactContactOutcome.PARTIAL_NOT_DELIVERED
    assert report.bearer_attempts == 1
    assert report.durable_commits == 0
