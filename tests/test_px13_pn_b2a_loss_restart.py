from __future__ import annotations

from pathlib import Path

import pytest

from pollicino.net.adaptive_reconciliation import (
    AdaptiveIndependentEndpoint,
    AdaptiveOutcome,
    AdaptivePolicy,
    run_adaptive_contact,
)
from pollicino.net.bearer import ImpairmentAction, LinkDirection, ScriptedImpairmentPlan
from pollicino.net.endpoint import (
    B2ContactBudget,
    EncodedBearerAttemptResult,
    RecordKind,
    ScriptedEncodedMessageLink,
)
from px10_support import memory_endpoint, persistent_endpoint, query, reopen_endpoint


def _run(source, receiver, plan=ScriptedImpairmentPlan(), budget=B2ContactBudget()):
    return run_adaptive_contact(
        AdaptiveIndependentEndpoint(source.catalog, source.query_results),
        AdaptiveIndependentEndpoint(receiver.catalog, receiver.query_results),
        kind=RecordKind.QUERY,
        bearer=ScriptedEncodedMessageLink(plan),
        policy=AdaptivePolicy.selected_cost_aware(),
        budget=budget,
    )


@pytest.mark.parametrize(
    "action",
    (
        ImpairmentAction.DROP,
        ImpairmentAction.DUPLICATE,
        ImpairmentAction.DELAY_DELIVER,
        ImpairmentAction.DISCONNECT,
    ),
)
def test_transport_action_is_not_misread_as_capacity_evidence(action) -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_query(query(1))
    report = _run(
        source,
        receiver,
        ScriptedImpairmentPlan(left_to_right=(action,)),
    )
    if action in (ImpairmentAction.DUPLICATE, ImpairmentAction.DELAY_DELIVER):
        assert receiver.query_results.query_count == 1
    else:
        assert report.capacities_attempted == (10,)
        assert not report.exact_fallback_triggered
        assert receiver.query_results.query_count == 0


@pytest.mark.parametrize(
    "plan",
    (
        ScriptedImpairmentPlan(right_to_left=(ImpairmentAction.DROP,)),
        ScriptedImpairmentPlan(
            left_to_right=(ImpairmentAction.DELIVER, ImpairmentAction.DROP)
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
def test_request_reveal_or_record_loss_is_safe_and_fresh_contact_recovers(plan) -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_query(query(1))
    first = _run(source, receiver, plan)
    assert first.outcome is AdaptiveOutcome.PARTIAL
    assert receiver.query_results.query_count == 0
    second = _run(source, receiver)
    assert second.durable_commits == 1


def test_sender_uncertainty_is_resolved_from_durable_receiver_state() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_query(query(1))
    uncertain = _run(
        source,
        receiver,
        ScriptedImpairmentPlan(
            left_to_right=(
                ImpairmentAction.DELIVER,
                ImpairmentAction.DELIVER,
                ImpairmentAction.DELIVER_UNCERTAIN,
            )
        ),
    )
    assert uncertain.outcome is AdaptiveOutcome.SENDER_UNCERTAIN
    assert receiver.query_results.query_count == 1
    fresh = _run(source, receiver)
    assert fresh.outcome is AdaptiveOutcome.COMPACT_EQUAL
    assert fresh.record_messages == 0


class _CorruptFirstBearer:
    def attempt(self, direction: LinkDirection, encoded: bytes) -> EncodedBearerAttemptResult:
        corrupted = bytearray(encoded)
        corrupted[-1] ^= 1
        return EncodedBearerAttemptResult(ImpairmentAction.DELIVER, (bytes(corrupted),), True)


def test_corruption_is_not_misread_as_capacity_failure() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_query(query(1))
    report = run_adaptive_contact(
        AdaptiveIndependentEndpoint(source.catalog, source.query_results),
        AdaptiveIndependentEndpoint(receiver.catalog, receiver.query_results),
        kind=RecordKind.QUERY,
        bearer=_CorruptFirstBearer(),
        policy=AdaptivePolicy.selected_cost_aware(),
    )
    assert report.outcome is AdaptiveOutcome.ERROR
    assert report.capacities_attempted == (10,)
    assert not report.exact_fallback_triggered
    assert receiver.query_results.query_count == 0


def test_partial_progress_restart_uses_fresh_selector_and_durable_state(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    source = persistent_endpoint(source_root, "source")
    receiver = persistent_endpoint(receiver_root, "receiver")
    source.query_results.add_queries(query(index) for index in range(105))
    first = _run(
        source,
        receiver,
        budget=B2ContactBudget(max_bearer_attempts=25, max_trace_entries=25),
    )
    assert 0 < first.durable_commits < 105
    source.close()
    receiver.close()
    source = reopen_endpoint(source_root, "source")
    receiver = reopen_endpoint(receiver_root, "receiver")
    contacts = 1
    while receiver.query_results.query_count < 105:
        report = _run(
            source,
            receiver,
            budget=B2ContactBudget(max_bearer_attempts=25, max_trace_entries=25),
        )
        contacts += 1
        assert contacts <= 10
        assert report.durable_commits > 0
    assert receiver.query_results.canonical_state() == source.query_results.canonical_state()
    assert not any(
        term in path.name.lower()
        for root in (source_root, receiver_root)
        for path in root.rglob("*")
        for term in ("peer", "policy", "capacity", "escalation", "session")
    )
    source.close()
    receiver.close()
