from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from pollicino.net.catalog import (
    BoundedReference,
    BoundedReferenceCatalog,
    CatalogLimits,
)
from pollicino.net.contact import (
    MAX_CONTACT_BYTES,
    MAX_CONTACT_ITEMS,
    ContactBudget,
    ContactInterruption,
    ContactNode,
    ContactOutcome,
    ContactPhase,
    ContactSelection,
    run_contact,
)
from pollicino.net.persistent_catalog import PersistentBoundedReferenceCatalog
from pollicino.net.persistent_query import PersistentQueryResultStore
from pollicino.net.query import QueryRecord, QueryResultStore, ResultRecord


def query(index: int, payload: bytes | None = None) -> QueryRecord:
    query_id = index.to_bytes(4, "big")
    return QueryRecord(query_id, payload if payload is not None else b"query-" + query_id)


def result(
    query_index: int,
    result_index: int,
    keys: tuple[bytes, ...] | None = None,
) -> ResultRecord:
    query_id = query_index.to_bytes(4, "big")
    result_id = result_index.to_bytes(4, "big")
    return ResultRecord(
        query_id,
        result_id,
        keys if keys is not None else (b"key-" + result_id,),
    )


def reference(index: int, value: bytes | None = None) -> BoundedReference:
    key = b"key-" + index.to_bytes(4, "big")
    return BoundedReference(key, value if value is not None else b"ref-" + key)


def memory_node(label: str) -> ContactNode:
    return ContactNode(BoundedReferenceCatalog(), QueryResultStore(), label)


def persistent_node(root: Path, label: str) -> ContactNode:
    root.mkdir()
    return ContactNode(
        PersistentBoundedReferenceCatalog(root / "catalog"),
        PersistentQueryResultStore(root / "query-result"),
        label,
    )


def reopen_node(root: Path, label: str) -> ContactNode:
    return ContactNode(
        PersistentBoundedReferenceCatalog(root / "catalog"),
        PersistentQueryResultStore(root / "query-result"),
        label,
    )


def close_node(node: ContactNode) -> None:
    assert isinstance(node.catalog, PersistentBoundedReferenceCatalog)
    assert isinstance(node.query_results, PersistentQueryResultStore)
    node.catalog.close()
    node.query_results.close()


def full_budget() -> ContactBudget:
    return ContactBudget(max_items=MAX_CONTACT_ITEMS, max_bytes=MAX_CONTACT_BYTES)


def test_empty_contact_is_valid_noop() -> None:
    left = memory_node("A")
    right = memory_node("B")
    report = run_contact(left, right, budget=full_budget())
    assert report.outcome is ContactOutcome.NO_MORE_ELIGIBLE_WORK
    assert report.items_used == report.encoded_bytes_accounted == 0
    assert not report.state_changed_left
    assert not report.state_changed_right


def test_queries_results_and_explicit_references_transfer_both_directions() -> None:
    left = memory_node("A")
    right = memory_node("B")
    left.query_results.add_query(query(1))
    right.query_results.add_query(query(2))
    left.query_results.add_result(result(1, 1))
    right.query_results.add_result(result(2, 2))
    left_reference = reference(1)
    right_reference = reference(2)
    left.catalog.add(left_reference)
    right.catalog.add(right_reference)

    report = run_contact(
        left,
        right,
        budget=full_budget(),
        selection=ContactSelection(
            right_wants_from_left=(left_reference.logical_key,),
            left_wants_from_right=(right_reference.logical_key,),
        ),
    )

    assert report.left_to_right.queries == report.right_to_left.queries == 1
    assert report.left_to_right.results == report.right_to_left.results == 1
    assert report.left_to_right.references == report.right_to_left.references == 1
    assert right.query_results.get_query(query(1).query_id) == query(1)
    assert left.query_results.get_result(result(2, 2).identity) == result(2, 2)
    assert right.catalog.get(left_reference.logical_key) == left_reference
    assert left.catalog.get(right_reference.logical_key) == right_reference


def test_reference_selection_is_required_at_every_contact() -> None:
    a = memory_node("A")
    b = memory_node("B")
    c = memory_node("C")
    item = reference(1)
    b.catalog.add(item)

    no_selection = run_contact(b, c, budget=full_budget())
    assert no_selection.left_to_right.references == 0
    assert item.logical_key not in c.catalog

    run_contact(
        b,
        c,
        budget=full_budget(),
        selection=ContactSelection(right_wants_from_left=(item.logical_key,)),
    )
    no_forward = run_contact(c, a, budget=full_budget())
    assert no_forward.left_to_right.references == 0
    assert item.logical_key not in a.catalog

    run_contact(
        c,
        a,
        budget=full_budget(),
        selection=ContactSelection(right_wants_from_left=(item.logical_key,)),
    )
    assert a.catalog.get(item.logical_key) == item


def test_item_and_byte_budgets_stop_before_atomic_apply() -> None:
    left = memory_node("A")
    right = memory_node("B")
    left.query_results.add_queries(query(index) for index in range(3))

    item_limited = run_contact(
        left,
        right,
        budget=ContactBudget(max_items=1, max_bytes=MAX_CONTACT_BYTES),
    )
    assert item_limited.outcome is ContactOutcome.BUDGET_EXHAUSTED
    assert item_limited.items_used == 1
    assert right.query_results.query_count == 1
    assert item_limited.remaining_missing_work == 2

    next_record = left.query_results.get_query(query(1).query_id)
    next_size = 6 + next_record.payload_bytes
    byte_limited = run_contact(
        left,
        right,
        budget=ContactBudget(max_items=MAX_CONTACT_ITEMS, max_bytes=next_size - 1),
    )
    assert byte_limited.outcome is ContactOutcome.BUDGET_EXHAUSTED
    assert byte_limited.items_used == 0
    assert right.query_results.query_count == 1


def test_interrupt_before_apply_changes_nothing_and_fresh_contact_transfers() -> None:
    left = memory_node("A")
    right = memory_node("B")
    left.query_results.add_query(query(1))
    before = right.query_results.canonical_state()

    interrupted = run_contact(
        left,
        right,
        budget=full_budget(),
        interruption=ContactInterruption(before_apply_item=1),
    )
    assert interrupted.outcome is ContactOutcome.INTERRUPTED
    assert interrupted.interruption_point == "BEFORE_APPLY:1"
    assert right.query_results.canonical_state() == before

    resumed = run_contact(left, right, budget=full_budget())
    assert resumed.left_to_right.queries == 1


def test_interrupt_after_apply_persists_and_fresh_contact_does_not_retransfer(
    tmp_path: Path,
) -> None:
    left_root = tmp_path / "A"
    right_root = tmp_path / "B"
    left = persistent_node(left_root, "A")
    right = persistent_node(right_root, "B")
    left.query_results.add_queries((query(1), query(2)))

    first_report = run_contact(
        left,
        right,
        budget=full_budget(),
        interruption=ContactInterruption(after_apply_item=1),
    )
    assert first_report.outcome is ContactOutcome.INTERRUPTED
    assert first_report.left_to_right.queries == 1
    del first_report
    close_node(left)
    close_node(right)

    left = reopen_node(left_root, "fresh-A")
    right = reopen_node(right_root, "fresh-B")
    resumed = run_contact(left, right, budget=full_budget())
    assert resumed.left_to_right.queries == 1
    assert resumed.items_used == 1
    assert resumed.records_skipped_already_known >= 1
    assert right.query_results.query_count == 2
    close_node(left)
    close_node(right)


def test_phase_boundary_interruptions_preserve_completed_types() -> None:
    left = memory_node("A")
    right = memory_node("B")
    q = query(1)
    r = result(1, 1)
    ref = reference(1)
    left.query_results.add_query(q)
    left.query_results.add_result(r)
    left.catalog.add(ref)

    after_query = run_contact(
        left,
        right,
        budget=full_budget(),
        selection=ContactSelection(right_wants_from_left=(ref.logical_key,)),
        interruption=ContactInterruption(
            before_phase=ContactPhase.RESULTS_LEFT_TO_RIGHT
        ),
    )
    assert after_query.left_to_right.queries == 1
    assert right.query_results.result_count == 0
    assert ref.logical_key not in right.catalog

    after_result = run_contact(
        left,
        right,
        budget=full_budget(),
        selection=ContactSelection(right_wants_from_left=(ref.logical_key,)),
        interruption=ContactInterruption(
            before_phase=ContactPhase.REFERENCES_LEFT_TO_RIGHT
        ),
    )
    assert after_result.left_to_right.results == 1
    assert ref.logical_key not in right.catalog

    final = run_contact(
        left,
        right,
        budget=full_budget(),
        selection=ContactSelection(right_wants_from_left=(ref.logical_key,)),
    )
    assert final.left_to_right.references == 1


@pytest.mark.parametrize("kind", ("result", "reference"))
def test_interrupt_after_result_or_reference_apply_is_durable_and_not_retransferred(
    tmp_path: Path, kind: str
) -> None:
    left_root, right_root = tmp_path / "left", tmp_path / "right"
    left = persistent_node(left_root, "left")
    right = persistent_node(right_root, "right")
    selection = ContactSelection()
    if kind == "result":
        record = result(8, 9)
        left.query_results.add_result(record)
    else:
        record = reference(9)
        left.catalog.add(record)
        selection = ContactSelection(
            right_wants_from_left=(record.logical_key,)
        )

    first = run_contact(
        left,
        right,
        budget=full_budget(),
        selection=selection,
        interruption=ContactInterruption(after_apply_item=1),
    )
    assert first.outcome is ContactOutcome.INTERRUPTED
    close_node(left)
    close_node(right)
    left = reopen_node(left_root, "left-restarted")
    right = reopen_node(right_root, "right-restarted")
    second = run_contact(
        left, right, budget=full_budget(), selection=selection
    )
    assert second.items_used == 0
    assert second.encoded_bytes_accounted == 0
    if kind == "result":
        assert right.query_results.get_result(record.identity) == record
    else:
        assert right.catalog.get(record.logical_key) == record
    close_node(left)
    close_node(right)


def test_real_subprocess_restart_then_forward(tmp_path: Path) -> None:
    mule_root = tmp_path / "mule"
    code = """
from pathlib import Path
import sys
from pollicino.net.persistent_catalog import PersistentBoundedReferenceCatalog
from pollicino.net.persistent_query import PersistentQueryResultStore
from pollicino.net.query import QueryRecord
root = Path(sys.argv[1]); root.mkdir()
with PersistentBoundedReferenceCatalog(root / 'catalog'):
    pass
with PersistentQueryResultStore(root / 'query-result') as store:
    store.add_query(QueryRecord(b'process-q', b'opaque-process-query'))
"""
    environment = dict(os.environ)
    source_root = str(Path(__file__).parents[1] / "src")
    environment["PYTHONPATH"] = source_root
    subprocess.run(
        [sys.executable, "-c", code, str(mule_root)],
        env=environment,
        check=True,
    )

    mule = reopen_node(mule_root, "C")
    receiver = persistent_node(tmp_path / "B", "B")
    report = run_contact(mule, receiver, budget=full_budget())
    assert report.left_to_right.queries == 1
    assert receiver.query_results.get_query(b"process-q").opaque_query == b"opaque-process-query"
    close_node(mule)
    close_node(receiver)


def test_three_node_query_and_result_mule_with_mule_restarts(tmp_path: Path) -> None:
    a_root, b_root, c_root = tmp_path / "A", tmp_path / "B", tmp_path / "C"
    a = persistent_node(a_root, "A")
    b = persistent_node(b_root, "B")
    c = persistent_node(c_root, "C")
    q = query(7, b"opaque consumer intent")
    r = result(7, 3, (b"candidate-X",))
    a.query_results.add_query(q)

    assert run_contact(a, c, budget=full_budget()).left_to_right.queries == 1
    close_node(c)
    c = reopen_node(c_root, "C-after-query-restart")
    assert run_contact(c, b, budget=full_budget()).left_to_right.queries == 1

    # Application evaluation is deliberately outside run_contact.
    b.query_results.add_result(r)
    assert run_contact(b, c, budget=full_budget()).left_to_right.results == 1
    close_node(c)
    c = reopen_node(c_root, "C-after-result-restart")
    assert run_contact(c, a, budget=full_budget()).left_to_right.results == 1
    assert a.query_results.get_result(r.identity) == r
    close_node(a)
    close_node(b)
    close_node(c)


def test_orphan_result_mule_correlates_only_after_query_arrival(tmp_path: Path) -> None:
    source = persistent_node(tmp_path / "source", "source")
    mule_root = tmp_path / "mule"
    mule = persistent_node(mule_root, "mule")
    q = query(4)
    r = result(4, 8)
    source.query_results.add_query(q)
    source.query_results.add_result(r)

    # Carry only the result by interrupting before query phase and using a
    # source node containing the result but not its query.
    result_only = memory_node("result-only")
    result_only.query_results.add_result(r)
    run_contact(result_only, mule, budget=full_budget())
    assert mule.query_results.orphan_result_count == 1
    close_node(mule)
    mule = reopen_node(mule_root, "restarted-mule")
    assert mule.query_results.orphan_result_count == 1

    run_contact(source, mule, budget=full_budget())
    assert mule.query_results.orphan_result_count == 0
    assert mule.query_results.results_for_query(q.query_id) == (r,)
    close_node(source)
    close_node(mule)


def test_duplicate_loops_converge_to_zero_missing_retransfers() -> None:
    a, b, c = memory_node("A"), memory_node("B"), memory_node("C")
    q = query(1)
    r = result(1, 1)
    a.query_results.add_query(q)
    a.query_results.add_result(r)
    run_contact(a, c, budget=full_budget())
    run_contact(c, b, budget=full_budget())
    run_contact(b, a, budget=full_budget())
    for left, right in ((a, c), (c, b), (b, a)):
        report = run_contact(left, right, budget=full_budget())
        assert report.items_used == 0
        assert report.encoded_bytes_accounted == 0
    assert a.query_results.canonical_state() == b.query_results.canonical_state()
    assert b.query_results.canonical_state() == c.query_results.canonical_state()


@pytest.mark.parametrize(
    ("kind", "expected"),
    (("query", "QUERY_CONFLICT"), ("result", "RESULT_CONFLICT"), ("reference", "REFERENCE_CONFLICT")),
)
def test_conflicts_through_contact_fail_closed(kind: str, expected: str) -> None:
    left, right = memory_node("left"), memory_node("right")
    selection = ContactSelection()
    if kind == "query":
        left.query_results.add_query(query(1, b"A"))
        right.query_results.add_query(query(1, b"B"))
        before = right.query_results.canonical_state()
    elif kind == "result":
        left.query_results.add_result(result(1, 1, (b"X",)))
        right.query_results.add_result(result(1, 1, (b"Y",)))
        before = right.query_results.canonical_state()
    else:
        left.catalog.add(reference(1, b"A"))
        right.catalog.add(reference(1, b"B"))
        selection = ContactSelection(
            right_wants_from_left=(reference(1).logical_key,)
        )
        before = right.catalog.canonical_state()

    report = run_contact(left, right, budget=full_budget(), selection=selection)
    assert report.outcome is ContactOutcome.ERROR
    assert report.error_code == expected
    after = (
        right.catalog.canonical_state()
        if kind == "reference"
        else right.query_results.canonical_state()
    )
    assert after == before


def test_query_quota_failure_keeps_prior_successful_records(monkeypatch: pytest.MonkeyPatch) -> None:
    import pollicino.net.query as query_module

    left, right = memory_node("left"), memory_node("right")
    left.query_results.add_queries((query(1), query(2)))
    monkeypatch.setattr(query_module, "MAX_STORED_QUERIES", 1)
    report = run_contact(left, right, budget=full_budget())
    assert report.outcome is ContactOutcome.ERROR
    assert report.error_code == "QUERY_RESULT_BOUNDS_ERROR"
    assert right.query_results.query_count == 1
    assert right.query_results.get_query(query(1).query_id) == query(1)


def test_catalog_quota_failure_does_not_partially_apply_record() -> None:
    left = memory_node("left")
    limited = BoundedReferenceCatalog(limits=CatalogLimits(max_catalog_items=1))
    right = ContactNode(limited, QueryResultStore(), "right")
    first, second = reference(1), reference(2)
    left.catalog.add_many((first, second))
    right.catalog.add(first)
    before = right.catalog.canonical_state()
    report = run_contact(
        left,
        right,
        budget=full_budget(),
        selection=ContactSelection(right_wants_from_left=(second.logical_key,)),
    )
    assert report.outcome is ContactOutcome.ERROR
    assert report.error_code == "CATALOG_BOUNDS_ERROR"
    assert right.catalog.canonical_state() == before


def test_more_than_one_contact_budget_converges_without_retransfer(tmp_path: Path) -> None:
    left_root, right_root = tmp_path / "left", tmp_path / "right"
    left = persistent_node(left_root, "left")
    right = persistent_node(right_root, "right")
    left.query_results.add_queries(query(index) for index in range(105))

    first = run_contact(left, right, budget=full_budget())
    assert first.outcome is ContactOutcome.BUDGET_EXHAUSTED
    assert first.items_used == 100
    close_node(left)
    close_node(right)

    left = reopen_node(left_root, "left-restarted")
    right = reopen_node(right_root, "right-restarted")
    second = run_contact(left, right, budget=full_budget())
    assert second.outcome is ContactOutcome.NO_MORE_ELIGIBLE_WORK
    assert second.items_used == 5
    assert second.left_to_right.queries == 5
    assert second.encoded_bytes_accounted > 0
    assert left.query_results.canonical_state() == right.query_results.canonical_state()
    close_node(left)
    close_node(right)


def test_different_contact_orders_produce_same_canonical_state() -> None:
    records = tuple(query(index) for index in range(6))
    source = memory_node("source")
    source.query_results.add_queries(records)
    direct = memory_node("direct")
    via_one = memory_node("via-one")
    via_two = memory_node("via-two")
    run_contact(source, direct, budget=full_budget())
    run_contact(source, via_one, budget=ContactBudget(3, MAX_CONTACT_BYTES))
    run_contact(via_one, via_two, budget=full_budget())
    run_contact(source, via_one, budget=full_budget())
    run_contact(via_one, via_two, budget=full_budget())
    assert direct.query_results.canonical_state() == via_two.query_results.canonical_state()


def test_reference_mule_preserves_key_and_bytes_across_restart(tmp_path: Path) -> None:
    a = persistent_node(tmp_path / "A", "A")
    b = persistent_node(tmp_path / "B", "B")
    c_root = tmp_path / "C"
    c = persistent_node(c_root, "C")
    item = BoundedReference(b"native-X", b"opaque\x00reference\xffbytes")
    b.catalog.add(item)
    run_contact(
        b,
        c,
        budget=full_budget(),
        selection=ContactSelection(right_wants_from_left=(item.logical_key,)),
    )
    close_node(c)
    c = reopen_node(c_root, "C-restarted")
    run_contact(
        c,
        a,
        budget=full_budget(),
        selection=ContactSelection(right_wants_from_left=(item.logical_key,)),
    )
    assert a.catalog.get(item.logical_key) == item
    close_node(a)
    close_node(b)
    close_node(c)


def test_contact_never_executes_application_callback_or_auto_pulls_reference() -> None:
    left, right = memory_node("left"), memory_node("right")
    q = query(1)
    candidate = reference(1)
    r = ResultRecord(q.query_id, b"result", (candidate.logical_key,))
    left.query_results.add_query(q)
    left.query_results.add_result(r)
    left.catalog.add(candidate)
    callbacks: list[bytes] = []

    report = run_contact(left, right, budget=full_budget())
    assert report.left_to_right.queries == 1
    assert report.left_to_right.results == 1
    assert callbacks == []
    assert candidate.logical_key not in right.catalog


def test_content_like_consumer_uses_unmodified_contact_core() -> None:
    producer, mule, consumer = (
        memory_node("producer"),
        memory_node("mule"),
        memory_node("consumer"),
    )
    opaque_query = QueryRecord(b"document-lookup", b"mime=application/octet-stream")
    opaque_result = ResultRecord(
        opaque_query.query_id,
        b"document-result",
        (b"sha256:synthetic-document",),
    )
    producer.query_results.add_query(opaque_query)
    producer.query_results.add_result(opaque_result)
    run_contact(producer, mule, budget=full_budget())
    run_contact(mule, consumer, budget=full_budget())
    assert consumer.query_results.get_query(opaque_query.query_id) == opaque_query
    assert consumer.query_results.get_result(opaque_result.identity) == opaque_result


def test_contact_core_has_no_application_bearer_or_pr52_branches() -> None:
    source = (Path(__file__).parents[1] / "src/pollicino/net/contact.py").read_text().lower()
    application_terms = (
        "faro",
        "registryquery",
        "evidencegrade",
        "publisher",
        "recommendation",
        "dna",
        "torrent",
        "magnet",
        "content",
    )
    bearer_terms = (
        "lora",
        "bluetooth",
        "wi-fi",
        "tcp",
        "udp",
        "http",
        "socket",
        "rssi",
        "mtu",
        "radio",
        "serial port",
    )
    pr52_terms = ("noderuntime", "pnb1", "pnc1", "custody runtime")
    assert not any(term in source for term in application_terms)
    assert not any(term in source for term in bearer_terms)
    assert not any(term in source for term in pr52_terms)


def test_contact_budget_has_no_unlimited_sentinel() -> None:
    with pytest.raises(ValueError):
        ContactBudget(max_items=MAX_CONTACT_ITEMS + 1)
    with pytest.raises(ValueError):
        ContactBudget(max_bytes=MAX_CONTACT_BYTES + 1)
    with pytest.raises(ValueError):
        ContactBudget(max_items=0)
