from __future__ import annotations

import pytest

from pollicino.net.adaptive_reconciliation import (
    AdaptiveIndependentEndpoint,
    AdaptiveOutcome,
    AdaptivePolicy,
    run_adaptive_contact,
)
from pollicino.net.endpoint import B2ContactBudget, RecordKind, ScriptedEncodedMessageLink
from px10_support import memory_endpoint, query


def _run(source, receiver, policy, budget=B2ContactBudget()):
    return run_adaptive_contact(
        AdaptiveIndependentEndpoint(source.catalog, source.query_results),
        AdaptiveIndependentEndpoint(receiver.catalog, receiver.query_results),
        kind=RecordKind.QUERY,
        bearer=ScriptedEncodedMessageLink(),
        policy=policy,
        budget=budget,
    )


@pytest.mark.parametrize(
    "policy",
    (
        AdaptivePolicy.fixed(1),
        AdaptivePolicy.fixed(10),
        AdaptivePolicy.fixed(100),
        AdaptivePolicy.escalating((1, 10, 100, 1000)),
        AdaptivePolicy.escalating((10, 1000)),
        AdaptivePolicy.escalating((10, 100)),
        AdaptivePolicy.escalating((100, 1000)),
    ),
)
def test_registered_policy_families_terminate_and_preserve_exactness(policy) -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_queries(query(index) for index in range(250))
    report = _run(source, receiver, policy)
    assert report.bearer_attempts <= 100
    assert len(report.capacities_attempted) <= policy.max_compact_probes
    assert receiver.query_results.query_count == report.durable_commits
    assert receiver.query_results.query_count <= 250


def test_selected_policy_avoids_fresh_contact_thrashing_on_large_difference() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_queries(query(index) for index in range(1_000))
    reports = []
    while receiver.query_results.query_count < 1_000:
        report = _run(source, receiver, AdaptivePolicy.selected_cost_aware())
        reports.append(report)
        assert len(reports) <= 12
        assert report.capacities_attempted == (10,)
        assert report.exact_fallback_triggered
        assert report.durable_commits > 0
    assert receiver.query_results.canonical_state() == source.query_results.canonical_state()
    assert sum(report.durable_commits for report in reports) == 1_000


def test_small_contacts_choose_exact_and_make_progress_instead_of_reprobing() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_queries(query(index) for index in range(100))
    contacts = 0
    while receiver.query_results.query_count < 100:
        report = _run(
            source,
            receiver,
            AdaptivePolicy.selected_cost_aware(),
            B2ContactBudget(max_bearer_attempts=8, max_trace_entries=8),
        )
        contacts += 1
        assert contacts <= 33
        assert report.capacities_attempted == ()
        assert report.exact_fallback_triggered
        assert report.durable_commits > 0
    assert receiver.query_results.canonical_state() == source.query_results.canonical_state()
    assert contacts == 33


@pytest.mark.parametrize("difference", (1_001, 2_000, 5_000, 10_000))
def test_difference_above_compact_max_falls_back_finitely(difference: int) -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_queries(query(index) for index in range(10_000))
    receiver.query_results.add_queries(query(index) for index in range(10_000 - difference))
    report = _run(source, receiver, AdaptivePolicy.selected_cost_aware())
    assert report.capacities_attempted == (10,)
    assert report.exact_fallback_triggered
    assert report.bearer_attempts <= 100
    assert report.durable_commits > 0
    assert report.outcome in (AdaptiveOutcome.EXACT_PROGRESS, AdaptiveOutcome.BUDGET_EXHAUSTED)


def test_control_budget_cannot_be_bypassed_by_compact_probe() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_queries(query(index) for index in range(100))
    report = _run(
        source,
        receiver,
        AdaptivePolicy.selected_cost_aware(),
        B2ContactBudget(max_control_bytes=500),
    )
    assert report.capacities_attempted == ()
    assert report.control_bytes <= 500
    assert report.bearer_attempts <= 100


def test_exact_cost_estimate_is_local_and_conservative_for_empty_receiver() -> None:
    source = memory_endpoint("source")
    source.query_results.add_queries(query(index) for index in range(1_000))
    endpoint = AdaptiveIndependentEndpoint(source.catalog, source.query_results)
    estimate = endpoint.exact_control_upper_bound(RecordKind.QUERY)
    assert estimate > 0
    assert estimate >= 97_950
