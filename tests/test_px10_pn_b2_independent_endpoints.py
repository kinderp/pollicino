from __future__ import annotations

import inspect
from pathlib import Path

from pollicino.net.contact import ContactNode, ContactSelection, ContactBudget, MAX_CONTACT_BYTES, MAX_CONTACT_ITEMS, run_contact
from pollicino.net.endpoint import (
    B2ContactOutcome,
    B2ContactSelection,
    RecordKind,
    ScriptedEncodedMessageLink,
    decode_message,
    run_independent_contact,
)
from px10_support import memory_endpoint, query, reference, result


def _populate(fixture, first: int, second: int) -> tuple[bytes, bytes]:
    fixture.query_results.add_query(query(first))
    fixture.query_results.add_result(result(first, first))
    selected = reference(second)
    fixture.catalog.add(selected)
    return query(first).query_id, selected.logical_key


def test_lossless_independent_endpoints_match_px8_canonical_state() -> None:
    left = memory_endpoint("left")
    right = memory_endpoint("right")
    local_left = memory_endpoint("local-left")
    local_right = memory_endpoint("local-right")
    _, left_key = _populate(left, 1, 1)
    _, right_key = _populate(right, 2, 2)
    _populate(local_left, 1, 1)
    _populate(local_right, 2, 2)

    b2 = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(),
        selection=B2ContactSelection(
            left_wants_from_right=(right_key,),
            right_wants_from_left=(left_key,),
        ),
    )
    px8 = run_contact(
        ContactNode(local_left.catalog, local_left.query_results),
        ContactNode(local_right.catalog, local_right.query_results),
        budget=ContactBudget(MAX_CONTACT_ITEMS, MAX_CONTACT_BYTES),
        selection=ContactSelection(
            left_wants_from_right=(right_key,),
            right_wants_from_left=(left_key,),
        ),
    )
    assert b2.outcome is B2ContactOutcome.NO_MORE_PLANNED_WORK
    assert px8.items_used == b2.durable_commits == 6
    assert b2.bearer_attempts == len(b2.trace)
    assert b2.control_bytes_encoded + b2.record_bytes_encoded == sum(
        entry.encoded_bytes for entry in b2.trace
    )
    assert left.catalog.canonical_state() == local_left.catalog.canonical_state()
    assert right.catalog.canonical_state() == local_right.catalog.canonical_state()
    assert left.query_results.canonical_state() == local_left.query_results.canonical_state()
    assert right.query_results.canonical_state() == local_right.query_results.canonical_state()


def test_advertisement_discloses_identity_and_digest_not_record_payload() -> None:
    endpoint = memory_endpoint("endpoint")
    opaque = b"unique-private-payload-not-in-control-message"
    endpoint.query_results.add_query(query(1, opaque))
    encoded = next(endpoint.endpoint.advertisement_messages(RecordKind.QUERY))
    decoded = decode_message(encoded)
    assert opaque not in encoded
    assert decoded.entries[0].identity == query(1).query_id
    assert len(decoded.entries[0].record_digest) == 32


def test_d3_result_does_not_automatically_select_or_transfer_reference() -> None:
    left = memory_endpoint("left")
    right = memory_endpoint("right")
    selected = reference(7)
    right.catalog.add(selected)
    right.query_results.add_result(result(1, 1, (selected.logical_key,)))
    report = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(),
    )
    assert report.durable_commits == 1
    assert left.query_results.result_count == 1
    assert len(left.catalog) == 0

    pulled = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(),
        selection=B2ContactSelection(left_wants_from_right=(selected.logical_key,)),
    )
    assert pulled.durable_commits == 1
    assert left.catalog.get(selected.logical_key) == selected


def test_production_driver_has_no_direct_store_visibility() -> None:
    source = inspect.getsource(run_independent_contact).lower()
    forbidden = (
        ".catalog",
        ".query_results",
        ".state_digest",
        ".receiver_known_ids",
        ".sorted_query_ids",
        ".sorted_result_ids",
        "_local_catalog",
        "_local_query_results",
        "__catalog",
        "__query_results",
    )
    assert not any(term in source for term in forbidden)

    module_source = Path(inspect.getfile(run_independent_contact)).read_text().lower()
    application_terms = (
        "faro",
        "dna",
        "travel dna",
        "content-specific",
        "topic semantics",
        "scientific trust",
        "publisher evidence",
        "recommendation",
        "school",
        "package validity",
    )
    assert not any(term in module_source for term in application_terms)
    deferred = (
        "pnf1",
        "fragmentframe",
        "fragment_payload",
        "reassemble_frames",
        "transmit_exact",
        "scarcelinkprofile",
        "from .link import",
    )
    assert not any(term in module_source for term in deferred)

    d4_source = Path(__file__).parents[1] / "src/pollicino/net/contact.py"
    concrete = ("lora", "freakwan", "bluetooth", "wi-fi", "tcp", "udp", "socket", "radio")
    lowered = d4_source.read_text().lower()
    assert not any(term in lowered for term in concrete)
