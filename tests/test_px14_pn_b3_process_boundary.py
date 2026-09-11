from __future__ import annotations

from pathlib import Path

from pollicino.net.adaptive_reconciliation import (
    AdaptiveIndependentEndpoint,
    AdaptivePolicy,
    run_adaptive_contact,
)
from pollicino.net.bearer import ScriptedImpairmentPlan
from pollicino.net.endpoint import (
    RecordKind,
    RecordMessage,
    ScriptedEncodedMessageLink,
    encode_message,
)
from px10_support import persistent_endpoint, query, reference, result, reopen_endpoint
from px14_support import run_directional_contact, run_reference_contact, run_worker


def _seed_queries(root: Path, count: int):
    endpoint = persistent_endpoint(root, "seed")
    endpoint.query_results.add_queries(query(index) for index in range(count))
    endpoint.close()


def test_two_process_lossless_query_matches_in_process_canonical_state(tmp_path: Path) -> None:
    source_root = tmp_path / "process-source"
    receiver_root = tmp_path / "process-receiver"
    oracle_source_root = tmp_path / "oracle-source"
    oracle_receiver_root = tmp_path / "oracle-receiver"
    _seed_queries(source_root, 3)
    _seed_queries(oracle_source_root, 3)
    persistent_endpoint(receiver_root, "empty").close()
    oracle_source = reopen_endpoint(oracle_source_root, "oracle-source")
    oracle_receiver = persistent_endpoint(oracle_receiver_root, "oracle-receiver")
    run_adaptive_contact(
        AdaptiveIndependentEndpoint(oracle_source.catalog, oracle_source.query_results),
        AdaptiveIndependentEndpoint(oracle_receiver.catalog, oracle_receiver.query_results),
        kind=RecordKind.QUERY,
        bearer=ScriptedEncodedMessageLink(ScriptedImpairmentPlan()),
        policy=AdaptivePolicy.selected_cost_aware(),
    )
    oracle_state = oracle_receiver.query_results.canonical_state()
    oracle_source.close(); oracle_receiver.close()

    report = run_directional_contact(source_root, receiver_root, kind=RecordKind.QUERY)
    receiver = reopen_endpoint(receiver_root, "verify")
    assert report.completed and report.durable_commits == 3
    assert len(set(report.process_ids)) == len(report.process_ids) >= 2
    assert receiver.query_results.canonical_state() == oracle_state
    receiver.close()


def test_exact_query_and_result_cross_process_bytes(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    source = persistent_endpoint(source_root, "source")
    source.query_results.add_query(query(1))
    source.query_results.add_result(result(1, 1))
    source.close(); persistent_endpoint(receiver_root, "receiver").close()
    queries = run_directional_contact(
        source_root, receiver_root, kind=RecordKind.QUERY, adaptive=False
    )
    results = run_directional_contact(
        source_root, receiver_root, kind=RecordKind.RESULT, adaptive=False
    )
    receiver = reopen_endpoint(receiver_root, "verify")
    assert queries.completed and results.completed
    assert receiver.query_results.get_query(query(1).query_id) == query(1)
    assert receiver.query_results.get_result(result(1, 1).identity) == result(1, 1)
    receiver.close()


def test_explicit_reference_selection_crosses_process_bytes(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    source = persistent_endpoint(source_root, "source")
    chosen = reference(1)
    ignored = reference(2)
    source.catalog.add_many((chosen, ignored))
    source.close(); persistent_endpoint(receiver_root, "receiver").close()
    report = run_reference_contact(source_root, receiver_root, (chosen.logical_key,))
    receiver = reopen_endpoint(receiver_root, "verify")
    assert report.completed and report.durable_commits == 1
    assert receiver.catalog.get(chosen.logical_key) == chosen
    assert ignored.logical_key not in receiver.catalog
    receiver.close()


def test_adaptive_compact_success_is_decided_inside_endpoint_workers(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    _seed_queries(source_root, 10)
    persistent_endpoint(receiver_root, "receiver").close()
    report = run_directional_contact(source_root, receiver_root, kind=RecordKind.QUERY)
    receiver = reopen_endpoint(receiver_root, "verify")
    assert report.completed and report.decisions == ("COMPACT_10",)
    assert receiver.query_results.query_count == 10
    receiver.close()


def test_directional_probe_does_not_pull_receiver_only_state_back_to_source(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    _seed_queries(source_root, 1)
    _seed_queries(receiver_root, 2)
    report = run_directional_contact(source_root, receiver_root, kind=RecordKind.QUERY)
    source = reopen_endpoint(source_root, "verify-source")
    receiver = reopen_endpoint(receiver_root, "verify-receiver")
    assert report.completed and report.durable_commits == 0
    assert source.query_results.query_count == 1
    assert receiver.query_results.query_count == 2
    source.close(); receiver.close()


def test_delivered_compact_failure_triggers_same_contact_exact_bytes(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    _seed_queries(source_root, 20)
    persistent_endpoint(receiver_root, "receiver").close()
    report = run_directional_contact(source_root, receiver_root, kind=RecordKind.QUERY)
    receiver = reopen_endpoint(receiver_root, "verify")
    assert report.completed and receiver.query_results.query_count == 20
    assert report.decisions == ("COMPACT_10",)
    receiver.close()


def test_small_attempt_budget_selects_exact_immediately(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    _seed_queries(source_root, 1)
    persistent_endpoint(receiver_root, "receiver").close()
    report = run_directional_contact(
        source_root, receiver_root, kind=RecordKind.QUERY, max_attempts=9
    )
    receiver = reopen_endpoint(receiver_root, "verify")
    assert report.completed and report.decisions == ("EXACT_RESERVE",)
    assert receiver.query_results.query_count == 1
    receiver.close()


def test_protocol_stdout_and_diagnostics_stderr_are_isolated(tmp_path: Path) -> None:
    root = tmp_path / "root"
    _seed_queries(root, 1)
    result = run_worker(
        root, "adaptive-start", kind=RecordKind.QUERY, diagnostic=True,
        output_segments=(1,)
    )
    assert result.returncode == 0
    assert result.messages
    assert b"diagnostic_probe" not in result.stdout
    assert result.diagnostics["diagnostic_probe"] == "stderr-only"


def test_worker_uses_many_os_reads_for_one_protocol_message(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    _seed_queries(source_root, 1)
    persistent_endpoint(receiver_root, "receiver").close()
    start = run_worker(source_root, "adaptive-start", kind=RecordKind.QUERY)
    received = run_worker(
        receiver_root, "consume", messages=start.messages, role="RESPONDER", read_size=1
    )
    assert received.returncode == 0
    assert received.diagnostics["protocol_messages_in"] == 1
    assert received.diagnostics["os_read_calls"] > 1


def test_multiple_and_legally_reordered_records_in_one_pipe_read(tmp_path: Path) -> None:
    receiver_root = tmp_path / "receiver"
    persistent_endpoint(receiver_root, "receiver").close()
    encoded = tuple(
        encode_message(RecordMessage(RecordKind.QUERY, query(index)))
        for index in (3, 1, 2)
    )
    received = run_worker(receiver_root, "consume", messages=encoded, read_size=8192)
    receiver = reopen_endpoint(receiver_root, "verify")
    assert received.returncode == 0
    assert received.diagnostics["protocol_messages_in"] == 3
    assert received.diagnostics["durable_commits"] == 3
    assert receiver.query_results.sorted_query_ids() == tuple(
        query(index).query_id for index in (1, 2, 3)
    )
    receiver.close()
