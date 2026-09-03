from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .catalog import BoundedReferenceCatalog
from .local_persistence import (
    DualGenerationSnapshotStore,
    FaultInjector,
    PersistenceBoundsError,
    PersistenceCorruptError,
    PersistenceStatus,
)
from .query import (
    MAX_QUERY_RESULT_ENCODED_BYTES,
    QueryMutationResult,
    QueryRecord,
    QueryResultBoundsError,
    QueryResultStore,
    ResultIdentity,
    ResultRecord,
)


LOCAL_QUERY_PERSISTENCE_MAGIC = b"PRQD3ST1"
LOCAL_QUERY_PERSISTENCE_VERSION = 1
LOCAL_QUERY_PERSISTENCE_FORMAT = "pollicino.local-persistent-query-result.v1"


def _decode_query_payload(payload: bytes) -> QueryResultStore:
    try:
        return QueryResultStore.from_canonical_state(payload)
    except QueryResultBoundsError as exc:
        raise PersistenceBoundsError(
            "query/result bounds rejected durable payload"
        ) from exc
    except (TypeError, ValueError) as exc:
        raise PersistenceCorruptError(
            "query/result codec rejected durable payload"
        ) from exc


class PersistentQueryResultStore(QueryResultStore):
    """Persistent D3 state using PX5's dual-generation durability primitive."""

    def __init__(
        self,
        directory: Path | str,
        *,
        fault_injector: FaultInjector | None = None,
    ) -> None:
        super().__init__()
        self._durable = DualGenerationSnapshotStore[QueryResultStore](
            directory,
            stem="query-result",
            magic=LOCAL_QUERY_PERSISTENCE_MAGIC,
            version=LOCAL_QUERY_PERSISTENCE_VERSION,
            max_payload_bytes=MAX_QUERY_RESULT_ENCODED_BYTES,
            decode_payload=_decode_query_payload,
            fault_injector=fault_injector,
        )
        loaded = self._durable.value
        if loaded is not None:
            self._load_into_memory(loaded)

    @property
    def directory(self) -> Path:
        return self._durable.directory

    @property
    def generation(self) -> int:
        return self._durable.generation

    @property
    def open_status(self) -> PersistenceStatus:
        return self._durable.open_status

    @property
    def last_persistence_status(self) -> PersistenceStatus:
        return self._durable.last_status

    @property
    def usable(self) -> bool:
        return self._durable.usable

    def close(self) -> None:
        self._durable.close()

    def __enter__(self) -> PersistentQueryResultStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _ensure_usable(self) -> None:
        self._durable.ensure_usable()

    def _load_into_memory(self, store: QueryResultStore) -> None:
        for query_id in store.sorted_query_ids():
            QueryResultStore.add_query(self, store.get_query(query_id))
        for identity in store.sorted_result_ids():
            QueryResultStore.add_result(self, store.get_result(identity))

    def _staged_clone(self) -> QueryResultStore:
        return QueryResultStore.from_canonical_state(
            QueryResultStore.canonical_state(self)
        )

    def add_query(self, record: QueryRecord) -> QueryMutationResult:
        return self.add_queries((record,))[0]

    def add_queries(
        self, records: Iterable[QueryRecord]
    ) -> tuple[QueryMutationResult, ...]:
        self._ensure_usable()
        pending = tuple(records)
        candidate = self._staged_clone()
        results = candidate.add_queries(pending)
        if not any(result is QueryMutationResult.ADDED for result in results):
            return results
        self._durable.commit(candidate.canonical_state())
        QueryResultStore.add_queries(self, pending)
        return results

    def add_result(self, record: ResultRecord) -> QueryMutationResult:
        return self.add_results((record,))[0]

    def add_results(
        self, records: Iterable[ResultRecord]
    ) -> tuple[QueryMutationResult, ...]:
        self._ensure_usable()
        pending = tuple(records)
        candidate = self._staged_clone()
        results = candidate.add_results(pending)
        if not any(result is QueryMutationResult.ADDED for result in results):
            return results
        self._durable.commit(candidate.canonical_state())
        QueryResultStore.add_results(self, pending)
        return results

    def create_local_result(
        self,
        *,
        query_id: bytes,
        result_id: bytes,
        candidate_keys: Iterable[bytes],
        catalog: BoundedReferenceCatalog,
    ) -> QueryMutationResult:
        self._ensure_usable()
        return super().create_local_result(
            query_id=query_id,
            result_id=result_id,
            candidate_keys=candidate_keys,
            catalog=catalog,
        )

    def __len__(self) -> int:
        self._ensure_usable()
        return super().__len__()

    @property
    def query_count(self) -> int:
        self._ensure_usable()
        return super().query_count

    @property
    def result_count(self) -> int:
        self._ensure_usable()
        return super().result_count

    @property
    def orphan_result_count(self) -> int:
        self._ensure_usable()
        return super().orphan_result_count

    @property
    def payload_bytes(self) -> int:
        self._ensure_usable()
        return super().payload_bytes

    def get_query(self, query_id: bytes) -> QueryRecord:
        self._ensure_usable()
        return super().get_query(query_id)

    def get_result(self, identity: ResultIdentity) -> ResultRecord:
        self._ensure_usable()
        return super().get_result(identity)

    def results_for_query(self, query_id: bytes) -> tuple[ResultRecord, ...]:
        self._ensure_usable()
        return super().results_for_query(query_id)

    def sorted_query_ids(
        self, *, offset: int = 0, limit: int | None = None
    ) -> tuple[bytes, ...]:
        self._ensure_usable()
        return super().sorted_query_ids(offset=offset, limit=limit)

    def sorted_result_ids(
        self, *, offset: int = 0, limit: int | None = None
    ) -> tuple[ResultIdentity, ...]:
        self._ensure_usable()
        return super().sorted_result_ids(offset=offset, limit=limit)

    def canonical_state(self) -> bytes:
        self._ensure_usable()
        return super().canonical_state()

    @property
    def state_digest(self) -> bytes:
        self._ensure_usable()
        return super().state_digest
