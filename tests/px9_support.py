from __future__ import annotations

from pathlib import Path

from pollicino.net.catalog import BoundedReference, BoundedReferenceCatalog
from pollicino.net.contact import (
    MAX_CONTACT_BYTES,
    MAX_CONTACT_ITEMS,
    ContactBudget,
    ContactNode,
)
from pollicino.net.persistent_catalog import PersistentBoundedReferenceCatalog
from pollicino.net.persistent_query import PersistentQueryResultStore
from pollicino.net.query import QueryRecord, QueryResultStore, ResultRecord


def query(index: int, payload: bytes | None = None) -> QueryRecord:
    query_id = index.to_bytes(4, "big")
    return QueryRecord(
        query_id,
        payload if payload is not None else b"opaque-query-" + query_id,
    )


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
    return BoundedReference(key, value if value is not None else b"opaque-ref-" + key)


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
    return ContactBudget(MAX_CONTACT_ITEMS, MAX_CONTACT_BYTES)
