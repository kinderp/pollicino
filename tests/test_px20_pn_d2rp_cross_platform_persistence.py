from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from pollicino.net.catalog import BoundedReference
from pollicino.net.local_filesystem import CAPABILITIES
from pollicino.net.persistent_catalog import (
    ConcurrentWriterError,
    LOCAL_PERSISTENCE_MAGIC,
    LOCAL_PERSISTENCE_VERSION,
    PersistentBoundedReferenceCatalog,
)
from pollicino.net.persistent_query import PersistentQueryResultStore
from pollicino.net.query import QueryRecord, ResultIdentity, ResultRecord


REPOSITORY = Path(__file__).resolve().parents[1]


def _environment() -> dict[str, str]:
    return dict(os.environ, PYTHONPATH=str(REPOSITORY / "src"))


def _entry(index: int) -> BoundedReference:
    return BoundedReference(index.to_bytes(4, "big"), hashlib.sha256(str(index).encode()).digest())


def test_registered_backend_and_no_unconditional_fcntl_import() -> None:
    expected = "windows" if os.name == "nt" else "posix"
    assert CAPABILITIES.backend == expected
    persistence_source = (REPOSITORY / "src/pollicino/net/local_persistence.py").read_text()
    assert "import fcntl" not in persistence_source
    assert LOCAL_PERSISTENCE_MAGIC == b"PRCP5D2R"
    assert LOCAL_PERSISTENCE_VERSION == 1


def test_catalog_and_query_result_roundtrip_on_native_platform(tmp_path: Path) -> None:
    catalog_root, query_root = tmp_path / "catalog", tmp_path / "query"
    with PersistentBoundedReferenceCatalog(catalog_root) as catalog:
        catalog.add_many((_entry(1), _entry(2)))
        catalog_state = catalog.canonical_state()
    with PersistentQueryResultStore(query_root) as store:
        store.add_query(QueryRecord(b"q", b"opaque"))
        store.add_result(ResultRecord(b"q", b"r", (b"key",)))
        query_state = store.canonical_state()
    with PersistentBoundedReferenceCatalog(catalog_root) as catalog:
        assert catalog.canonical_state() == catalog_state
    with PersistentQueryResultStore(query_root) as store:
        assert store.canonical_state() == query_state
        assert store.get_result(ResultIdentity(b"q", b"r")) is not None


def test_second_independent_process_is_rejected_then_close_releases_lock(tmp_path: Path) -> None:
    root = tmp_path / "locked"
    owner = PersistentBoundedReferenceCatalog(root)
    probe = """
from pollicino.net.persistent_catalog import ConcurrentWriterError, PersistentBoundedReferenceCatalog
import sys
try:
    PersistentBoundedReferenceCatalog(sys.argv[1])
except ConcurrentWriterError:
    raise SystemExit(23)
raise SystemExit(24)
"""
    blocked = subprocess.run([sys.executable, "-c", probe, str(root)], env=_environment())
    assert blocked.returncode == 23
    owner.close()
    with PersistentBoundedReferenceCatalog(root) as reopened:
        assert reopened.usable


def test_hard_process_exit_releases_lock(tmp_path: Path) -> None:
    root, ready = tmp_path / "crash-lock", tmp_path / "ready"
    owner = """
from pathlib import Path
from pollicino.net.persistent_catalog import PersistentBoundedReferenceCatalog
import os, sys, time
catalog = PersistentBoundedReferenceCatalog(sys.argv[1])
Path(sys.argv[2]).write_text('ready')
while True:
    time.sleep(1)
"""
    process = subprocess.Popen(
        [sys.executable, "-c", owner, str(root), str(ready)], env=_environment()
    )
    deadline = time.monotonic() + 5
    while not ready.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert ready.exists()
    with pytest.raises(ConcurrentWriterError):
        PersistentBoundedReferenceCatalog(root)
    process.kill()
    assert process.wait(timeout=5) != 0
    with PersistentBoundedReferenceCatalog(root) as reopened:
        assert reopened.usable


def test_stale_lock_contents_are_not_live_lock(tmp_path: Path) -> None:
    root = tmp_path / "stale"
    root.mkdir()
    (root / "catalog.lock").write_bytes(b"stale-lock-metadata")
    with PersistentBoundedReferenceCatalog(root) as catalog:
        assert catalog.usable


def test_snapshot_envelope_is_platform_neutral_json_evidence(tmp_path: Path) -> None:
    root = tmp_path / "format"
    with PersistentBoundedReferenceCatalog(root) as catalog:
        catalog.add(_entry(7))
        expected = catalog.canonical_state().hex()
    snapshots = sorted(root.glob("catalog.*.snapshot"))
    report = {
        "backend": CAPABILITIES.backend,
        "canonical_state": expected,
        "sha256": [hashlib.sha256(path.read_bytes()).hexdigest() for path in snapshots],
        "snapshot_sizes": [path.stat().st_size for path in snapshots],
    }
    encoded = json.dumps(report, sort_keys=True)
    assert json.loads(encoded) == report
