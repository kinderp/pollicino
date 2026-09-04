from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pollicino.net.catalog import BoundedReference, BoundedReferenceCatalog
from pollicino.net.endpoint import IndependentEndpoint
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


@dataclass(slots=True)
class EndpointFixture:
    endpoint: IndependentEndpoint
    catalog: BoundedReferenceCatalog
    query_results: QueryResultStore

    def close(self) -> None:
        assert isinstance(self.catalog, PersistentBoundedReferenceCatalog)
        assert isinstance(self.query_results, PersistentQueryResultStore)
        self.catalog.close()
        self.query_results.close()


def memory_endpoint(label: str) -> EndpointFixture:
    catalog = BoundedReferenceCatalog()
    query_results = QueryResultStore()
    return EndpointFixture(
        IndependentEndpoint(catalog, query_results, label), catalog, query_results
    )


def persistent_endpoint(root: Path, label: str) -> EndpointFixture:
    root.mkdir()
    catalog = PersistentBoundedReferenceCatalog(root / "catalog")
    query_results = PersistentQueryResultStore(root / "query-result")
    return EndpointFixture(
        IndependentEndpoint(catalog, query_results, label), catalog, query_results
    )


def reopen_endpoint(root: Path, label: str) -> EndpointFixture:
    catalog = PersistentBoundedReferenceCatalog(root / "catalog")
    query_results = PersistentQueryResultStore(root / "query-result")
    return EndpointFixture(
        IndependentEndpoint(catalog, query_results, label), catalog, query_results
    )
