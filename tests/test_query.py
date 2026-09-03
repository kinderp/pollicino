from __future__ import annotations

import hashlib
from pathlib import Path
import struct

import pytest
import pollicino.net.query as query_module

from pollicino.net.catalog import BoundedReference, BoundedReferenceCatalog
from pollicino.net.query import (
    MAX_QUERY_EXCHANGE_ITEMS,
    MAX_QUERY_ID_BYTES,
    MAX_QUERY_PAYLOAD_BYTES,
    MAX_RESULT_ID_BYTES,
    MAX_RESULT_KEYS,
    LocalResultKeyError,
    QueryConflictError,
    QueryMutationResult,
    QueryRecord,
    QueryResultBoundsError,
    QueryResultStore,
    ResultConflictError,
    ResultIdentity,
    ResultRecord,
    evaluate_query,
    reconcile_queries,
    reconcile_results,
)


def key(index: int) -> bytes:
    return index.to_bytes(4, "big")


def query(index: int, payload: bytes | None = None) -> QueryRecord:
    return QueryRecord(key(index), payload or f"opaque-{index}".encode())


def result(query_index: int, result_index: int, keys=()) -> ResultRecord:
    return ResultRecord(key(query_index), key(result_index), tuple(keys))


def catalog(*indices: int) -> BoundedReferenceCatalog:
    value = BoundedReferenceCatalog()
    value.add_many(BoundedReference(key(i), f"ref-{i}".encode()) for i in indices)
    return value


def test_query_bounds_and_opaque_bytes() -> None:
    assert QueryRecord(b"q" * MAX_QUERY_ID_BYTES, b"x" * MAX_QUERY_PAYLOAD_BYTES)
    with pytest.raises(QueryResultBoundsError):
        QueryRecord(b"q" * (MAX_QUERY_ID_BYTES + 1), b"x")
    with pytest.raises(QueryResultBoundsError):
        QueryRecord(b"q", b"x" * (MAX_QUERY_PAYLOAD_BYTES + 1))
    with pytest.raises(TypeError):
        QueryRecord("q", b"x")  # type: ignore[arg-type]


def test_query_duplicate_and_conflict_are_atomic() -> None:
    store = QueryResultStore()
    record = query(1)
    assert store.add_query(record) is QueryMutationResult.ADDED
    before = store.canonical_state()
    assert store.add_query(record) is QueryMutationResult.NOOP_DUPLICATE
    assert store.canonical_state() == before
    with pytest.raises(QueryConflictError):
        store.add_query(query(1, b"different"))
    assert store.canonical_state() == before


def test_batch_query_failure_is_atomic() -> None:
    store = QueryResultStore()
    store.add_query(query(1))
    before = store.canonical_state()
    with pytest.raises(QueryConflictError):
        store.add_queries((query(2), query(1, b"conflict")))
    assert store.canonical_state() == before


def test_result_bounds_empty_and_canonical_key_order() -> None:
    assert ResultRecord(b"q", b"r", ()).candidate_keys == ()
    record = ResultRecord(b"q", b"r", (b"z", b"a"))
    assert record.candidate_keys == (b"a", b"z")
    assert ResultRecord(b"q", b"r" * (MAX_RESULT_ID_BYTES // 1), ())
    with pytest.raises(QueryResultBoundsError):
        ResultRecord(b"q", b"r" * (MAX_RESULT_ID_BYTES + 1), ())
    with pytest.raises(QueryResultBoundsError):
        ResultRecord(b"q", b"r", tuple(key(i) for i in range(MAX_RESULT_KEYS + 1)))
    with pytest.raises(ValueError, match="duplicate"):
        ResultRecord(b"q", b"r", (b"x", b"x"))


def test_result_duplicate_and_conflict_are_atomic() -> None:
    store = QueryResultStore()
    store.add_query(query(1))
    record = result(1, 1, (key(7),))
    assert store.add_result(record) is QueryMutationResult.ADDED
    before = store.canonical_state()
    assert store.add_result(record) is QueryMutationResult.NOOP_DUPLICATE
    with pytest.raises(ResultConflictError):
        store.add_result(result(1, 1, (key(8),)))
    assert store.canonical_state() == before


def test_batch_result_failure_is_atomic() -> None:
    store = QueryResultStore()
    store.add_query(query(1))
    store.add_result(result(1, 1, (key(1),)))
    before = store.canonical_state()
    with pytest.raises(ResultConflictError):
        store.add_results((result(1, 2), result(1, 1, (key(9),))))
    assert store.canonical_state() == before


def test_remote_unknown_key_is_accepted_without_catalog_mutation() -> None:
    store = QueryResultStore()
    store.add_query(query(1))
    local_catalog = catalog()
    store.add_result(result(1, 1, (key(99),)))
    assert store.results_for_query(key(1))[0].candidate_keys == (key(99),)
    assert len(local_catalog) == 0


def test_local_result_requires_known_catalog_keys() -> None:
    store = QueryResultStore()
    store.add_query(query(1))
    local_catalog = catalog(1)
    with pytest.raises(LocalResultKeyError):
        store.create_local_result(
            query_id=key(1), result_id=b"bad", candidate_keys=(key(2),), catalog=local_catalog
        )
    assert store.result_count == 0
    assert store.create_local_result(
        query_id=key(1), result_id=b"ok", candidate_keys=(key(1),), catalog=local_catalog
    ) is QueryMutationResult.ADDED


def test_handler_is_external_and_can_return_zero_matches() -> None:
    store = QueryResultStore()
    store.add_query(query(1))
    assert evaluate_query(
        store,
        query_id=key(1),
        result_id=b"zero",
        catalog=catalog(),
        handler=lambda opaque: () if opaque == b"opaque-1" else (key(1),),
    ) is QueryMutationResult.ADDED
    assert store.results_for_query(key(1))[0].candidate_keys == ()


def test_orphan_result_is_bounded_persistent_state_and_correlates_later() -> None:
    store = QueryResultStore()
    orphan = result(1, 1, (key(9),))
    store.add_result(orphan)
    assert store.orphan_result_count == 1
    with pytest.raises(LookupError):
        store.results_for_query(key(1))
    store.add_query(query(1))
    assert store.orphan_result_count == 0
    assert store.results_for_query(key(1)) == (orphan,)


def test_canonical_state_is_insertion_order_independent() -> None:
    a = QueryResultStore()
    b = QueryResultStore()
    for record in (query(2), query(1)):
        a.add_query(record)
    for record in (result(1, 2, (key(3),)), result(2, 1, (key(2), key(1)))):
        a.add_result(record)
    for record in (result(2, 1, (key(1), key(2))), result(1, 2, (key(3),))):
        b.add_result(record)
    for record in (query(1), query(2)):
        b.add_query(record)
    assert a.canonical_state() == b.canonical_state()
    assert a.state_digest == b.state_digest


def test_canonical_round_trip_and_corruption_fail_closed() -> None:
    store = QueryResultStore()
    store.add_query(query(1))
    store.add_result(result(1, 1, (key(3),)))
    encoded = store.canonical_state()
    assert QueryResultStore.from_canonical_state(encoded).canonical_state() == encoded
    corrupted = bytearray(encoded)
    corrupted[-1] ^= 1
    with pytest.raises(ValueError, match="digest"):
        QueryResultStore.from_canonical_state(bytes(corrupted))
    with pytest.raises(ValueError, match="truncated"):
        QueryResultStore.from_canonical_state(encoded[:10])


def test_duplicate_records_in_encoded_state_fail_closed() -> None:
    store = QueryResultStore(); store.add_query(query(1))
    encoded = store.canonical_state()
    header = struct.Struct(">4sBIIQ32s")
    magic, version, _, results, payload, _ = header.unpack_from(encoded)
    body = encoded[header.size:]
    doubled = body + body
    malformed = header.pack(
        magic, version, 2, results, payload,
        hashlib.sha256(doubled).digest(),
    ) + doubled
    with pytest.raises(ValueError, match="duplicate query"):
        QueryResultStore.from_canonical_state(malformed)


def test_aggregate_and_orphan_quotas_are_atomic(monkeypatch) -> None:
    monkeypatch.setattr(query_module, "MAX_ORPHAN_RESULTS", 2)
    store = QueryResultStore()
    store.add_results((result(1, 1), result(2, 1)))
    before = store.canonical_state()
    with pytest.raises(QueryResultBoundsError, match="orphan"):
        store.add_result(result(3, 1))
    assert store.canonical_state() == before

    monkeypatch.setattr(query_module, "MAX_QUERY_RESULT_STATE_BYTES", store.payload_bytes)
    with pytest.raises(QueryResultBoundsError, match="byte quota"):
        store.add_query(query(1))
    assert store.canonical_state() == before


def test_query_reconcile_selected_and_loop_deduplication() -> None:
    a, b, c = QueryResultStore(), QueryResultStore(), QueryResultStore()
    a.add_queries((query(1), query(2)))
    first = reconcile_queries(
        a, b, advertised_ids=a.sorted_query_ids(), selected_ids=(key(1),)
    )
    assert first.candidate_ids == (key(1), key(2))
    assert b.query_count == 1
    reconcile_queries(b, c, advertised_ids=b.sorted_query_ids())
    loop = reconcile_queries(c, a, advertised_ids=c.sorted_query_ids())
    assert loop.candidate_ids == ()
    assert len(a) == 2 and len(b) == 1 and len(c) == 1


def test_result_reconcile_selected_and_loop_deduplication() -> None:
    a, b, c = QueryResultStore(), QueryResultStore(), QueryResultStore()
    for store in (a, b, c):
        store.add_query(query(1))
    b.add_result(result(1, 1, (key(1),)))
    identity = ResultIdentity(key(1), key(1))
    reconcile_results(b, a, advertised_ids=(identity,))
    reconcile_results(a, c, advertised_ids=(identity,))
    loop = reconcile_results(c, b, advertised_ids=(identity,))
    assert loop.candidate_ids == ()
    assert all(store.result_count == 1 for store in (a, b, c))


def test_two_responder_delivery_order_converges_without_ranking() -> None:
    left, right = QueryResultStore(), QueryResultStore()
    for store in (left, right):
        store.add_query(query(1))
    rb = ResultRecord(key(1), b"responder-b", (key(1), key(2)))
    rc = ResultRecord(key(1), b"responder-c", (key(2), key(3)))
    left.add_results((rb, rc))
    right.add_results((rc, rb))
    assert left.canonical_state() == right.canonical_state()
    assert left.results_for_query(key(1)) == (rb, rc)


def test_exchange_bounds_are_native_d2_sized() -> None:
    sender, receiver = QueryResultStore(), QueryResultStore()
    records = tuple(QueryRecord(i.to_bytes(2, "big"), b"q") for i in range(MAX_QUERY_EXCHANGE_ITEMS + 1))
    sender.add_queries(records)
    with pytest.raises(QueryResultBoundsError, match="exchange"):
        reconcile_queries(sender, receiver, advertised_ids=sender.sorted_query_ids(limit=MAX_QUERY_EXCHANGE_ITEMS) + (records[-1].query_id,))


def test_content_like_consumer_uses_same_opaque_engine() -> None:
    store = QueryResultStore()
    content_query = QueryRecord(b"content-query-1", b"synthetic-tag=lawful-audio")
    store.add_query(content_query)
    local = catalog(5, 8)
    evaluate_query(
        store,
        query_id=content_query.query_id,
        result_id=b"content-result-1",
        catalog=local,
        handler=lambda opaque: (key(5),) if b"lawful-audio" in opaque else (),
    )
    assert store.results_for_query(content_query.query_id)[0].candidate_keys == (key(5),)


def test_query_core_has_no_application_semantic_branches() -> None:
    source = (Path(__file__).parents[1] / "src/pollicino/net/query.py").read_text().lower()
    forbidden = (
        "faro", "registryquery", "publisher", "evidence", "recommendation",
        "content", "torrent", "magnet", "dna", "topic",
    )
    assert not {word for word in forbidden if word in source}
