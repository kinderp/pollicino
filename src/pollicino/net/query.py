from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import struct
from typing import Callable, Iterable, Sequence

from .catalog import (
    BoundedReferenceCatalog,
    MAX_EXCHANGE_ITEMS,
    MAX_LOGICAL_KEY_BYTES,
)


MAX_QUERY_ID_BYTES = 128
MAX_QUERY_PAYLOAD_BYTES = 4096
MAX_RESULT_ID_BYTES = 128
MAX_RESULT_KEYS = MAX_EXCHANGE_ITEMS
MAX_STORED_QUERIES = 10_000
MAX_STORED_RESULTS = 10_000
MAX_RESULTS_PER_QUERY = 100
MAX_ORPHAN_RESULTS = 1_000
MAX_QUERY_RESULT_STATE_BYTES = 16 * 1024 * 1024
MAX_QUERY_EXCHANGE_ITEMS = MAX_EXCHANGE_ITEMS
# Canonical framing overhead is bounded separately from application payload.
MAX_QUERY_RESULT_ENCODED_BYTES = (
    MAX_QUERY_RESULT_STATE_BYTES
    + 53
    + (MAX_STORED_QUERIES * 6)
    + (MAX_STORED_RESULTS * (6 + (MAX_RESULT_KEYS * 2)))
)

LOCAL_QUERY_STATE_MAGIC = b"PRQ3"
LOCAL_QUERY_STATE_VERSION = 1
LOCAL_QUERY_STATE_FORMAT = "pollicino.local-query-result-state.v1"
LOCAL_QUERY_RECORD_FORMAT = "pollicino.local-opaque-query-record.v1"
LOCAL_RESULT_RECORD_FORMAT = "pollicino.local-catalog-key-result-record.v1"
_STATE_HEADER = struct.Struct(">4sBIIQ32s")
_QUERY_HEADER = struct.Struct(">HI")
_RESULT_HEADER = struct.Struct(">HHH")
_KEY_LENGTH = struct.Struct(">H")


class QueryResultBoundsError(ValueError):
    pass


class QueryConflictError(ValueError):
    def __init__(self, query_id: bytes) -> None:
        super().__init__("query identifier is already bound to different bytes")
        self.query_id = query_id


class ResultConflictError(ValueError):
    def __init__(self, query_id: bytes, result_id: bytes) -> None:
        super().__init__("result identifier is already bound to different keys")
        self.query_id = query_id
        self.result_id = result_id


class LocalResultKeyError(ValueError):
    pass


class QueryMutationResult(str, Enum):
    ADDED = "ADDED"
    NOOP_DUPLICATE = "NOOP_DUPLICATE"


def _require_bytes(name: str, value: bytes, maximum: int, *, empty: bool = False) -> None:
    if not isinstance(value, bytes):
        raise TypeError(f"{name} must be bytes")
    if not value and not empty:
        raise QueryResultBoundsError(f"{name} must not be empty")
    if len(value) > maximum:
        raise QueryResultBoundsError(f"{name} exceeds {maximum} bytes")


@dataclass(frozen=True, slots=True)
class QueryRecord:
    query_id: bytes
    opaque_query: bytes

    def __post_init__(self) -> None:
        _require_bytes("query_id", self.query_id, MAX_QUERY_ID_BYTES)
        _require_bytes("opaque_query", self.opaque_query, MAX_QUERY_PAYLOAD_BYTES)

    @property
    def payload_bytes(self) -> int:
        return len(self.query_id) + len(self.opaque_query)


@dataclass(frozen=True, slots=True, order=True)
class ResultIdentity:
    query_id: bytes
    result_id: bytes

    def __post_init__(self) -> None:
        _require_bytes("query_id", self.query_id, MAX_QUERY_ID_BYTES)
        _require_bytes("result_id", self.result_id, MAX_RESULT_ID_BYTES)


@dataclass(frozen=True, slots=True)
class ResultRecord:
    query_id: bytes
    result_id: bytes
    candidate_keys: tuple[bytes, ...]

    def __post_init__(self) -> None:
        _require_bytes("query_id", self.query_id, MAX_QUERY_ID_BYTES)
        _require_bytes("result_id", self.result_id, MAX_RESULT_ID_BYTES)
        if not isinstance(self.candidate_keys, tuple):
            raise TypeError("candidate_keys must be a tuple")
        if len(self.candidate_keys) > MAX_RESULT_KEYS:
            raise QueryResultBoundsError(
                f"candidate_keys exceeds {MAX_RESULT_KEYS} items"
            )
        for key in self.candidate_keys:
            _require_bytes("candidate_key", key, MAX_LOGICAL_KEY_BYTES)
        if len(set(self.candidate_keys)) != len(self.candidate_keys):
            raise ValueError("candidate_keys contains duplicate keys")
        object.__setattr__(self, "candidate_keys", tuple(sorted(self.candidate_keys)))

    @property
    def identity(self) -> ResultIdentity:
        return ResultIdentity(self.query_id, self.result_id)

    @property
    def payload_bytes(self) -> int:
        return (
            len(self.query_id)
            + len(self.result_id)
            + sum(len(key) for key in self.candidate_keys)
        )


@dataclass(frozen=True, slots=True)
class QueryExchangeResult:
    advertised_ids: tuple[bytes, ...]
    receiver_known_ids: tuple[bytes, ...]
    candidate_ids: tuple[bytes, ...]
    selected_ids: tuple[bytes, ...]
    pulled_records: tuple[QueryRecord, ...]
    mutation_results: tuple[QueryMutationResult, ...]


@dataclass(frozen=True, slots=True)
class ResultExchangeResult:
    advertised_ids: tuple[ResultIdentity, ...]
    receiver_known_ids: tuple[ResultIdentity, ...]
    candidate_ids: tuple[ResultIdentity, ...]
    selected_ids: tuple[ResultIdentity, ...]
    pulled_records: tuple[ResultRecord, ...]
    mutation_results: tuple[QueryMutationResult, ...]


class QueryResultStore:
    """Bounded state for opaque questions and catalog-key answers."""

    def __init__(self) -> None:
        self._queries: dict[bytes, bytes] = {}
        self._results: dict[ResultIdentity, tuple[bytes, ...]] = {}
        self._payload_bytes = 0

    def __len__(self) -> int:
        return len(self._queries) + len(self._results)

    @property
    def query_count(self) -> int:
        return len(self._queries)

    @property
    def result_count(self) -> int:
        return len(self._results)

    @property
    def orphan_result_count(self) -> int:
        return sum(
            1 for identity in self._results if identity.query_id not in self._queries
        )

    @property
    def payload_bytes(self) -> int:
        return self._payload_bytes

    def add_query(self, record: QueryRecord) -> QueryMutationResult:
        if not isinstance(record, QueryRecord):
            raise TypeError("record must be QueryRecord")
        previous = self._queries.get(record.query_id)
        if previous is not None:
            if previous != record.opaque_query:
                raise QueryConflictError(record.query_id)
            return QueryMutationResult.NOOP_DUPLICATE
        if len(self._queries) + 1 > MAX_STORED_QUERIES:
            raise QueryResultBoundsError("stored query quota exceeded")
        candidate_bytes = self._payload_bytes + record.payload_bytes
        if candidate_bytes > MAX_QUERY_RESULT_STATE_BYTES:
            raise QueryResultBoundsError("query/result byte quota exceeded")
        staged = dict(self._queries)
        staged[record.query_id] = record.opaque_query
        self._queries = staged
        self._payload_bytes = candidate_bytes
        return QueryMutationResult.ADDED

    def add_queries(
        self, records: Iterable[QueryRecord]
    ) -> tuple[QueryMutationResult, ...]:
        pending = tuple(records)
        staged = QueryResultStore.from_canonical_state(self.canonical_state())
        results = tuple(staged.add_query(record) for record in pending)
        self._queries = staged._queries
        self._results = staged._results
        self._payload_bytes = staged._payload_bytes
        return results

    def add_result(self, record: ResultRecord) -> QueryMutationResult:
        if not isinstance(record, ResultRecord):
            raise TypeError("record must be ResultRecord")
        previous = self._results.get(record.identity)
        if previous is not None:
            if previous != record.candidate_keys:
                raise ResultConflictError(record.query_id, record.result_id)
            return QueryMutationResult.NOOP_DUPLICATE
        if len(self._results) + 1 > MAX_STORED_RESULTS:
            raise QueryResultBoundsError("stored result quota exceeded")
        per_query = sum(
            1 for identity in self._results if identity.query_id == record.query_id
        )
        if per_query + 1 > MAX_RESULTS_PER_QUERY:
            raise QueryResultBoundsError("results-per-query quota exceeded")
        if record.query_id not in self._queries and self.orphan_result_count + 1 > MAX_ORPHAN_RESULTS:
            raise QueryResultBoundsError("orphan result quota exceeded")
        candidate_bytes = self._payload_bytes + record.payload_bytes
        if candidate_bytes > MAX_QUERY_RESULT_STATE_BYTES:
            raise QueryResultBoundsError("query/result byte quota exceeded")
        staged = dict(self._results)
        staged[record.identity] = record.candidate_keys
        self._results = staged
        self._payload_bytes = candidate_bytes
        return QueryMutationResult.ADDED

    def add_results(
        self, records: Iterable[ResultRecord]
    ) -> tuple[QueryMutationResult, ...]:
        pending = tuple(records)
        staged = QueryResultStore.from_canonical_state(self.canonical_state())
        results = tuple(staged.add_result(record) for record in pending)
        self._queries = staged._queries
        self._results = staged._results
        self._payload_bytes = staged._payload_bytes
        return results

    def create_local_result(
        self,
        *,
        query_id: bytes,
        result_id: bytes,
        candidate_keys: Iterable[bytes],
        catalog: BoundedReferenceCatalog,
    ) -> QueryMutationResult:
        if not isinstance(catalog, BoundedReferenceCatalog):
            raise TypeError("catalog must be BoundedReferenceCatalog")
        if query_id not in self._queries:
            raise LookupError("query is not present")
        record = ResultRecord(query_id, result_id, tuple(candidate_keys))
        missing = tuple(key for key in record.candidate_keys if key not in catalog)
        if missing:
            raise LocalResultKeyError("local result contains a key absent from catalog")
        return self.add_result(record)

    def get_query(self, query_id: bytes) -> QueryRecord:
        _require_bytes("query_id", query_id, MAX_QUERY_ID_BYTES)
        try:
            return QueryRecord(query_id, self._queries[query_id])
        except KeyError as exc:
            raise LookupError("query is not present") from exc

    def get_result(self, identity: ResultIdentity) -> ResultRecord:
        if not isinstance(identity, ResultIdentity):
            raise TypeError("identity must be ResultIdentity")
        try:
            return ResultRecord(
                identity.query_id, identity.result_id, self._results[identity]
            )
        except KeyError as exc:
            raise LookupError("result is not present") from exc

    def results_for_query(self, query_id: bytes) -> tuple[ResultRecord, ...]:
        self.get_query(query_id)
        return tuple(
            self.get_result(identity)
            for identity in sorted(self._results)
            if identity.query_id == query_id
        )

    def sorted_query_ids(
        self, *, offset: int = 0, limit: int | None = None
    ) -> tuple[bytes, ...]:
        start, end = _page_bounds(offset, limit)
        return tuple(sorted(self._queries)[start:end])

    def sorted_result_ids(
        self, *, offset: int = 0, limit: int | None = None
    ) -> tuple[ResultIdentity, ...]:
        start, end = _page_bounds(offset, limit)
        return tuple(sorted(self._results)[start:end])

    def canonical_state(self) -> bytes:
        body = bytearray()
        for query_id in sorted(self._queries):
            opaque = self._queries[query_id]
            body += _QUERY_HEADER.pack(len(query_id), len(opaque))
            body += query_id + opaque
        for identity in sorted(self._results):
            keys = self._results[identity]
            body += _RESULT_HEADER.pack(
                len(identity.query_id), len(identity.result_id), len(keys)
            )
            body += identity.query_id + identity.result_id
            for key in keys:
                body += _KEY_LENGTH.pack(len(key)) + key
        encoded_body = bytes(body)
        return _STATE_HEADER.pack(
            LOCAL_QUERY_STATE_MAGIC,
            LOCAL_QUERY_STATE_VERSION,
            len(self._queries),
            len(self._results),
            self._payload_bytes,
            hashlib.sha256(encoded_body).digest(),
        ) + encoded_body

    @property
    def state_digest(self) -> bytes:
        return hashlib.sha256(self.canonical_state()).digest()

    @classmethod
    def from_canonical_state(cls, data: bytes) -> QueryResultStore:
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        if len(data) > MAX_QUERY_RESULT_ENCODED_BYTES:
            raise QueryResultBoundsError("canonical query/result state exceeds encoded bound")
        if len(data) < _STATE_HEADER.size:
            raise ValueError("query state header is truncated")
        magic, version, query_count, result_count, payload_bytes, digest = _STATE_HEADER.unpack_from(data)
        if magic != LOCAL_QUERY_STATE_MAGIC:
            raise ValueError("invalid query state magic")
        if version != LOCAL_QUERY_STATE_VERSION:
            raise ValueError(f"unsupported query state version: {version}")
        if query_count > MAX_STORED_QUERIES or result_count > MAX_STORED_RESULTS:
            raise QueryResultBoundsError("declared query/result item quota exceeded")
        if payload_bytes > MAX_QUERY_RESULT_STATE_BYTES:
            raise QueryResultBoundsError("declared query/result byte quota exceeded")
        body = data[_STATE_HEADER.size :]
        if hashlib.sha256(body).digest() != digest:
            raise ValueError("query state body digest mismatch")
        store = cls()
        offset = 0
        queries: list[QueryRecord] = []
        seen_queries: set[bytes] = set()
        for _ in range(query_count):
            if offset + _QUERY_HEADER.size > len(body):
                raise ValueError("query entry header is truncated")
            id_length, query_length = _QUERY_HEADER.unpack_from(body, offset)
            offset += _QUERY_HEADER.size
            end = offset + id_length + query_length
            if end > len(body):
                raise ValueError("query entry is truncated")
            record = QueryRecord(
                body[offset : offset + id_length],
                body[offset + id_length : end],
            )
            if record.query_id in seen_queries:
                raise ValueError("query state contains duplicate query identifiers")
            seen_queries.add(record.query_id)
            queries.append(record)
            offset = end
        for query in queries:
            store.add_query(query)
        results: list[ResultRecord] = []
        seen_results: set[ResultIdentity] = set()
        for _ in range(result_count):
            if offset + _RESULT_HEADER.size > len(body):
                raise ValueError("result entry header is truncated")
            query_length, result_length, key_count = _RESULT_HEADER.unpack_from(body, offset)
            offset += _RESULT_HEADER.size
            if key_count > MAX_RESULT_KEYS:
                raise QueryResultBoundsError("declared result key quota exceeded")
            end = offset + query_length + result_length
            if end > len(body):
                raise ValueError("result identity is truncated")
            query_id = body[offset : offset + query_length]
            result_id = body[offset + query_length : end]
            offset = end
            keys: list[bytes] = []
            for _ in range(key_count):
                if offset + _KEY_LENGTH.size > len(body):
                    raise ValueError("result key length is truncated")
                key_length = _KEY_LENGTH.unpack_from(body, offset)[0]
                offset += _KEY_LENGTH.size
                end = offset + key_length
                if end > len(body):
                    raise ValueError("result key is truncated")
                keys.append(body[offset:end])
                offset = end
            record = ResultRecord(query_id, result_id, tuple(keys))
            if record.identity in seen_results:
                raise ValueError("query state contains duplicate result identifiers")
            seen_results.add(record.identity)
            results.append(record)
        for result in results:
            store.add_result(result)
        if offset != len(body):
            raise ValueError("query state contains trailing data")
        if store.payload_bytes != payload_bytes:
            raise ValueError("query state payload byte count mismatch")
        if store.canonical_state() != data:
            raise ValueError("query state is not canonically ordered")
        return store


QueryHandler = Callable[[bytes], Iterable[bytes]]


def evaluate_query(
    store: QueryResultStore,
    *,
    query_id: bytes,
    result_id: bytes,
    catalog: BoundedReferenceCatalog,
    handler: QueryHandler,
) -> QueryMutationResult:
    if not callable(handler):
        raise TypeError("handler must be callable")
    query = store.get_query(query_id)
    return store.create_local_result(
        query_id=query_id,
        result_id=result_id,
        candidate_keys=handler(query.opaque_query),
        catalog=catalog,
    )


def _page_bounds(offset: int, limit: int | None) -> tuple[int, int]:
    if type(offset) is not int or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    active = MAX_QUERY_EXCHANGE_ITEMS if limit is None else limit
    if type(active) is not int or not 1 <= active <= MAX_QUERY_EXCHANGE_ITEMS:
        raise QueryResultBoundsError(
            f"exchange page must contain at most {MAX_QUERY_EXCHANGE_ITEMS} items"
        )
    return offset, offset + active


def _exchange_query_ids(name: str, values: Sequence[bytes]) -> tuple[bytes, ...]:
    if not isinstance(values, (tuple, list)):
        raise TypeError(f"{name} must be a tuple or list")
    if len(values) > MAX_QUERY_EXCHANGE_ITEMS:
        raise QueryResultBoundsError(f"{name} exceeds exchange bound")
    for value in values:
        _require_bytes(name, value, MAX_QUERY_ID_BYTES)
    if len(set(values)) != len(values):
        raise ValueError(f"{name} contains duplicate identifiers")
    return tuple(sorted(values))


def _exchange_result_ids(
    name: str, values: Sequence[ResultIdentity]
) -> tuple[ResultIdentity, ...]:
    if not isinstance(values, (tuple, list)):
        raise TypeError(f"{name} must be a tuple or list")
    if len(values) > MAX_QUERY_EXCHANGE_ITEMS:
        raise QueryResultBoundsError(f"{name} exceeds exchange bound")
    if any(not isinstance(value, ResultIdentity) for value in values):
        raise TypeError(f"{name} values must be ResultIdentity")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} contains duplicate identifiers")
    return tuple(sorted(values))


def reconcile_queries(
    sender: QueryResultStore,
    receiver: QueryResultStore,
    *,
    advertised_ids: Sequence[bytes],
    selected_ids: Sequence[bytes] | None = None,
) -> QueryExchangeResult:
    advertised = _exchange_query_ids("advertised_ids", advertised_ids)
    if any(value not in sender._queries for value in advertised):
        raise LookupError("advertised query is absent at sender")
    known = tuple(value for value in advertised if value in receiver._queries)
    candidates = tuple(value for value in advertised if value not in receiver._queries)
    selected = candidates if selected_ids is None else _exchange_query_ids("selected_ids", selected_ids)
    if not set(selected).issubset(candidates):
        raise ValueError("selected query identifiers must be new candidates")
    records = tuple(sender.get_query(value) for value in selected)
    mutations = receiver.add_queries(records)
    return QueryExchangeResult(advertised, known, candidates, selected, records, mutations)


def reconcile_results(
    sender: QueryResultStore,
    receiver: QueryResultStore,
    *,
    advertised_ids: Sequence[ResultIdentity],
    selected_ids: Sequence[ResultIdentity] | None = None,
) -> ResultExchangeResult:
    advertised = _exchange_result_ids("advertised_ids", advertised_ids)
    if any(value not in sender._results for value in advertised):
        raise LookupError("advertised result is absent at sender")
    known = tuple(value for value in advertised if value in receiver._results)
    candidates = tuple(value for value in advertised if value not in receiver._results)
    selected = candidates if selected_ids is None else _exchange_result_ids("selected_ids", selected_ids)
    if not set(selected).issubset(candidates):
        raise ValueError("selected result identifiers must be new candidates")
    records = tuple(sender.get_result(value) for value in selected)
    mutations = receiver.add_results(records)
    return ResultExchangeResult(advertised, known, candidates, selected, records, mutations)
