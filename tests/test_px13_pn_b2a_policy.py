from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from pollicino.net.adaptive_reconciliation import (
    AdaptiveIndependentEndpoint,
    AdaptiveOutcome,
    AdaptivePolicy,
    AdaptivePolicyKind,
    run_adaptive_contact,
)
from pollicino.net.endpoint import B2ContactBudget, RecordKind, ScriptedEncodedMessageLink
from px10_support import memory_endpoint, query


def _adaptive(fixture, label="endpoint"):
    return AdaptiveIndependentEndpoint(fixture.catalog, fixture.query_results, label)


def _run(source, receiver, policy, budget=B2ContactBudget()):
    return run_adaptive_contact(
        _adaptive(source, "source"),
        _adaptive(receiver, "receiver"),
        kind=RecordKind.QUERY,
        bearer=ScriptedEncodedMessageLink(),
        policy=policy,
        budget=budget,
    )


def test_policy_bounds_and_order_are_explicit() -> None:
    assert AdaptivePolicy.exact_always().capacities == ()
    assert AdaptivePolicy.fixed(10).capacities == (10,)
    assert AdaptivePolicy.escalating((1, 10, 100, 1000)).max_compact_probes == 4
    assert AdaptivePolicy.selected_cost_aware().capacities == (10,)
    with pytest.raises(Exception):
        AdaptivePolicy.escalating((100, 10))
    with pytest.raises(Exception):
        AdaptivePolicy.escalating((1, 10, 100, 1000, 1001))


def test_exact_always_uses_no_compact_probe() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_query(query(1))
    report = _run(source, receiver, AdaptivePolicy.exact_always())
    assert report.policy_kind is AdaptivePolicyKind.EXACT_ALWAYS
    assert report.capacities_attempted == ()
    assert not report.exact_fallback_triggered
    assert report.decisions[0].reason == "EXACT_ALWAYS"
    assert report.durable_commits == 1


def test_zero_difference_is_resolved_by_one_small_summary() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    records = tuple(query(index) for index in range(1_000))
    source.query_results.add_queries(records)
    receiver.query_results.add_queries(records)
    report = _run(source, receiver, AdaptivePolicy.selected_cost_aware())
    assert report.outcome is AdaptiveOutcome.COMPACT_EQUAL
    assert report.capacities_attempted == (10,)
    assert report.control_bytes == 797
    assert not report.exact_fallback_triggered


@pytest.mark.parametrize("difference", (1, 2, 5, 10))
def test_small_unknown_difference_uses_compact_without_fixture_label(difference: int) -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    records = tuple(query(index) for index in range(10_000))
    source.query_results.add_queries(records)
    receiver.query_results.add_queries(records[:-difference])
    report = _run(source, receiver, AdaptivePolicy.selected_cost_aware())
    assert report.outcome is AdaptiveOutcome.COMPACT_PROGRESS
    assert report.capacities_attempted == (10,)
    assert report.durable_commits == difference
    assert not report.exact_fallback_triggered


def test_selected_policy_falls_back_after_one_failed_probe() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    records = tuple(query(index) for index in range(10_000))
    source.query_results.add_queries(records)
    receiver.query_results.add_queries(records[:-100])
    report = _run(source, receiver, AdaptivePolicy.selected_cost_aware())
    assert report.capacities_attempted == (10,)
    assert report.exact_fallback_triggered
    assert report.durable_commits > 0
    assert report.largest_summary_bytes == 797


def test_selected_policy_never_attempts_near_ceiling_capacity() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_queries(query(index) for index in range(10_000))
    report = _run(source, receiver, AdaptivePolicy.selected_cost_aware())
    assert report.capacities_attempted == (10,)
    assert report.largest_summary_bytes == 797
    assert report.b2_ceiling_margin == 28_448
    assert report.exact_fallback_triggered


def test_tiny_attempt_budget_preserves_exact_progress_reserve() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    records = tuple(query(index) for index in range(10_000))
    source.query_results.add_queries(records)
    receiver.query_results.add_queries(records[:-1])
    report = _run(
        source,
        receiver,
        AdaptivePolicy.selected_cost_aware(),
        B2ContactBudget(max_bearer_attempts=8, max_trace_entries=8),
    )
    assert report.capacities_attempted == ()
    assert report.decisions[0].reason == "EXACT_RESERVE"
    assert report.exact_fallback_triggered
    assert report.bearer_attempts <= 8


def test_oracle_knowledge_is_absent_from_selector_inputs_and_source() -> None:
    signature = inspect.signature(run_adaptive_contact)
    forbidden_inputs = {
        "actual_difference_size", "oracle_difference_size", "oracle_missing_set",
        "overlap", "fixture_label",
    }
    assert forbidden_inputs.isdisjoint(signature.parameters)
    source = inspect.getsource(run_adaptive_contact).lower()
    assert not any(term in source for term in forbidden_inputs)


@pytest.mark.parametrize("shape", ("prefix", "suffix", "sparse", "alternating", "random"))
def test_difference_topology_does_not_change_exact_final_state(shape: str) -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    records = tuple(query(index) for index in range(1_000))
    source.query_results.add_queries(records)
    if shape == "prefix":
        missing = set(range(20))
    elif shape == "suffix":
        missing = set(range(980, 1_000))
    elif shape == "sparse":
        missing = {0, 9, 99, 199, 299, 399, 499, 599, 699, 999}
    elif shape == "alternating":
        missing = set(range(0, 40, 2))
    else:
        missing = {17, 31, 83, 109, 211, 307, 401, 503, 701, 907}
    receiver.query_results.add_queries(
        record for index, record in enumerate(records) if index not in missing
    )
    report = _run(source, receiver, AdaptivePolicy.selected_cost_aware())
    assert report.durable_commits == len(missing)
    assert receiver.query_results.canonical_state() == source.query_results.canonical_state()


def test_adaptive_production_module_is_application_neutral_and_nonpersistent() -> None:
    module = Path(inspect.getfile(run_adaptive_contact)).read_text().lower()
    applications = ("faro", "dna", "delivery", "content", "topic", "publisher", "recommendation")
    persistent = ("peer history", "peer cursor", "last capacity", "persistent ack", "session journal")
    transports = ("socket", "tcp", "udp", "bluetooth", "wi-fi", "lora", "freakwan", "serial")
    assert not any(term in module for term in applications)
    assert not any(term in module for term in persistent)
    assert not any(term in module for term in transports)
