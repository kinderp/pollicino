from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from pollicino.net.endpoint import RecordKind, RecordMessage, encode_message
from pollicino.net.fragmentation import fragment_message
from px10_support import persistent_endpoint, query, reopen_endpoint
from px15_support import REPOSITORY, run_fragment_worker, run_fragmented_contact


def _roots(tmp_path: Path, count: int = 1) -> tuple[Path, Path]:
    source_root, receiver_root = tmp_path / "source", tmp_path / "receiver"
    source = persistent_endpoint(source_root, "source")
    source.query_results.add_queries(query(index) for index in range(count))
    source.close()
    persistent_endpoint(receiver_root, "receiver").close()
    return source_root, receiver_root


def test_duplicate_and_reverse_fragment_delivery_converges(tmp_path: Path) -> None:
    source, receiver = _roots(tmp_path, 10)
    report = run_fragmented_contact(
        source,
        receiver,
        kind=RecordKind.QUERY,
        mtu=128,
        impair_message=1,
        duplicate_indexes=(0, 3),
        reverse=True,
    )
    check = reopen_endpoint(receiver, "verify")
    assert report.completed and check.query_results.query_count == 10
    check.close()


def test_corrupt_fragment_is_transport_failure_without_fallback(tmp_path: Path) -> None:
    source, receiver = _roots(tmp_path, 20)
    report = run_fragmented_contact(
        source,
        receiver,
        kind=RecordKind.QUERY,
        mtu=128,
        impair_message=1,
        corrupt_index=3,
    )
    check = reopen_endpoint(receiver, "verify")
    assert not report.completed and report.durable_commits == 0
    assert check.query_results.query_count == 0
    check.close()


def test_fragment_diagnostics_never_enter_protocol_stdout(tmp_path: Path) -> None:
    source, _receiver = _roots(tmp_path)
    result = run_fragment_worker(
        source,
        "adaptive-start",
        mtu=128,
        kind=RecordKind.QUERY,
        diagnostic=True,
    )
    assert result.returncode == 0
    assert b"diagnostic_probe" not in result.stdout
    assert result.diagnostics["diagnostic_probe"] == "stderr-only"


def test_os_writes_are_not_protocol_message_count(tmp_path: Path) -> None:
    source, _receiver = _roots(tmp_path)
    result = run_fragment_worker(
        source,
        "adaptive-start",
        mtu=64,
        kind=RecordKind.QUERY,
        write_chunk_size=1,
    )
    assert result.returncode == 0
    assert result.diagnostics["protocol_messages_out"] == 1
    assert result.diagnostics["fragment_frames_out"] > 1
    assert result.diagnostics["os_write_calls"] == len(result.stdout)
    assert result.diagnostics["os_bytes_out"] == len(result.stdout)
    assert result.diagnostics["protocol_bytes_out"] < len(result.stdout)


def test_receiver_process_killed_mid_reassembly_has_no_native_mutation(
    tmp_path: Path,
) -> None:
    _source, receiver = _roots(tmp_path)
    encoded = encode_message(RecordMessage(RecordKind.QUERY, query(9, bytes(1024))))
    frames = tuple(frame.encode() for frame in fragment_message(encoded, max_frame_bytes=128))
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPOSITORY / "src")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "pollicino.net.process_worker",
            "--root",
            str(receiver),
            "--operation",
            "consume",
            "--fragment-mtu",
            "128",
            "--read-size",
            "1",
        ],
        cwd=REPOSITORY,
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None
    process.stdin.write(b"".join(frames[:-1]))
    process.stdin.flush()
    process.kill()
    process.wait(timeout=2)
    check = reopen_endpoint(receiver, "verify")
    assert check.query_results.query_count == 0
    check.close()


def test_sender_crash_mid_fragmentation_is_whole_message_loss(tmp_path: Path) -> None:
    _source, receiver = _roots(tmp_path)
    encoded = encode_message(RecordMessage(RecordKind.QUERY, query(9, bytes(1024))))
    frames = tuple(frame.encode() for frame in fragment_message(encoded, max_frame_bytes=128))
    result = run_fragment_worker(
        receiver, "consume", mtu=128, frame_groups=(frames[:-1],), read_size=1
    )
    check = reopen_endpoint(receiver, "verify")
    assert result.returncode == 2
    assert check.query_results.query_count == 0
    check.close()


def test_malformed_fragment_produces_bounded_nonzero_child_exit(tmp_path: Path) -> None:
    _source, receiver = _roots(tmp_path)
    result = run_fragment_worker(
        receiver, "consume", mtu=128, frame_groups=((b"not-a-fragment",),)
    )
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.diagnostics["error_type"]

