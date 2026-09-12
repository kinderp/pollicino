from __future__ import annotations

from pathlib import Path

from pollicino.net.endpoint import RecordKind, RecordMessage, encode_message
from pollicino.net.fragmentation import fragment_message
from px10_support import persistent_endpoint, query, reopen_endpoint
from px15_support import run_fragment_worker, run_fragmented_contact


def _roots(tmp_path: Path, count: int = 1):
    source_root, receiver_root = tmp_path / "source", tmp_path / "receiver"
    source = persistent_endpoint(source_root, "source")
    source.query_results.add_queries(query(index) for index in range(count)); source.close()
    persistent_endpoint(receiver_root, "receiver").close()
    return source_root, receiver_root


def test_lost_compact_fragment_is_transport_failure_not_fallback(tmp_path: Path) -> None:
    source, receiver = _roots(tmp_path, 20)
    lost = run_fragmented_contact(
        source, receiver, kind=RecordKind.QUERY, mtu=128,
        impair_message=1, drop_indexes=(3,),
    )
    check = reopen_endpoint(receiver, "verify")
    assert not lost.completed and lost.durable_commits == 0
    assert check.query_results.query_count == 0
    check.close()


def test_loss_during_exact_fallback_preserves_earlier_full_commits(tmp_path: Path) -> None:
    source, receiver = _roots(tmp_path, 20)
    lost = run_fragmented_contact(
        source, receiver, kind=RecordKind.QUERY, mtu=128,
        impair_message=5, drop_indexes=(0,),
    )
    assert not lost.completed
    before = reopen_endpoint(receiver, "before")
    committed = before.query_results.query_count
    before.close()
    resumed = run_fragmented_contact(source, receiver, kind=RecordKind.QUERY, mtu=128)
    after = reopen_endpoint(receiver, "after")
    assert resumed.completed and after.query_results.query_count == 20
    assert after.query_results.query_count >= committed
    after.close()


def test_receiver_restart_discards_mid_reassembly(tmp_path: Path) -> None:
    _source, receiver = _roots(tmp_path)
    encoded = encode_message(RecordMessage(RecordKind.QUERY, query(9)))
    frames = tuple(frame.encode() for frame in fragment_message(encoded, max_frame_bytes=64))
    assert len(frames) > 1
    partial = run_fragment_worker(receiver, "consume", mtu=64, frame_groups=(frames[:-1],))
    assert partial.returncode == 2
    check = reopen_endpoint(receiver, "verify")
    assert check.query_results.query_count == 0
    check.close()


def test_crash_after_reassembly_before_apply_leaves_record_missing(tmp_path: Path) -> None:
    _source, receiver = _roots(tmp_path)
    encoded = encode_message(RecordMessage(RecordKind.QUERY, query(9)))
    frames = tuple(frame.encode() for frame in fragment_message(encoded, max_frame_bytes=128))
    crashed = run_fragment_worker(
        receiver, "consume", mtu=128, frame_groups=(frames,), crash_after_reassembly=True
    )
    assert crashed.returncode == 92
    check = reopen_endpoint(receiver, "verify")
    assert check.query_results.query_count == 0
    check.close()


def test_crash_after_durable_commit_is_resolved_by_reconciliation(tmp_path: Path) -> None:
    source, receiver = _roots(tmp_path)
    encoded = encode_message(RecordMessage(RecordKind.QUERY, query(0)))
    frames = tuple(frame.encode() for frame in fragment_message(encoded, max_frame_bytes=128))
    crashed = run_fragment_worker(
        receiver, "consume", mtu=128, frame_groups=(frames,), crash_after_commit=True
    )
    assert crashed.returncode == 91
    fresh = run_fragmented_contact(source, receiver, kind=RecordKind.QUERY, mtu=128)
    check = reopen_endpoint(receiver, "verify")
    assert fresh.durable_commits == 0 and check.query_results.query_count == 1
    check.close()


def test_both_process_restart_after_partial_exchange_converges(tmp_path: Path) -> None:
    source, receiver = _roots(tmp_path, 20)
    partial = run_fragmented_contact(
        source, receiver, kind=RecordKind.QUERY, mtu=128, stop_before_message=7
    )
    assert not partial.completed
    resumed = run_fragmented_contact(source, receiver, kind=RecordKind.QUERY, mtu=128)
    check = reopen_endpoint(receiver, "verify")
    assert resumed.completed and check.query_results.query_count == 20
    check.close()


def test_permanent_fragment_loss_returns_finitely_without_false_convergence(tmp_path: Path) -> None:
    source, receiver = _roots(tmp_path, 1)
    for _ in range(3):
        report = run_fragmented_contact(
            source, receiver, kind=RecordKind.QUERY, mtu=128,
            impair_message=1, drop_indexes=(0,),
        )
        assert not report.completed and report.durable_commits == 0
    check = reopen_endpoint(receiver, "verify")
    assert check.query_results.query_count == 0
    check.close()
