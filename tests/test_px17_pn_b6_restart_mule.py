from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

from pollicino.net.endpoint import RecordKind
from pollicino.net.fragmentation import fragment_message
from px10_support import persistent_endpoint, query, reopen_endpoint, result
from px17_support import REPOSITORY, run_stream_contact
from test_px15_pn_b4_fragment_codec import compact_summary


def _seed(root: Path, count: int = 1) -> None:
    endpoint = persistent_endpoint(root, "seed")
    endpoint.query_results.add_queries(query(index, bytes(512)) for index in range(count))
    endpoint.close()


def _empty(root: Path) -> None:
    persistent_endpoint(root, "empty").close()


def test_receiver_crash_before_apply_has_no_mutation_and_fresh_contact_recovers(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source); _empty(receiver)
    crashed = run_stream_contact(
        source, receiver, kind=RecordKind.QUERY, mtu=128,
        responder_extra=("--crash-after-reassembly",),
    )
    check = reopen_endpoint(receiver, "after-crash")
    assert crashed.responder_returncode == 93
    assert check.query_results.query_count == 0
    check.close()
    recovered = run_stream_contact(source, receiver, kind=RecordKind.QUERY, mtu=128)
    check = reopen_endpoint(receiver, "after-recovery")
    assert recovered.initiator_returncode == recovered.responder_returncode == 0
    assert check.query_results.query_count == 1
    check.close()


def test_receiver_crash_after_commit_preserves_durable_progress(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source); _empty(receiver)
    crashed = run_stream_contact(
        source, receiver, kind=RecordKind.QUERY, mtu=128,
        responder_extra=("--crash-after-commit",),
    )
    check = reopen_endpoint(receiver, "after-crash")
    assert crashed.responder_returncode == 94
    assert check.query_results.query_count == 1
    check.close()
    fresh = run_stream_contact(source, receiver, kind=RecordKind.QUERY, mtu=128)
    check = reopen_endpoint(receiver, "fresh")
    assert fresh.initiator_returncode == fresh.responder_returncode == 0
    assert check.query_results.query_count == 1
    check.close()


def test_interrupted_exact_fallback_keeps_only_complete_commits(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, 100); _empty(receiver)
    crashed = run_stream_contact(
        source, receiver, kind=RecordKind.QUERY, mtu=128,
        responder_extra=("--crash-after-commit",),
    )
    partial = reopen_endpoint(receiver, "partial")
    count = partial.query_results.query_count
    partial.close()
    assert crashed.responder_returncode == 94
    assert 0 < count < 100
    fresh = run_stream_contact(source, receiver, kind=RecordKind.QUERY, mtu=128)
    complete = reopen_endpoint(receiver, "complete")
    assert fresh.initiator_returncode == fresh.responder_returncode == 0
    count = complete.query_results.query_count
    complete.close()
    contacts = 1
    while count < 100:
        contacts += 1
        later = run_stream_contact(source, receiver, kind=RecordKind.QUERY, mtu=128)
        assert later.initiator_returncode == later.responder_returncode == 0
        complete = reopen_endpoint(receiver, "complete-later")
        count = complete.query_results.query_count
        complete.close()
        assert contacts <= 3
    assert count == 100


def test_both_endpoint_restart_uses_only_durable_state(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, 100); _empty(receiver)
    first = run_stream_contact(
        source, receiver, kind=RecordKind.QUERY, mtu=128,
        responder_extra=("--crash-after-commit",),
    )
    assert first.responder_returncode == 94
    # Both worker processes are gone. A new pair opens only the durable roots.
    second = run_stream_contact(source, receiver, kind=RecordKind.QUERY, mtu=128)
    check = reopen_endpoint(receiver, "verify")
    assert second.initiator_returncode == second.responder_returncode == 0
    count = check.query_results.query_count
    check.close()
    contacts = 1
    while count < 100:
        contacts += 1
        later = run_stream_contact(source, receiver, kind=RecordKind.QUERY, mtu=128)
        assert later.initiator_returncode == later.responder_returncode == 0
        check = reopen_endpoint(receiver, "verify-later")
        count = check.query_results.query_count
        check.close()
        assert contacts <= 3
    assert count == 100


def test_sender_crash_after_complete_local_record_write_is_resolved_by_durable_state(
    tmp_path: Path,
) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source); _empty(receiver)
    crashed = run_stream_contact(
        source,
        receiver,
        kind=RecordKind.QUERY,
        mtu=128,
        initiator_extra=("--crash-after-send-batch", "2"),
    )
    check = reopen_endpoint(receiver, "after-sender-crash")
    assert crashed.initiator_returncode == 95
    assert check.query_results.query_count == 1
    check.close()
    fresh = run_stream_contact(source, receiver, kind=RecordKind.QUERY, mtu=128)
    check = reopen_endpoint(receiver, "fresh")
    assert fresh.initiator_returncode == fresh.responder_returncode == 0
    assert check.query_results.query_count == 1
    check.close()


def test_sender_exit_mid_frame_causes_no_receiver_mutation(tmp_path: Path) -> None:
    receiver = tmp_path / "receiver"
    _empty(receiver)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPOSITORY / "src")
    with tempfile.TemporaryDirectory(prefix="px17-mid-", dir="/tmp") as raw:
        path = Path(raw) / "listener.sock"
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "pollicino.net.unix_stream_worker",
                "--root",
                str(receiver),
                "--listener",
                str(path),
                "--role",
                "responder",
                "--kind",
                RecordKind.QUERY.name,
                "--mtu",
                "128",
                "--timeout",
                "0.3",
            ],
            cwd=REPOSITORY,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 2
        while not path.exists() and time.monotonic() < deadline:
            time.sleep(0.005)
        assert path.exists()
        raw_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        raw_socket.connect(os.fspath(path))
        frame = fragment_message(compact_summary(), max_frame_bytes=128)[0].encode()
        raw_socket.sendall(frame[:31])
        raw_socket.close()
        stdout, stderr = process.communicate(timeout=3)
        assert stdout == b"" and process.returncode == 2
        diagnostic = json.loads(stderr.decode().splitlines()[-1])
        assert diagnostic["error_type"] == "UnixStreamFrameError"
    check = reopen_endpoint(receiver, "verify")
    assert check.query_results.query_count == 0
    check.close()


def test_semantic_blind_stream_mule_with_restart(tmp_path: Path) -> None:
    a_root, b_root, c_root = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    _seed(a_root); _empty(b_root); _empty(c_root)
    ac = run_stream_contact(a_root, c_root, kind=RecordKind.QUERY, mtu=128)
    cb = run_stream_contact(c_root, b_root, kind=RecordKind.QUERY, mtu=128)
    b = reopen_endpoint(b_root, "result")
    carried = result(0, 0, (b"selected-reference-key",))
    b.query_results.add_result(carried)
    b.close()
    bc = run_stream_contact(b_root, c_root, kind=RecordKind.RESULT, mtu=128)
    ca = run_stream_contact(c_root, a_root, kind=RecordKind.RESULT, mtu=128)
    a = reopen_endpoint(a_root, "verify")
    try:
        assert all(
            report.initiator_returncode == report.responder_returncode == 0
            for report in (ac, cb, bc, ca)
        )
        assert a.query_results.get_result(carried.identity) == carried
    finally:
        a.close()
