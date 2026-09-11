from __future__ import annotations

from pollicino.net.adaptive_reconciliation import (
    AdaptiveIndependentEndpoint,
    AdaptivePolicy,
    run_adaptive_contact,
)
from pollicino.net.endpoint import RecordKind, ScriptedEncodedMessageLink
from px10_support import memory_endpoint, query, reference, result


def _run(source, receiver, kind, selected=()):
    return run_adaptive_contact(
        AdaptiveIndependentEndpoint(source.catalog, source.query_results),
        AdaptiveIndependentEndpoint(receiver.catalog, receiver.query_results),
        kind=kind,
        bearer=ScriptedEncodedMessageLink(),
        policy=AdaptivePolicy.selected_cost_aware(),
        selected_references=selected,
    )


def test_results_and_explicit_references_use_same_policy_without_auto_pull() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    ref = reference(1)
    source.catalog.add(ref)
    source.query_results.add_result(result(1, 1, (ref.logical_key,)))
    assert _run(source, receiver, RecordKind.RESULT).durable_commits == 1
    assert len(receiver.catalog) == 0
    assert _run(source, receiver, RecordKind.REFERENCE, (ref.logical_key,)).durable_commits == 1
    assert receiver.catalog.get(ref.logical_key) == ref


def test_semantic_blind_mule_carries_query_and_result() -> None:
    a = memory_endpoint("a")
    b = memory_endpoint("b")
    c = memory_endpoint("c")
    a.query_results.add_query(query(1))
    assert _run(a, c, RecordKind.QUERY).durable_commits == 1
    assert _run(c, b, RecordKind.QUERY).durable_commits == 1
    b.query_results.add_result(result(1, 1))
    assert _run(b, c, RecordKind.RESULT).durable_commits == 1
    assert _run(c, a, RecordKind.RESULT).durable_commits == 1
    assert a.query_results.get_result(result(1, 1).identity) == result(1, 1)


def test_directional_use_is_symmetric() -> None:
    left = memory_endpoint("left")
    right = memory_endpoint("right")
    left.query_results.add_query(query(1))
    right.query_results.add_query(query(2))
    assert _run(left, right, RecordKind.QUERY).durable_commits == 1
    assert _run(right, left, RecordKind.QUERY).durable_commits == 1
    assert left.query_results.canonical_state() == right.query_results.canonical_state()
