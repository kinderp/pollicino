from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from pollicino.net.catalog import BoundedReference, BoundedReferenceCatalog
from pollicino.net.local_persistence import (
    AmbiguousDurableStateError,
    ConcurrentWriterError,
    FaultStage,
    PersistenceCorruptError,
    PersistenceIOError,
    PersistenceStatus,
    PersistenceUncertainCommitError,
    PersistenceVersionError,
    PersistentStoreFailStopError,
    encode_envelope,
)
from pollicino.net.persistent_query import (
    LOCAL_QUERY_PERSISTENCE_MAGIC,
    LOCAL_QUERY_PERSISTENCE_VERSION,
    PersistentQueryResultStore,
)
from pollicino.net.query import (
    MAX_QUERY_RESULT_ENCODED_BYTES,
    QueryConflictError,
    QueryMutationResult,
    QueryRecord,
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


def query(index: int) -> QueryRecord:
    return QueryRecord(key(index), f"opaque-{index}".encode())


def result(q: int, r: int, keys=()) -> ResultRecord:
    return ResultRecord(key(q), key(r), tuple(keys))


def catalog(*indices: int) -> BoundedReferenceCatalog:
    value = BoundedReferenceCatalog()
    value.add_many(BoundedReference(key(i), f"ref-{i}".encode()) for i in indices)
    return value


def slot(root: Path, generation: int) -> Path:
    return root / f"query-result.{generation % 2}.snapshot"


class InjectedFault(OSError):
    pass


def injector(target: FaultStage):
    def inject(stage: FaultStage) -> None:
        if stage is target:
            raise InjectedFault(stage.value)
    return inject


def test_no_state_and_clean_query_result_restart(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentQueryResultStore(root) as store:
        assert store.open_status is PersistenceStatus.NO_DURABLE_STATE
        store.add_query(query(1))
        store.add_result(result(1, 1, (key(9),)))
        expected = store.canonical_state()
    with PersistentQueryResultStore(root) as store:
        assert store.open_status is PersistenceStatus.LOADED_CURRENT_GENERATION
        assert store.canonical_state() == expected
        assert store.query_count == 1 and store.result_count == 1


def test_real_subprocess_restart(tmp_path: Path) -> None:
    root = tmp_path / "subprocess"
    src = Path(__file__).parents[1] / "src"
    environment = dict(os.environ, PYTHONPATH=str(src))
    writer = """
from pollicino.net.persistent_query import PersistentQueryResultStore
from pollicino.net.query import QueryRecord, ResultRecord
import sys
with PersistentQueryResultStore(sys.argv[1]) as s:
    s.add_query(QueryRecord(b'q', b'opaque'))
    s.add_result(ResultRecord(b'q', b'r', (b'unknown-key',)))
"""
    reader = """
from pollicino.net.persistent_query import PersistentQueryResultStore
from pollicino.net.query import ResultIdentity
import sys
with PersistentQueryResultStore(sys.argv[1]) as s:
    assert s.get_query(b'q').opaque_query == b'opaque'
    assert s.get_result(ResultIdentity(b'q', b'r')).candidate_keys == (b'unknown-key',)
"""
    subprocess.run([sys.executable, "-c", writer, str(root)], check=True, env=environment)
    subprocess.run([sys.executable, "-c", reader, str(root)], check=True, env=environment)


def test_duplicate_after_restart_does_not_rewrite(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentQueryResultStore(root) as store:
        store.add_query(query(1))
        generation = store.generation
    with PersistentQueryResultStore(root) as store:
        assert store.add_query(query(1)) is QueryMutationResult.NOOP_DUPLICATE
        assert store.generation == generation


def test_conflicts_after_restart_leave_memory_and_disk_unchanged(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentQueryResultStore(root) as store:
        store.add_query(query(1)); store.add_result(result(1, 1, (key(1),)))
    with PersistentQueryResultStore(root) as store:
        before = store.canonical_state(); generation = store.generation
        with pytest.raises(QueryConflictError):
            store.add_query(QueryRecord(key(1), b"changed"))
        with pytest.raises(ResultConflictError):
            store.add_result(result(1, 1, (key(2),)))
        assert store.canonical_state() == before and store.generation == generation
    with PersistentQueryResultStore(root) as store:
        assert store.canonical_state() == before


@pytest.mark.parametrize("stage", [
    FaultStage.BEFORE_TEMP_CREATE,
    FaultStage.DURING_WRITE,
    FaultStage.AFTER_WRITE_BEFORE_FILE_FSYNC,
    FaultStage.AFTER_FILE_FSYNC_BEFORE_REPLACE,
])
def test_pre_replace_fault_preserves_old_authority(tmp_path: Path, stage: FaultStage) -> None:
    root = tmp_path / stage.value
    with PersistentQueryResultStore(root) as initial:
        initial.add_query(query(1))
    with PersistentQueryResultStore(root, fault_injector=injector(stage)) as store:
        before = store.canonical_state()
        with pytest.raises(PersistenceIOError):
            store.add_query(query(2))
        assert store.usable and store.canonical_state() == before
    with PersistentQueryResultStore(root) as reopened:
        assert reopened.sorted_query_ids() == (key(1),)


@pytest.mark.parametrize("stage", [
    FaultStage.AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC,
    FaultStage.AFTER_DIRECTORY_FSYNC_BEFORE_MEMORY_SWAP,
])
def test_post_replace_is_fail_stop_then_reopen_resolves_authority(tmp_path: Path, stage: FaultStage) -> None:
    root = tmp_path / stage.value
    with PersistentQueryResultStore(root) as initial:
        initial.add_query(query(1))
    store = PersistentQueryResultStore(root, fault_injector=injector(stage))
    with pytest.raises(PersistenceUncertainCommitError):
        store.add_query(query(2))
    assert not store.usable
    with pytest.raises(PersistentStoreFailStopError):
        store.canonical_state()
    store.close()
    with PersistentQueryResultStore(root) as reopened:
        assert reopened.sorted_query_ids() == (key(1), key(2))


def test_orphan_temp_is_ignored(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentQueryResultStore(root) as store:
        store.add_query(query(1))
    (root / ".query-result.orphan.tmp").write_bytes(b"partial")
    with PersistentQueryResultStore(root) as reopened:
        assert reopened.get_query(key(1)) == query(1)


def test_previous_generation_recovery_is_explicit(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentQueryResultStore(root) as store:
        store.add_query(query(1))
        old = store.canonical_state()
        store.add_query(query(2))
    data = bytearray(slot(root, 2).read_bytes()); data[-1] ^= 1; slot(root, 2).write_bytes(data)
    with PersistentQueryResultStore(root) as recovered:
        assert recovered.open_status is PersistenceStatus.RECOVERED_PREVIOUS_GENERATION
        assert recovered.canonical_state() == old


def test_both_generations_corrupt_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentQueryResultStore(root) as store:
        store.add_query(query(1)); store.add_query(query(2))
    for path in root.glob("query-result.*.snapshot"):
        data = bytearray(path.read_bytes()); data[-1] ^= 1; path.write_bytes(data)
    with pytest.raises(PersistenceCorruptError):
        PersistentQueryResultStore(root)


def test_unsupported_persistence_version_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentQueryResultStore(root) as store:
        store.add_query(query(1))
    path = slot(root, 1); data = bytearray(path.read_bytes()); data[8] = 99; path.write_bytes(data)
    with pytest.raises(PersistenceVersionError):
        PersistentQueryResultStore(root)


def test_truncated_and_payload_corruption_fail_closed(tmp_path: Path) -> None:
    for name, mutate in (
        ("truncated", lambda raw: raw[:12]),
        ("corrupt", lambda raw: raw[:-1] + bytes((raw[-1] ^ 1,))),
    ):
        root = tmp_path / name
        with PersistentQueryResultStore(root) as store:
            store.add_query(query(1))
        path = slot(root, 1); path.write_bytes(mutate(path.read_bytes()))
        with pytest.raises(PersistenceCorruptError):
            PersistentQueryResultStore(root)


def test_ambiguous_same_generation_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "node"; root.mkdir()
    a, b = QueryResultStore(), QueryResultStore(); a.add_query(query(1)); b.add_query(query(2))
    for slot_index, payload in enumerate((a.canonical_state(), b.canonical_state())):
        (root / f"query-result.{slot_index}.snapshot").write_bytes(encode_envelope(
            magic=LOCAL_QUERY_PERSISTENCE_MAGIC,
            version=LOCAL_QUERY_PERSISTENCE_VERSION,
            generation=7,
            payload=payload,
            max_payload_bytes=MAX_QUERY_RESULT_ENCODED_BYTES,
        ))
    with pytest.raises(AmbiguousDurableStateError):
        PersistentQueryResultStore(root)


def test_second_writer_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "node"
    first = PersistentQueryResultStore(root)
    try:
        with pytest.raises(ConcurrentWriterError):
            PersistentQueryResultStore(root)
    finally:
        first.close()


def test_handler_reattaches_after_restart_and_is_not_persisted(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentQueryResultStore(root) as store:
        store.add_query(query(1))
    with PersistentQueryResultStore(root) as store:
        evaluate_query(
            store, query_id=key(1), result_id=b"late", catalog=catalog(7),
            handler=lambda opaque: (key(7),) if opaque == b"opaque-1" else (),
        )
    with PersistentQueryResultStore(root) as store:
        assert store.results_for_query(key(1))[0].candidate_keys == (key(7),)


def test_async_offline_requester_responder_and_restart(tmp_path: Path) -> None:
    roots = {name: tmp_path / name for name in "abc"}
    with PersistentQueryResultStore(roots["a"]) as a:
        a.add_query(query(1))
    with PersistentQueryResultStore(roots["a"]) as a, PersistentQueryResultStore(roots["b"]) as b:
        reconcile_queries(a, b, advertised_ids=a.sorted_query_ids())
        evaluate_query(b, query_id=key(1), result_id=b"b", catalog=catalog(1, 2), handler=lambda _: (key(1), key(2)))
    with PersistentQueryResultStore(roots["b"]) as b, PersistentQueryResultStore(roots["c"]) as c:
        reconcile_queries(b, c, advertised_ids=b.sorted_query_ids())
        evaluate_query(c, query_id=key(1), result_id=b"c", catalog=catalog(2, 3), handler=lambda _: (key(2), key(3)))
    with PersistentQueryResultStore(roots["a"]) as a, PersistentQueryResultStore(roots["b"]) as b, PersistentQueryResultStore(roots["c"]) as c:
        reconcile_results(b, a, advertised_ids=b.sorted_result_ids())
        reconcile_results(c, a, advertised_ids=c.sorted_result_ids())
        reconcile_results(a, b, advertised_ids=a.sorted_result_ids())
        reconcile_results(a, c, advertised_ids=a.sorted_result_ids())
        assert a.canonical_state() == b.canonical_state() == c.canonical_state()
        converged = a.canonical_state()
    with PersistentQueryResultStore(roots["a"]) as a, PersistentQueryResultStore(roots["b"]) as b, PersistentQueryResultStore(roots["c"]) as c:
        assert a.canonical_state() == b.canonical_state() == c.canonical_state() == converged


def test_result_before_query_survives_restart_then_correlates(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentQueryResultStore(root) as store:
        store.add_result(result(1, 1, (key(8),)))
        assert store.orphan_result_count == 1
    with PersistentQueryResultStore(root) as store:
        assert store.orphan_result_count == 1
        store.add_query(query(1))
    with PersistentQueryResultStore(root) as store:
        assert store.orphan_result_count == 0
        assert store.results_for_query(key(1))[0].candidate_keys == (key(8),)
