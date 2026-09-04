from __future__ import annotations

from pathlib import Path

from pollicino.net.bearer import (
    BearerContactOutcome,
    ImpairmentAction,
    ScriptedImpairmentPlan,
    ScriptedInMemoryLink,
    run_bearer_contact,
)
from pollicino.net.catalog import BoundedReference
from pollicino.net.contact import ContactSelection
from px9_support import close_node, full_budget, persistent_node, query, reference, reopen_node, result


def test_lossy_query_and_result_mule_with_restart_and_explicit_reference_selection(
    tmp_path: Path,
) -> None:
    roots = {name: tmp_path / name for name in ("a", "b", "c")}
    a = persistent_node(roots["a"], "A")
    b = persistent_node(roots["b"], "B")
    c = persistent_node(roots["c"], "semantic-blind-C")
    carried_query = query(7, b"opaque-interest")
    a.query_results.add_query(carried_query)

    lost = run_bearer_contact(
        a,
        c,
        bearer=ScriptedInMemoryLink(
            ScriptedImpairmentPlan(default_left_to_right=ImpairmentAction.DROP)
        ),
        contact_budget=full_budget(),
    )
    assert lost.outcome is BearerContactOutcome.PARTIAL_NOT_DELIVERED
    assert c.query_results.query_count == 0
    delivered = run_bearer_contact(
        a,
        c,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
    )
    assert delivered.durable_records_committed == 1
    close_node(c)
    c = reopen_node(roots["c"], "semantic-blind-C-restarted-query")

    forwarded_query = run_bearer_contact(
        c,
        b,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
    )
    assert forwarded_query.durable_records_committed == 1
    assert b.query_results.get_query(carried_query.query_id) == carried_query

    # Evaluation is an explicit application action outside contact and bearer.
    carried_result = result(7, 11, (b"offer-key",))
    b.query_results.add_result(carried_result)
    first_result_attempt = run_bearer_contact(
        b,
        c,
        bearer=ScriptedInMemoryLink(
            ScriptedImpairmentPlan(left_to_right=(ImpairmentAction.DISCONNECT,))
        ),
        contact_budget=full_budget(),
    )
    assert first_result_attempt.outcome is BearerContactOutcome.DISCONNECTED
    assert c.query_results.result_count == 0
    second_result_attempt = run_bearer_contact(
        b,
        c,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
    )
    assert second_result_attempt.durable_records_committed == 1
    close_node(c)
    c = reopen_node(roots["c"], "semantic-blind-C-restarted-result")

    forwarded_result = run_bearer_contact(
        c,
        a,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
    )
    assert forwarded_result.durable_records_committed == 1
    assert a.query_results.get_result(carried_result.identity) == carried_result

    # Candidate receipt neither retrieves nor mutates application authority.
    application_authority_events: list[str] = []
    assert len(a.catalog) == len(c.catalog) == 0
    assert application_authority_events == []

    selected_reference = BoundedReference(
        carried_result.candidate_keys[0], b"opaque-selected-reference"
    )
    b.catalog.add(selected_reference)
    b_to_c = run_bearer_contact(
        b,
        c,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
        selection=ContactSelection(
            right_wants_from_left=(selected_reference.logical_key,)
        ),
    )
    assert b_to_c.durable_records_committed == 1
    close_node(c)
    c = reopen_node(roots["c"], "semantic-blind-C-restarted-reference")
    c_to_a = run_bearer_contact(
        c,
        a,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
        selection=ContactSelection(
            right_wants_from_left=(selected_reference.logical_key,)
        ),
    )
    assert c_to_a.durable_records_committed == 1
    assert a.catalog.get(selected_reference.logical_key) == selected_reference
    assert application_authority_events == []

    close_node(a)
    close_node(b)
    close_node(c)


def test_semantic_blind_mule_converges_canonical_transport_state(tmp_path: Path) -> None:
    roots = {name: tmp_path / name for name in ("a", "b", "c")}
    a = persistent_node(roots["a"], "A")
    b = persistent_node(roots["b"], "B")
    c = persistent_node(roots["c"], "C")
    a.query_results.add_queries((query(1), query(2)))
    b.query_results.add_results((result(1, 1), result(2, 2)))

    for left, right in ((a, c), (c, b), (b, c), (c, a), (a, c), (c, b)):
        run_bearer_contact(
            left,
            right,
            bearer=ScriptedInMemoryLink(),
            contact_budget=full_budget(),
        )

    assert a.query_results.canonical_state() == b.query_results.canonical_state()
    assert b.query_results.canonical_state() == c.query_results.canonical_state()
    close_node(a)
    close_node(b)
    close_node(c)
