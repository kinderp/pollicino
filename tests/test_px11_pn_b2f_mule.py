from __future__ import annotations

from pollicino.net.bearer import ImpairmentAction, ScriptedImpairmentPlan
from pollicino.net.endpoint import B2ContactBudget, ScriptedEncodedMessageLink
from pollicino.net.fair_reconciliation import (
    FairContactSelection,
    FairIndependentEndpoint,
    run_fair_contact,
)
from px10_support import query, reference, result
from px11_support import (
    fair_memory_endpoint,
    fair_persistent_endpoint,
    reopen_fair_endpoint,
)


def _endpoint(fixture, label: str) -> FairIndependentEndpoint:
    return FairIndependentEndpoint(fixture.catalog, fixture.query_results, label)


def _converge(source, receiver, *, horizon=40, selection=None) -> int:
    commits = 0
    for contact in range(1, horizon + 1):
        report = run_fair_contact(
            _endpoint(source, "source"),
            _endpoint(receiver, "receiver"),
            bearer=ScriptedEncodedMessageLink(),
            budget=B2ContactBudget(max_bearer_attempts=25),
            selection=selection,
        )
        commits += report.durable_commits
        if (
            source.query_results.canonical_state()
            == receiver.query_results.canonical_state()
            and (
                selection is None
                or source.catalog.canonical_state() == receiver.catalog.canonical_state()
            )
        ):
            return contact
    raise AssertionError("mule leg exceeded explicit contact horizon")


def test_paged_query_result_and_reference_mule_with_restart_and_loss(tmp_path) -> None:
    a = fair_memory_endpoint("A")
    b = fair_memory_endpoint("B")
    c_root = tmp_path / "C"
    c = fair_persistent_endpoint(c_root, "C")
    a.query_results.add_queries(query(index) for index in range(250))

    lost = run_fair_contact(
        _endpoint(a, "A"),
        c.endpoint,
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(left_to_right=(ImpairmentAction.DROP,))
        ),
        budget=B2ContactBudget(max_bearer_attempts=25),
    )
    assert lost.drops == 1
    _converge(a, c)
    c.close()
    c = reopen_fair_endpoint(c_root, "C")

    disconnected = run_fair_contact(
        c.endpoint,
        _endpoint(b, "B"),
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(
                left_to_right=(ImpairmentAction.DISCONNECT,)
            )
        ),
        budget=B2ContactBudget(max_bearer_attempts=25),
    )
    assert disconnected.disconnects == 1
    _converge(c, b)
    assert b.query_results.query_count == 250

    b.query_results.add_results(result(index, 0) for index in range(250))
    uncertain = run_fair_contact(
        _endpoint(b, "B"),
        c.endpoint,
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(
                left_to_right=(
                    ImpairmentAction.DELIVER,
                    ImpairmentAction.DELIVER,
                    ImpairmentAction.DELIVER,
                    ImpairmentAction.DELIVER_UNCERTAIN,
                )
            )
        ),
        budget=B2ContactBudget(max_bearer_attempts=25),
    )
    assert uncertain.sender_uncertainties == 1
    assert c.query_results.result_count == 1
    c.close()
    c = reopen_fair_endpoint(c_root, "C")
    _converge(b, c)
    c.close()
    c = reopen_fair_endpoint(c_root, "C")
    _converge(c, a)
    assert a.query_results.result_count == 250

    references = tuple(reference(index) for index in range(150))
    b.catalog.add_many(references)
    selected = tuple(value.logical_key for value in references)
    b_to_c = FairContactSelection(right_wants_from_left=selected)
    _converge(b, c, selection=b_to_c)
    c.close()
    c = reopen_fair_endpoint(c_root, "C")
    c_to_a = FairContactSelection(right_wants_from_left=selected)
    _converge(c, a, selection=c_to_a)
    assert a.catalog.canonical_state() == b.catalog.canonical_state()
    c.close()


def test_contact_history_does_not_change_canonical_state() -> None:
    source = fair_memory_endpoint("source")
    tiny = fair_memory_endpoint("tiny")
    large = fair_memory_endpoint("large")
    lossy = fair_memory_endpoint("lossy")
    source.query_results.add_queries(query(index) for index in range(250))
    _converge(source, tiny, horizon=50)
    for _ in range(10):
        report = run_fair_contact(
            _endpoint(source, "source"),
            _endpoint(large, "large"),
            bearer=ScriptedEncodedMessageLink(),
        )
        if large.query_results.query_count == 250:
            break
    run_fair_contact(
        _endpoint(source, "source"),
        _endpoint(lossy, "lossy"),
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(left_to_right=(ImpairmentAction.DROP,))
        ),
    )
    _converge(source, lossy, horizon=50)
    assert (
        tiny.query_results.canonical_state()
        == large.query_results.canonical_state()
        == lossy.query_results.canonical_state()
        == source.query_results.canonical_state()
    )


def test_bounded_prefix_churn_is_safe_but_not_an_infinite_fairness_claim() -> None:
    source = fair_memory_endpoint("source")
    receiver = fair_memory_endpoint("receiver")
    source.query_results.add_queries(query(1_000 + index) for index in range(100))
    for contact in range(20):
        source.query_results.add_query(query(contact))
        run_fair_contact(
            _endpoint(source, "source"),
            _endpoint(receiver, "receiver"),
            bearer=ScriptedEncodedMessageLink(),
            budget=B2ContactBudget(max_bearer_attempts=20),
        )
    _converge(source, receiver, horizon=20)
    assert receiver.query_results.canonical_state() == source.query_results.canonical_state()
