from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

import pytest

from pollicino.net.endpoint import RecordKind, RecordMessage, encode_message
from px10_support import persistent_endpoint, query, reference, result, reopen_endpoint
from px14_support import (
    REPOSITORY,
    run_directional_contact,
    run_reference_contact,
    run_worker,
)


def _seed(root: Path, queries: int = 1):
    endpoint = persistent_endpoint(root, "seed")
    endpoint.query_results.add_queries(query(index) for index in range(queries))
    endpoint.close()


@pytest.mark.parametrize("fraction", (0.1, 0.9))
def test_eof_before_complete_record_causes_no_native_mutation(tmp_path: Path, fraction: float) -> None:
    receiver_root = tmp_path / "receiver"
    persistent_endpoint(receiver_root, "receiver").close()
    encoded = encode_message(RecordMessage(RecordKind.QUERY, query(1)))
    partial = encoded[: int(len(encoded) * fraction)]
    result = run_worker(receiver_root, "consume", messages=(partial,), read_size=1)
    assert result.returncode == 2 and result.stdout == b""
    receiver = reopen_endpoint(receiver_root, "verify")
    assert receiver.query_results.query_count == 0
    receiver.close()


def test_corrupt_complete_record_fails_without_mutation(tmp_path: Path) -> None:
    receiver_root = tmp_path / "receiver"
    persistent_endpoint(receiver_root, "receiver").close()
    encoded = bytearray(encode_message(RecordMessage(RecordKind.QUERY, query(1))))
    encoded[-1] ^= 1
    result = run_worker(receiver_root, "consume", messages=(bytes(encoded),))
    assert result.returncode == 2
    receiver = reopen_endpoint(receiver_root, "verify")
    assert receiver.query_results.query_count == 0
    receiver.close()


@pytest.mark.parametrize("offset", (0, 4, 5))
def test_corrupt_magic_unknown_version_or_type_never_mutates(
    tmp_path: Path, offset: int
) -> None:
    receiver_root = tmp_path / f"receiver-{offset}"
    persistent_endpoint(receiver_root, "receiver").close()
    encoded = bytearray(encode_message(RecordMessage(RecordKind.QUERY, query(1))))
    encoded[offset] = 255
    result = run_worker(receiver_root, "consume", messages=(bytes(encoded),))
    receiver = reopen_endpoint(receiver_root, "verify")
    assert result.returncode == 2
    assert receiver.query_results.query_count == 0
    receiver.close()


def test_clean_empty_eof_is_bounded_noop(tmp_path: Path) -> None:
    root = tmp_path / "root"
    persistent_endpoint(root, "root").close()
    result = run_worker(root, "consume")
    assert result.returncode == 0 and result.messages == ()
    assert result.diagnostics["protocol_messages_in"] == 0


def test_receiver_exit_after_commit_sender_uncertainty_reconciles_from_disk(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    _seed(source_root)
    persistent_endpoint(receiver_root, "receiver").close()
    first = run_directional_contact(source_root, receiver_root, kind=RecordKind.QUERY)
    assert first.durable_commits == 1
    fresh = run_directional_contact(source_root, receiver_root, kind=RecordKind.QUERY)
    receiver = reopen_endpoint(receiver_root, "verify")
    assert fresh.durable_commits == 0
    assert receiver.query_results.query_count == 1
    receiver.close()


def test_receiver_hard_crash_after_commit_preserves_atomic_record(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    _seed(source_root)
    persistent_endpoint(receiver_root, "receiver").close()
    encoded = encode_message(RecordMessage(RecordKind.QUERY, query(0)))
    crashed = run_worker(
        receiver_root, "consume", messages=(encoded,), crash_after_commit=True
    )
    assert crashed.returncode == 91 and crashed.stdout == b""
    receiver = reopen_endpoint(receiver_root, "after-crash")
    assert receiver.query_results.get_query(query(0).query_id) == query(0)
    receiver.close()
    fresh = run_directional_contact(source_root, receiver_root, kind=RecordKind.QUERY)
    assert fresh.durable_commits == 0


def test_receiver_process_killed_mid_body_leaves_no_record(tmp_path: Path) -> None:
    receiver_root = tmp_path / "receiver"
    persistent_endpoint(receiver_root, "receiver").close()
    encoded = encode_message(RecordMessage(RecordKind.QUERY, query(1)))
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPOSITORY / "src")
    process = subprocess.Popen(
        [
            sys.executable, "-m", "pollicino.net.process_worker",
            "--root", str(receiver_root), "--operation", "consume",
            "--read-size", "1",
        ],
        cwd=REPOSITORY,
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None
    process.stdin.write(encoded[: int(len(encoded) * 0.9)])
    process.stdin.flush()
    process.kill()
    process.wait(timeout=2)
    receiver = reopen_endpoint(receiver_root, "verify")
    assert receiver.query_results.query_count == 0
    receiver.close()


def test_loss_before_commit_then_both_sides_restart_recovers(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    _seed(source_root)
    persistent_endpoint(receiver_root, "receiver").close()
    interrupted = run_directional_contact(
        source_root, receiver_root, kind=RecordKind.QUERY, stop_before_attempt=3
    )
    assert not interrupted.completed
    receiver = reopen_endpoint(receiver_root, "precheck")
    assert receiver.query_results.query_count == 0
    receiver.close()
    resumed = run_directional_contact(source_root, receiver_root, kind=RecordKind.QUERY)
    assert resumed.completed and resumed.durable_commits == 1


def test_disconnect_during_compact_probe_is_not_capacity_evidence(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    _seed(source_root, 20)
    persistent_endpoint(receiver_root, "receiver").close()
    dropped = run_directional_contact(
        source_root, receiver_root, kind=RecordKind.QUERY, drop_attempts=(1,)
    )
    receiver = reopen_endpoint(receiver_root, "verify")
    assert dropped.completed and dropped.durable_commits == 0
    assert receiver.query_results.query_count == 0
    receiver.close()


def test_corrupt_compact_probe_stops_without_exact_fallback(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    _seed(source_root, 20)
    persistent_endpoint(receiver_root, "receiver").close()
    corrupted = run_directional_contact(
        source_root, receiver_root, kind=RecordKind.QUERY, corrupt_attempts=(1,)
    )
    receiver = reopen_endpoint(receiver_root, "verify")
    assert not corrupted.completed and receiver.query_results.query_count == 0
    receiver.close()


def test_crash_mid_exact_fallback_then_fresh_policy_converges(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    _seed(source_root, 20)
    persistent_endpoint(receiver_root, "receiver").close()
    partial = run_directional_contact(
        source_root, receiver_root, kind=RecordKind.QUERY, stop_before_attempt=6
    )
    assert not partial.completed
    resumed = run_directional_contact(source_root, receiver_root, kind=RecordKind.QUERY)
    receiver = reopen_endpoint(receiver_root, "verify")
    assert resumed.completed and receiver.query_results.query_count == 20
    receiver.close()


def test_semantic_blind_process_mule_carries_query_and_result(tmp_path: Path) -> None:
    a_root, b_root, c_root = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    _seed(a_root)
    persistent_endpoint(b_root, "b").close()
    persistent_endpoint(c_root, "c").close()
    assert run_directional_contact(a_root, c_root, kind=RecordKind.QUERY).completed
    assert run_directional_contact(c_root, b_root, kind=RecordKind.QUERY).completed
    b = reopen_endpoint(b_root, "application-b")
    b.query_results.add_result(result(0, 1))
    b.close()
    assert run_directional_contact(b_root, c_root, kind=RecordKind.RESULT).completed
    assert run_directional_contact(c_root, a_root, kind=RecordKind.RESULT).completed
    a = reopen_endpoint(a_root, "verify-a")
    assert a.query_results.get_result(result(0, 1).identity) == result(0, 1)
    a.close()


def test_semantic_blind_process_mule_carries_only_explicit_reference(tmp_path: Path) -> None:
    a_root, b_root, c_root = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    persistent_endpoint(a_root, "a").close()
    b = persistent_endpoint(b_root, "b")
    chosen, ignored = reference(1), reference(2)
    b.catalog.add_many((chosen, ignored))
    b.close(); persistent_endpoint(c_root, "c").close()
    assert run_reference_contact(b_root, c_root, (chosen.logical_key,)).completed
    assert run_reference_contact(c_root, a_root, (chosen.logical_key,)).completed
    a = reopen_endpoint(a_root, "verify")
    assert a.catalog.get(chosen.logical_key) == chosen
    assert ignored.logical_key not in a.catalog
    a.close()


def test_tiny_contact_budget_returns_control_without_false_convergence(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    _seed(source_root, 20)
    persistent_endpoint(receiver_root, "receiver").close()
    report = run_directional_contact(
        source_root, receiver_root, kind=RecordKind.QUERY, max_attempts=2
    )
    receiver = reopen_endpoint(receiver_root, "verify")
    assert not report.completed
    assert receiver.query_results.query_count < 20
    receiver.close()


def test_nonzero_child_exit_is_bounded_process_failure(tmp_path: Path) -> None:
    root = tmp_path / "root"
    persistent_endpoint(root, "root").close()
    result = run_worker(root, "consume", messages=(b"not-a-message",))
    assert result.returncode == 2
    assert result.diagnostics["error_type"]


def test_harness_timeout_bounds_a_stalled_child() -> None:
    with pytest.raises(subprocess.TimeoutExpired):
        subprocess.run(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            cwd=REPOSITORY,
            timeout=0.05,
            check=False,
        )


def test_backpressure_sanity_has_bounded_output_and_terminates(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    _seed(source_root, 100)
    from pollicino.net.endpoint import RequestMessage

    requested = tuple(query(index).query_id for index in range(100))
    request = encode_message(RequestMessage(RecordKind.QUERY, requested))
    result = run_worker(
        source_root,
        "consume",
        messages=(request,),
        write_chunk_size=1,
        timeout=10,
        output_segments=(8191,),
    )
    assert result.returncode == 0
    assert len(result.messages) == 100
    assert result.diagnostics["os_write_calls"] == len(result.stdout)
