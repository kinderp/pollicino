from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

from pollicino.net.catalog import BoundedReference
from pollicino.net.local_filesystem import CAPABILITIES
from pollicino.net.persistent_catalog import PersistentBoundedReferenceCatalog
from pollicino.net.persistent_query import PersistentQueryResultStore
from pollicino.net.query import QueryRecord, ResultIdentity, ResultRecord


REPOSITORY = Path(__file__).resolve().parents[1]


def _git_state() -> tuple[str, bool]:
    sha = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=REPOSITORY,
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    status = subprocess.run(
        ("git", "status", "--porcelain=v1"), cwd=REPOSITORY,
        check=True, capture_output=True, text=True,
    ).stdout
    return sha, not bool(status)


def _environment() -> dict[str, str]:
    return dict(os.environ, PYTHONPATH=str(REPOSITORY / "src"))


def _write(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def _lock_probe(root: Path) -> int:
    try:
        store = PersistentBoundedReferenceCatalog(root)
    except Exception as exc:
        from pollicino.net.local_persistence import ConcurrentWriterError

        return 23 if isinstance(exc, ConcurrentWriterError) else 25
    store.close()
    return 24


def _hold_lock(root: Path, ready: Path) -> int:
    store = PersistentBoundedReferenceCatalog(root)
    ready.write_text("ready", encoding="ascii")
    try:
        while True:
            time.sleep(1)
    finally:
        store.close()


def probe(args: argparse.Namespace) -> int:
    sha, clean = _git_state()
    with tempfile.TemporaryDirectory(prefix="px20-persistence-") as raw:
        base = Path(raw)
        catalog_root, query_root = base / "catalog", base / "query"
        reference = BoundedReference(b"px20-key", hashlib.sha256(b"px20").digest())
        with PersistentBoundedReferenceCatalog(catalog_root) as catalog:
            catalog.add(reference)
            catalog_state = catalog.canonical_state()
            lock_probe = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "lock-probe", str(catalog_root)],
                env=_environment(), check=False,
            ).returncode
        with PersistentBoundedReferenceCatalog(catalog_root) as catalog:
            catalog_reopen = catalog.canonical_state() == catalog_state

        with PersistentQueryResultStore(query_root) as queries:
            queries.add_query(QueryRecord(b"query", b"opaque"))
            queries.add_result(ResultRecord(b"query", b"result", (b"px20-key",)))
            query_state = queries.canonical_state()
        with PersistentQueryResultStore(query_root) as queries:
            query_reopen = queries.canonical_state() == query_state
            result_present = queries.get_result(ResultIdentity(b"query", b"result")) is not None

        crash_root, ready = base / "crash-lock", base / "ready"
        owner = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "hold-lock", str(crash_root), str(ready)],
            env=_environment(),
        )
        deadline = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        if not ready.exists():
            owner.kill(); owner.wait(timeout=5)
            raise RuntimeError("lock owner did not become ready")
        owner.kill()
        owner.wait(timeout=5)
        with PersistentBoundedReferenceCatalog(crash_root) as reopened:
            crash_lock_released = reopened.usable

        snapshot = next(catalog_root.glob("catalog.*.snapshot"))
        value: dict[str, object] = {
            "gate": "PX20-PN-D2RP",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "commit_sha": sha,
            "worktree_clean": clean,
            "os": platform.platform(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "filesystem_backend": CAPABILITIES.backend,
            "lock_primitive": CAPABILITIES.exclusive_nonblocking_lock,
            "replacement_primitive": CAPABILITIES.replacement,
            "directory_fsync": CAPABILITIES.directory_fsync,
            "posix_modes": CAPABILITIES.posix_modes,
            "second_process_rejected": lock_probe == 23,
            "crash_lock_released": crash_lock_released,
            "catalog_reopen_match": catalog_reopen,
            "query_result_reopen_match": query_reopen,
            "result_present": result_present,
            "catalog_state_sha256": hashlib.sha256(catalog_state).hexdigest(),
            "query_result_state_sha256": hashlib.sha256(query_state).hexdigest(),
            "snapshot_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
            "snapshot_bytes": snapshot.stat().st_size,
            "success": all((
                clean,
                lock_probe == 23,
                crash_lock_released,
                catalog_reopen,
                query_reopen,
                result_present,
            )),
        }
    _write(args.output, value)
    print(json.dumps(value, sort_keys=True))
    return 0 if value["success"] else 2


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="px20-pn-d2rp-persistence")
    commands = root.add_subparsers(dest="command", required=True)
    probe_parser = commands.add_parser("probe")
    probe_parser.add_argument("--output", type=Path, required=True)
    probe_parser.set_defaults(handler=probe)
    lock_parser = commands.add_parser("lock-probe")
    lock_parser.add_argument("root", type=Path)
    lock_parser.set_defaults(handler=lambda args: _lock_probe(args.root))
    hold_parser = commands.add_parser("hold-lock")
    hold_parser.add_argument("root", type=Path)
    hold_parser.add_argument("ready", type=Path)
    hold_parser.set_defaults(handler=lambda args: _hold_lock(args.root, args.ready))
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
