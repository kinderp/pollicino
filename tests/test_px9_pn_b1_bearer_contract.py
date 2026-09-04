from __future__ import annotations

from pathlib import Path

import pytest

from pollicino.net.bearer import (
    MAX_BEARER_ATTEMPTS,
    MAX_BEARER_TRACE_ENTRIES,
    BearerBoundsError,
    BearerBudget,
    BearerContactOutcome,
    ImpairmentAction,
    ScriptedImpairmentPlan,
    ScriptedInMemoryLink,
    run_bearer_contact,
)
from pollicino.net.contact import ContactSelection, run_contact
from pollicino.net.query import MAX_QUERY_PAYLOAD_BYTES, QueryRecord, QueryResultBoundsError
from px9_support import full_budget, memory_node, query, reference, result


def _populate_pair(left, right) -> tuple[bytes, bytes]:
    left.query_results.add_query(query(1))
    right.query_results.add_query(query(2))
    left.query_results.add_result(result(1, 1))
    right.query_results.add_result(result(2, 2))
    left_reference = reference(1)
    right_reference = reference(2)
    left.catalog.add(left_reference)
    right.catalog.add(right_reference)
    return left_reference.logical_key, right_reference.logical_key


def test_lossless_b1_matches_equivalent_px8_contact_canonical_state() -> None:
    local_left, local_right = memory_node("local-left"), memory_node("local-right")
    bearer_left, bearer_right = memory_node("bearer-left"), memory_node("bearer-right")
    left_key, right_key = _populate_pair(local_left, local_right)
    assert _populate_pair(bearer_left, bearer_right) == (left_key, right_key)
    selection = ContactSelection(
        right_wants_from_left=(left_key,),
        left_wants_from_right=(right_key,),
    )

    local_report = run_contact(
        local_left,
        local_right,
        budget=full_budget(),
        selection=selection,
    )
    bearer_report = run_bearer_contact(
        bearer_left,
        bearer_right,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
        selection=selection,
    )

    assert local_report.items_used == bearer_report.durable_records_committed == 6
    assert bearer_report.outcome is BearerContactOutcome.NO_MORE_ELIGIBLE_WORK
    assert local_left.catalog.canonical_state() == bearer_left.catalog.canonical_state()
    assert local_right.catalog.canonical_state() == bearer_right.catalog.canonical_state()
    assert local_left.query_results.canonical_state() == bearer_left.query_results.canonical_state()
    assert local_right.query_results.canonical_state() == bearer_right.query_results.canonical_state()


def test_delayed_complete_unit_is_delivered_without_fragmentation_or_retry() -> None:
    sender, receiver = memory_node("sender"), memory_node("receiver")
    sender.query_results.add_query(query(1))
    link = ScriptedInMemoryLink(
        ScriptedImpairmentPlan(
            left_to_right=(ImpairmentAction.DELAY_DELIVER,),
        )
    )
    report = run_bearer_contact(
        sender,
        receiver,
        bearer=link,
        contact_budget=full_budget(),
    )
    assert report.outcome is BearerContactOutcome.NO_MORE_ELIGIBLE_WORK
    assert report.delayed_units == 1
    assert report.bearer_attempts == 1
    assert report.delivered_presentations == 1
    assert report.queued_units_peak == 1
    assert link.queued_units == 0


def test_bearer_and_trace_budgets_are_positive_and_hard_bounded() -> None:
    BearerBudget(MAX_BEARER_ATTEMPTS, MAX_BEARER_TRACE_ENTRIES)
    with pytest.raises(BearerBoundsError):
        BearerBudget(0, 1)
    with pytest.raises(BearerBoundsError):
        BearerBudget(MAX_BEARER_ATTEMPTS + 1, 1)
    with pytest.raises(BearerBoundsError):
        BearerBudget(1, MAX_BEARER_TRACE_ENTRIES + 1)
    with pytest.raises(BearerBoundsError):
        ScriptedImpairmentPlan(
            left_to_right=(ImpairmentAction.DROP,) * (MAX_BEARER_ATTEMPTS + 1)
        )


def test_existing_query_payload_bound_remains_authoritative_through_b1() -> None:
    sender, receiver = memory_node("sender"), memory_node("receiver")
    maximum = QueryRecord(b"maximum", b"x" * MAX_QUERY_PAYLOAD_BYTES)
    sender.query_results.add_query(maximum)
    report = run_bearer_contact(
        sender,
        receiver,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
    )
    assert report.durable_records_committed == 1
    assert receiver.query_results.get_query(maximum.query_id) == maximum
    with pytest.raises(QueryResultBoundsError):
        QueryRecord(b"over", b"x" * (MAX_QUERY_PAYLOAD_BYTES + 1))


def test_b1_and_d4_sources_preserve_layering_and_neutrality() -> None:
    repository = Path(__file__).parents[1]
    bearer_source = (repository / "src/pollicino/net/bearer.py").read_text().lower()
    contact_source = (repository / "src/pollicino/net/contact.py").read_text().lower()
    application_terms = (
        "faro",
        "dna",
        "delivery",
        "content",
        "topic",
        "registry",
        "rider",
        "publisher",
        "trust",
        "payment",
    )
    concrete_bearers = (
        "lora",
        "lorawan",
        "freakwan",
        "bluetooth",
        "wi-fi",
        "tcp",
        "udp",
        "socket",
        "radio",
        "serial port",
    )
    deferred_protocol_terms = (
        "fragment_payload",
        "fragmentframe",
        "transmit_exact",
        "scarcelinkprofile",
        "persistence_ack",
        "custody",
    )
    assert not any(term in bearer_source for term in application_terms)
    assert not any(term in contact_source for term in concrete_bearers)
    assert not any(term in bearer_source for term in deferred_protocol_terms)
    assert "from .link import" not in bearer_source
    assert "from .bearer import" not in contact_source
