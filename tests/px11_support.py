from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pollicino.net.catalog import BoundedReferenceCatalog
from pollicino.net.fair_reconciliation import FairIndependentEndpoint
from pollicino.net.persistent_catalog import PersistentBoundedReferenceCatalog
from pollicino.net.persistent_query import PersistentQueryResultStore
from pollicino.net.query import QueryResultStore


@dataclass(slots=True)
class FairEndpointFixture:
    endpoint: FairIndependentEndpoint
    catalog: BoundedReferenceCatalog
    query_results: QueryResultStore

    def close(self) -> None:
        assert isinstance(self.catalog, PersistentBoundedReferenceCatalog)
        assert isinstance(self.query_results, PersistentQueryResultStore)
        self.catalog.close()
        self.query_results.close()


def fair_memory_endpoint(label: str) -> FairEndpointFixture:
    catalog = BoundedReferenceCatalog()
    query_results = QueryResultStore()
    return FairEndpointFixture(
        FairIndependentEndpoint(catalog, query_results, label),
        catalog,
        query_results,
    )


def fair_persistent_endpoint(root: Path, label: str) -> FairEndpointFixture:
    root.mkdir()
    catalog = PersistentBoundedReferenceCatalog(root / "catalog")
    query_results = PersistentQueryResultStore(root / "query-result")
    return FairEndpointFixture(
        FairIndependentEndpoint(catalog, query_results, label),
        catalog,
        query_results,
    )


def reopen_fair_endpoint(root: Path, label: str) -> FairEndpointFixture:
    catalog = PersistentBoundedReferenceCatalog(root / "catalog")
    query_results = PersistentQueryResultStore(root / "query-result")
    return FairEndpointFixture(
        FairIndependentEndpoint(catalog, query_results, label),
        catalog,
        query_results,
    )
