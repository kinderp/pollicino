from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys

import pytest

from pollicino.net.catalog import (
    BoundedReference,
    BoundedReferenceCatalog,
    CatalogBoundsError,
    CatalogLimits,
    MutationResult,
)
from pollicino.net.persistent_catalog import (
    AmbiguousDurableStateError,
    ConcurrentWriterError,
    FaultStage,
    LOCAL_PERSISTENCE_FORMAT,
    LOCAL_PERSISTENCE_MAGIC,
    LOCAL_PERSISTENCE_VERSION,
    PersistenceBoundsError,
    PersistenceCorruptError,
    PersistenceDigestError,
    PersistenceIOError,
    PersistenceStatus,
    PersistenceTruncatedError,
    PersistenceUncertainCommitError,
    PersistenceVersionError,
    PersistentBoundedReferenceCatalog,
    PersistentCatalogFailStopError,
    _HEADER,
    _PREFIX,
    _encode_snapshot,
    persist_reconcile_and_pull,
)


def entry(index: int, size: int = 16) -> BoundedReference:
    key = index.to_bytes(4, "big")
    seed = hashlib.sha256(f"persistent-reference-{index}".encode()).digest()
    return BoundedReference(key, (seed * ((size // len(seed)) + 1))[:size])


def snapshot_paths(root: Path) -> list[Path]:
    return sorted(root.glob("catalog.*.snapshot"))


def generation_path(root: Path, generation: int) -> Path:
    return root / f"catalog.{generation % 2}.snapshot"


def write_native_state(
    root: Path,
    *,
    generation: int,
    key: bytes,
    reference: bytes,
    declared_items: int = 1,
    declared_payload: int | None = None,
) -> None:
    entry_header = struct.Struct(">HI")
    state_header = struct.Struct(">4sBIQ32s")
    body = entry_header.pack(len(key), len(reference)) + key + reference
    payload_count = len(key) + len(reference) if declared_payload is None else declared_payload
    native = state_header.pack(
        b"PRCS", 1, declared_items, payload_count, hashlib.sha256(body).digest()
    ) + body
    data = _encode_snapshot(generation, native, CatalogLimits())
    generation_path(root, generation).write_bytes(data)


def corrupt(path: Path, offset: int) -> None:
    data = bytearray(path.read_bytes())
    data[offset] ^= 0x01
    path.write_bytes(data)


class InjectedFault(OSError):
    pass


def injector(target: FaultStage):
    def inject(stage: FaultStage) -> None:
        if stage is target:
            raise InjectedFault(stage.value)

    return inject


def test_01_no_state_initializes_empty_explicitly(tmp_path: Path) -> None:
    with PersistentBoundedReferenceCatalog(tmp_path / "node") as catalog:
        assert catalog.open_status is PersistenceStatus.NO_DURABLE_STATE
        assert len(catalog) == 0
        assert catalog.generation == 0


def test_02_first_insert_is_durable_and_permissions_are_conservative(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog:
        assert catalog.add(entry(1)) is MutationResult.ADDED
        assert catalog.generation == 1
        assert catalog.last_persistence_status is PersistenceStatus.PERSIST_COMMITTED
    path = generation_path(root, 1)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(root.stat().st_mode) == 0o700


def test_03_clean_restart_restores_exact_native_state(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as first:
        first.add_many((entry(2), entry(1)))
        expected = first.canonical_state()
    with PersistentBoundedReferenceCatalog(root) as second:
        assert second.open_status is PersistenceStatus.LOADED_CURRENT_GENERATION
        assert second.canonical_state() == expected


def test_04_real_subprocess_restart(tmp_path: Path) -> None:
    root = tmp_path / "node"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    write = """
from pathlib import Path
from pollicino.net.catalog import BoundedReference
from pollicino.net.persistent_catalog import PersistentBoundedReferenceCatalog
import sys
with PersistentBoundedReferenceCatalog(Path(sys.argv[1])) as c:
    c.add(BoundedReference(b'process-key', b'process-reference'))
    print(c.canonical_state().hex())
"""
    read = """
from pathlib import Path
from pollicino.net.persistent_catalog import PersistentBoundedReferenceCatalog
import sys
with PersistentBoundedReferenceCatalog(Path(sys.argv[1])) as c:
    print(c.canonical_state().hex())
"""
    first = subprocess.run([sys.executable, "-c", write, str(root)], env=env, check=True, text=True, capture_output=True)
    second = subprocess.run([sys.executable, "-c", read, str(root)], env=env, check=True, text=True, capture_output=True)
    assert first.stdout == second.stdout


def test_05_duplicate_after_restart_is_noop_without_generation(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog:
        catalog.add(entry(1))
    before = generation_path(root, 1).read_bytes()
    with PersistentBoundedReferenceCatalog(root) as catalog:
        assert catalog.add(entry(1)) is MutationResult.NOOP_DUPLICATE
        assert catalog.generation == 1
    assert generation_path(root, 1).read_bytes() == before


def test_06_conflict_after_restart_is_atomic(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog:
        catalog.add(entry(1))
    before = generation_path(root, 1).read_bytes()
    with PersistentBoundedReferenceCatalog(root) as catalog:
        with pytest.raises(ValueError, match="different reference"):
            catalog.add(BoundedReference(entry(1).logical_key, b"different"))
        assert catalog.get(entry(1).logical_key) == entry(1)
    assert generation_path(root, 1).read_bytes() == before


def test_07_item_quota_survives_restart(tmp_path: Path) -> None:
    root = tmp_path / "node"
    limits = CatalogLimits(max_catalog_items=1)
    with PersistentBoundedReferenceCatalog(root, limits=limits) as catalog:
        catalog.add(entry(1))
    with PersistentBoundedReferenceCatalog(root, limits=limits) as catalog:
        with pytest.raises(CatalogBoundsError, match="item quota"):
            catalog.add(entry(2))
        assert len(catalog) == 1


def test_08_byte_quota_survives_restart(tmp_path: Path) -> None:
    root = tmp_path / "node"
    first = entry(1, 12)
    limits = CatalogLimits(max_catalog_bytes=first.payload_bytes)
    with PersistentBoundedReferenceCatalog(root, limits=limits) as catalog:
        catalog.add(first)
    with PersistentBoundedReferenceCatalog(root, limits=limits) as catalog:
        with pytest.raises(CatalogBoundsError, match="byte quota"):
            catalog.add(entry(2, 1))
        assert catalog.payload_bytes == first.payload_bytes


def test_09_exchange_semantics_survive_restart(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog:
        catalog.add_many((entry(1), entry(2)))
    with PersistentBoundedReferenceCatalog(root) as catalog:
        assert catalog.receiver_known_ids((entry(3).logical_key, entry(1).logical_key)) == (entry(1).logical_key,)


def test_10_persisted_payload_is_native_canonical_state(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog:
        catalog.add(entry(1))
        expected = catalog.canonical_state()
    raw = generation_path(root, 1).read_bytes()
    assert raw[_HEADER.size :] == expected


def test_11_generation_history_does_not_change_catalog_identity(tmp_path: Path) -> None:
    roots = (tmp_path / "a", tmp_path / "b")
    with PersistentBoundedReferenceCatalog(roots[0]) as a:
        a.add(entry(1)); a.add(entry(2)); a.remove(entry(2).logical_key)
        state_a = a.canonical_state()
    with PersistentBoundedReferenceCatalog(roots[1]) as b:
        b.add(entry(1)); state_b = b.canonical_state()
    assert state_a == state_b


def test_12_failed_native_mutation_does_not_touch_disk(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog:
        catalog.add(entry(1)); before = generation_path(root, 1).read_bytes()
        with pytest.raises(ValueError):
            catalog.add(BoundedReference(entry(1).logical_key, b"x"))
        assert generation_path(root, 1).read_bytes() == before


@pytest.mark.parametrize("stage", [
    FaultStage.BEFORE_TEMP_CREATE,
    FaultStage.DURING_WRITE,
    FaultStage.AFTER_WRITE_BEFORE_FILE_FSYNC,
    FaultStage.AFTER_FILE_FSYNC_BEFORE_REPLACE,
])
def test_13_to_16_pre_replace_faults_preserve_authority(tmp_path: Path, stage: FaultStage) -> None:
    root = tmp_path / stage.value
    with PersistentBoundedReferenceCatalog(root) as initial:
        initial.add(entry(1))
    with PersistentBoundedReferenceCatalog(root, fault_injector=injector(stage)) as catalog:
        before = catalog.canonical_state()
        with pytest.raises(PersistenceIOError):
            catalog.add(entry(2))
        assert catalog.usable
        assert catalog.canonical_state() == before
    with PersistentBoundedReferenceCatalog(root) as reopened:
        assert len(reopened) == 1


def test_17_orphan_temp_is_ignored(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog:
        catalog.add(entry(1))
    (root / ".catalog.snapshot.orphan.tmp").write_bytes(b"partial")
    with PersistentBoundedReferenceCatalog(root) as reopened:
        assert reopened.get(entry(1).logical_key) == entry(1)


@pytest.mark.parametrize("stage", [
    FaultStage.AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC,
    FaultStage.AFTER_DIRECTORY_FSYNC_BEFORE_MEMORY_SWAP,
])
def test_18_to_19_post_replace_faults_fail_stop_then_reopen(tmp_path: Path, stage: FaultStage) -> None:
    root = tmp_path / stage.value
    with PersistentBoundedReferenceCatalog(root) as initial:
        initial.add(entry(1))
    catalog = PersistentBoundedReferenceCatalog(root, fault_injector=injector(stage))
    with pytest.raises(PersistenceUncertainCommitError) as raised:
        catalog.add(entry(2))
    assert raised.value.replacement_completed
    assert not catalog.usable
    with pytest.raises(PersistentCatalogFailStopError):
        catalog.get(entry(1).logical_key)
    catalog.close()
    with PersistentBoundedReferenceCatalog(root) as reopened:
        assert reopened.get(entry(2).logical_key) == entry(2)


@pytest.mark.parametrize("cut", [1, _HEADER.size - 1, _HEADER.size + 3])
def test_20_to_22_truncation_fails_closed(tmp_path: Path, cut: int) -> None:
    root = tmp_path / str(cut)
    with PersistentBoundedReferenceCatalog(root) as catalog:
        catalog.add(entry(1))
    path = generation_path(root, 1)
    path.write_bytes(path.read_bytes()[:cut])
    with pytest.raises(PersistenceTruncatedError):
        PersistentBoundedReferenceCatalog(root)


def test_23_corrupt_magic_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog: catalog.add(entry(1))
    corrupt(generation_path(root, 1), 0)
    with pytest.raises(PersistenceCorruptError): PersistentBoundedReferenceCatalog(root)


def test_24_unsupported_version_is_distinct(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog: catalog.add(entry(1))
    path = generation_path(root, 1); data = bytearray(path.read_bytes()); data[8] = 99; path.write_bytes(data)
    with pytest.raises(PersistenceVersionError): PersistentBoundedReferenceCatalog(root)


def test_25_corrupt_payload_digest_is_detected(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog: catalog.add(entry(1))
    corrupt(generation_path(root, 1), _HEADER.size)
    with pytest.raises(PersistenceDigestError): PersistentBoundedReferenceCatalog(root)


def test_26_corrupt_digest_is_detected(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog: catalog.add(entry(1))
    corrupt(generation_path(root, 1), _PREFIX.size)
    with pytest.raises(PersistenceDigestError): PersistentBoundedReferenceCatalog(root)


def test_corrupt_generation_is_digest_protected(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog:
        catalog.add(entry(1))
    corrupt(generation_path(root, 1), 9)
    with pytest.raises(PersistenceDigestError):
        PersistentBoundedReferenceCatalog(root)


def test_27_declared_envelope_bound_fails_before_payload(tmp_path: Path) -> None:
    root = tmp_path / "node"; root.mkdir()
    prefix = _PREFIX.pack(LOCAL_PERSISTENCE_MAGIC, LOCAL_PERSISTENCE_VERSION, 1, 20_000_000)
    generation_path(root, 1).write_bytes(prefix + b"x" * 32)
    with pytest.raises(PersistenceBoundsError): PersistentBoundedReferenceCatalog(root)


def test_28_oversized_persisted_key_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "node"; root.mkdir()
    write_native_state(root, generation=1, key=b"k" * 257, reference=b"r")
    with pytest.raises(PersistenceBoundsError): PersistentBoundedReferenceCatalog(root)


def test_29_oversized_persisted_reference_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "node"; root.mkdir()
    write_native_state(root, generation=1, key=b"k", reference=b"r" * 4097)
    with pytest.raises(PersistenceBoundsError): PersistentBoundedReferenceCatalog(root)


def test_30_oversized_declared_catalog_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "node"; root.mkdir()
    write_native_state(root, generation=1, key=b"k", reference=b"r", declared_items=10_001)
    with pytest.raises(PersistenceBoundsError): PersistentBoundedReferenceCatalog(root)


def test_31_previous_generation_recovery_is_explicit(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog:
        catalog.add(entry(1)); catalog.add(entry(2))
    corrupt(generation_path(root, 2), _HEADER.size)
    with PersistentBoundedReferenceCatalog(root) as recovered:
        assert recovered.open_status is PersistenceStatus.RECOVERED_PREVIOUS_GENERATION
        assert recovered.generation == 1
        assert len(recovered) == 1


def test_32_both_generations_corrupt_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog:
        catalog.add(entry(1)); catalog.add(entry(2))
    for path in snapshot_paths(root): corrupt(path, _HEADER.size)
    with pytest.raises(PersistenceCorruptError): PersistentBoundedReferenceCatalog(root)


def test_33_same_generation_different_valid_payload_is_ambiguous(tmp_path: Path) -> None:
    root = tmp_path / "node"; root.mkdir()
    one = BoundedReferenceCatalog(); one.add(entry(1))
    two = BoundedReferenceCatalog(); two.add(entry(2))
    (root / "catalog.0.snapshot").write_bytes(_encode_snapshot(7, one.canonical_state(), one.limits))
    (root / "catalog.1.snapshot").write_bytes(_encode_snapshot(7, two.canonical_state(), two.limits))
    with pytest.raises(AmbiguousDurableStateError): PersistentBoundedReferenceCatalog(root)


def test_34_generations_increase_only_on_durable_change(tmp_path: Path) -> None:
    with PersistentBoundedReferenceCatalog(tmp_path / "node") as catalog:
        catalog.add(entry(1)); assert catalog.generation == 1
        catalog.add(entry(1)); assert catalog.generation == 1
        with pytest.raises(ValueError): catalog.add(BoundedReference(entry(1).logical_key, b"x"))
        assert catalog.generation == 1
        catalog.add(entry(2)); assert catalog.generation == 2


def test_35_remove_persists_without_content_deletion_semantics(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog:
        catalog.add(entry(1)); assert catalog.remove(entry(1).logical_key) == entry(1)
    with PersistentBoundedReferenceCatalog(root) as reopened: assert len(reopened) == 0


def test_36_second_writer_fails_safely_and_crash_releases_lock(tmp_path: Path) -> None:
    root = tmp_path / "node"
    first = PersistentBoundedReferenceCatalog(root)
    with pytest.raises(ConcurrentWriterError): PersistentBoundedReferenceCatalog(root)
    first.close()
    with PersistentBoundedReferenceCatalog(root) as second: assert second.usable


def test_37_stale_lock_file_is_not_a_stale_lock(tmp_path: Path) -> None:
    root = tmp_path / "node"; root.mkdir(); (root / "catalog.lock").write_text("stale")
    with PersistentBoundedReferenceCatalog(root) as catalog: assert catalog.usable


def test_38_symlink_directory_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target"; target.mkdir(); link = tmp_path / "link"; link.symlink_to(target)
    with pytest.raises(PersistenceIOError): PersistentBoundedReferenceCatalog(link)


def test_39_non_directory_target_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "file"; path.write_text("x")
    with pytest.raises(PersistenceIOError): PersistentBoundedReferenceCatalog(path)


def test_40_missing_parent_fails_explicitly(tmp_path: Path) -> None:
    with pytest.raises(PersistenceIOError): PersistentBoundedReferenceCatalog(tmp_path / "missing" / "node")


def test_41_snapshot_symlink_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "node"; root.mkdir(); target = tmp_path / "other"; target.write_bytes(b"x")
    (root / "catalog.1.snapshot").symlink_to(target)
    with pytest.raises(PersistenceIOError): PersistentBoundedReferenceCatalog(root)


def test_42_three_nodes_restart_then_reconcile_and_converge(tmp_path: Path) -> None:
    roots = [tmp_path / name for name in "abc"]
    initial = ((entry(1), entry(2)), (entry(2), entry(3)), (entry(3), entry(4)))
    for root, entries in zip(roots, initial, strict=True):
        with PersistentBoundedReferenceCatalog(root) as catalog: catalog.add_many(entries)
    nodes = [PersistentBoundedReferenceCatalog(root) for root in roots]
    try:
        for sender, receiver in ((nodes[0], nodes[1]), (nodes[1], nodes[0]), (nodes[1], nodes[2]), (nodes[2], nodes[1]), (nodes[0], nodes[2]), (nodes[2], nodes[0])):
            advertised = sender.sorted_logical_ids(limit=100)
            persist_reconcile_and_pull(sender, receiver, advertised_keys=advertised)
        assert len({node.canonical_state() for node in nodes}) == 1
    finally:
        for node in nodes: node.close()
    for root in roots:
        with PersistentBoundedReferenceCatalog(root) as restarted: assert len(restarted) == 4


def test_43_selected_pull_after_restart_is_application_owned(tmp_path: Path) -> None:
    with PersistentBoundedReferenceCatalog(tmp_path / "a") as initial:
        initial.add_many((entry(1), entry(2)))
    with PersistentBoundedReferenceCatalog(tmp_path / "a") as sender, PersistentBoundedReferenceCatalog(tmp_path / "b") as receiver:
        result = persist_reconcile_and_pull(sender, receiver, advertised_keys=sender.sorted_logical_ids(), selected_keys=(entry(2).logical_key,))
        assert result.selected_keys == (entry(2).logical_key,)
        assert len(receiver) == 1


def test_44_paths_and_restart_history_are_not_payload_identity(tmp_path: Path) -> None:
    with PersistentBoundedReferenceCatalog(tmp_path / "a") as a: a.add(entry(1)); expected = a.canonical_state()
    with PersistentBoundedReferenceCatalog(tmp_path / "b") as b: b.add(entry(1)); assert b.canonical_state() == expected
    with PersistentBoundedReferenceCatalog(tmp_path / "a") as a2: assert a2.canonical_state() == expected


def test_45_format_is_local_versioned_and_not_pickle() -> None:
    assert LOCAL_PERSISTENCE_FORMAT.startswith("pollicino.local-")
    assert LOCAL_PERSISTENCE_VERSION == 1
    assert LOCAL_PERSISTENCE_MAGIC != b"\x80\x04"


def test_46_application_semantic_tokens_absent_from_core() -> None:
    source = Path(__file__).resolve().parents[1] / "src/pollicino/net/persistent_catalog.py"
    text = source.read_text().casefold()
    forbidden = {"faro", "evidence", "publisher", "recommendation", "machineprofile", "dna", "travel", "torrent", "magnet"}
    assert {token for token in forbidden if token in text} == set()


def test_47_no_pr52_or_network_dependency() -> None:
    source = Path(__file__).resolve().parents[1] / "src/pollicino/net/persistent_catalog.py"
    text = source.read_text().casefold()
    forbidden = {"noderuntime", "directorypollicinostore", "pnb1", "pnc1", "custody", "socket", "http", "bearer"}
    assert {token for token in forbidden if token in text} == set()


def test_48_standard_library_only_imports() -> None:
    source = (Path(__file__).resolve().parents[1] / "src/pollicino/net/persistent_catalog.py").read_text()
    assert "sqlite" not in source.casefold()
    assert "pickle" not in source.casefold()
    assert "journal" not in source.casefold()


def test_closed_or_uncertain_instance_exposes_no_stale_catalog_state(tmp_path: Path) -> None:
    catalog = PersistentBoundedReferenceCatalog(tmp_path / "node")
    catalog.add(entry(1))
    catalog.close()
    with pytest.raises(PersistentCatalogFailStopError):
        len(catalog)
    with pytest.raises(PersistentCatalogFailStopError):
        catalog.canonical_state()


@pytest.mark.parametrize("size", [10, 100, 1000, 10_000])
def test_49_to_52_bounded_snapshot_sizes_restart_exactly(tmp_path: Path, size: int) -> None:
    root = tmp_path / str(size)
    expected_entries = tuple(entry(index, 1) for index in range(size))
    with PersistentBoundedReferenceCatalog(root) as catalog:
        catalog.add_many(expected_entries)
        expected = catalog.canonical_state()
    with PersistentBoundedReferenceCatalog(root) as restarted:
        assert len(restarted) == size
        assert restarted.canonical_state() == expected


@pytest.mark.parametrize("size", [10, 100, 1000, 10_000])
def test_49_to_52_bounded_snapshot_sizes_restart_exactly(tmp_path: Path, size: int) -> None:
    root = tmp_path / str(size)
    entries = tuple(entry(index, 4) for index in range(size))
    with PersistentBoundedReferenceCatalog(root) as catalog:
        catalog.add_many(entries)
        expected = catalog.canonical_state()
        assert len(catalog) == size
    with PersistentBoundedReferenceCatalog(root) as restarted:
        assert restarted.canonical_state() == expected
        assert len(restarted) == size


def test_53_corrupt_generation_is_digest_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "node"
    with PersistentBoundedReferenceCatalog(root) as catalog:
        catalog.add(entry(1))
    corrupt(generation_path(root, 1), 9)
    with pytest.raises(PersistenceDigestError):
        PersistentBoundedReferenceCatalog(root)
