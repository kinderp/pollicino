from __future__ import annotations

from pathlib import Path

from pollicino.net.endpoint import RecordKind
from pollicino.net.fragmentation import fragment_message
from px10_support import persistent_endpoint, query, reference, result, reopen_endpoint
from px15_support import (
    run_fragment_worker,
    run_fragmented_contact,
    run_fragmented_reference_contact,
)
from test_px15_pn_b4_fragment_codec import maximum_message


def _seed(root: Path, *, queries: int = 0, results: int = 0) -> None:
    endpoint = persistent_endpoint(root, "seed")
    endpoint.query_results.add_queries(query(index) for index in range(queries))
    endpoint.query_results.add_results(result(index, index) for index in range(results))
    endpoint.close()


def test_exact_query_and_result_cross_fragmented_process_boundary(tmp_path: Path) -> None:
    source_root, receiver_root = tmp_path / "source", tmp_path / "receiver"
    _seed(source_root, queries=1, results=1)
    persistent_endpoint(receiver_root, "receiver").close()
    queries = run_fragmented_contact(
        source_root, receiver_root, kind=RecordKind.QUERY, mtu=128, adaptive=False
    )
    results = run_fragmented_contact(
        source_root, receiver_root, kind=RecordKind.RESULT, mtu=128, adaptive=False
    )
    receiver = reopen_endpoint(receiver_root, "verify")
    assert queries.completed and results.completed
    assert queries.fragment_frames > queries.protocol_messages
    assert receiver.query_results.get_query(query(0).query_id) == query(0)
    assert receiver.query_results.get_result(result(0, 0).identity) == result(0, 0)
    receiver.close()


def test_explicit_reference_crosses_fragmented_process_boundary(tmp_path: Path) -> None:
    source_root, receiver_root = tmp_path / "source", tmp_path / "receiver"
    source = persistent_endpoint(source_root, "source")
    chosen, ignored = reference(1, bytes(512)), reference(2)
    source.catalog.add_many((chosen, ignored)); source.close()
    persistent_endpoint(receiver_root, "receiver").close()
    report = run_fragmented_reference_contact(
        source_root, receiver_root, (chosen.logical_key,), mtu=128
    )
    receiver = reopen_endpoint(receiver_root, "verify")
    assert report.completed and report.durable_commits == 1
    assert receiver.catalog.get(chosen.logical_key) == chosen
    assert ignored.logical_key not in receiver.catalog
    receiver.close()


def test_compact_success_and_fallback_both_use_fragments(tmp_path: Path) -> None:
    small_source, small_receiver = tmp_path / "small-source", tmp_path / "small-receiver"
    _seed(small_source, queries=10); persistent_endpoint(small_receiver, "receiver").close()
    compact = run_fragmented_contact(
        small_source, small_receiver, kind=RecordKind.QUERY, mtu=128
    )
    large_source, large_receiver = tmp_path / "large-source", tmp_path / "large-receiver"
    _seed(large_source, queries=20); persistent_endpoint(large_receiver, "receiver").close()
    fallback = run_fragmented_contact(
        large_source, large_receiver, kind=RecordKind.QUERY, mtu=128
    )
    large = reopen_endpoint(large_receiver, "verify")
    assert compact.completed and fallback.completed
    assert compact.decision == fallback.decision == "COMPACT_10"
    assert compact.fragment_frames > compact.protocol_messages
    assert fallback.fragment_frames > fallback.protocol_messages
    assert large.query_results.query_count == 20
    large.close()


def test_small_budget_keeps_exact_immediate_policy(tmp_path: Path) -> None:
    source_root, receiver_root = tmp_path / "source", tmp_path / "receiver"
    _seed(source_root, queries=1); persistent_endpoint(receiver_root, "receiver").close()
    report = run_fragmented_contact(
        source_root, receiver_root, kind=RecordKind.QUERY, mtu=256,
        max_protocol_messages=9,
    )
    receiver = reopen_endpoint(receiver_root, "verify")
    assert report.completed and report.decision == "EXACT_RESERVE"
    assert receiver.query_results.query_count == 1
    receiver.close()


def test_maximum_message_reassembles_inside_receiver_process_at_mtu64(tmp_path: Path) -> None:
    root = tmp_path / "receiver"
    persistent_endpoint(root, "receiver").close()
    frames = tuple(frame.encode() for frame in fragment_message(maximum_message(), max_frame_bytes=64))
    result = run_fragment_worker(
        root, "consume", mtu=64, frame_groups=(frames,), read_size=1, timeout=20
    )
    assert result.returncode == 0
    assert result.diagnostics["fragment_frames_in"] == 2438
    assert result.diagnostics["protocol_messages_in"] == 1


def test_many_exact_records_make_fair_progress_across_fresh_processes(tmp_path: Path) -> None:
    source_root, receiver_root = tmp_path / "source", tmp_path / "receiver"
    _seed(source_root, queries=105); persistent_endpoint(receiver_root, "receiver").close()
    contacts = 0
    while True:
        contacts += 1
        report = run_fragmented_contact(
            source_root, receiver_root, kind=RecordKind.QUERY, mtu=256, adaptive=False
        )
        receiver = reopen_endpoint(receiver_root, "check")
        count = receiver.query_results.query_count
        receiver.close()
        if count == 105:
            break
        assert not report.completed and contacts <= 3
    assert contacts == 2

