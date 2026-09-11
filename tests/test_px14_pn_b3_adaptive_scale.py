from __future__ import annotations

from pathlib import Path

import pytest

from pollicino.net.endpoint import RecordKind
from px10_support import persistent_endpoint, query, result, reopen_endpoint
from px14_support import run_directional_contact, run_worker


def _seed_state(root: Path, *, query_count: int, result_count: int = 0) -> None:
    endpoint = persistent_endpoint(root, "seed")
    endpoint.query_results.add_queries(query(index) for index in range(query_count))
    endpoint.query_results.add_results(result(index, index) for index in range(result_count))
    endpoint.close()


@pytest.mark.parametrize(
    ("difference", "expected"),
    (
        (0, "EQUAL"),
        (1, "DECODED"),
        (10, "DECODED"),
        (100, "CAPACITY_EXCEEDED"),
        (1_000, "CAPACITY_EXCEEDED"),
        (10_000, "CAPACITY_EXCEEDED"),
    ),
)
def test_capacity_10_process_probe_at_10000_scale(
    tmp_path: Path, difference: int, expected: str
) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    _seed_state(source_root, query_count=10_000)
    _seed_state(receiver_root, query_count=10_000 - difference)
    start = run_worker(source_root, "adaptive-start", kind=RecordKind.QUERY)
    assert start.returncode == 0 and start.diagnostics["decision"] == "COMPACT_10"
    receiver = run_worker(
        receiver_root,
        "consume",
        messages=start.messages,
        role="RESPONDER",
        read_size=1,
    )
    assert receiver.returncode == 0
    assert receiver.diagnostics["compact_statuses"] == [expected]
    if expected == "CAPACITY_EXCEEDED":
        source = run_worker(
            source_root,
            "consume",
            messages=receiver.messages,
            role="INITIATOR",
        )
        assert source.returncode == 0
        assert source.messages and source.messages[0][:4] == b"PB2F"


def test_105_queries_and_results_cross_process_path_after_restarts(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    _seed_state(source_root, query_count=105, result_count=105)
    persistent_endpoint(receiver_root, "receiver").close()
    contacts = 0
    for kind in (RecordKind.QUERY, RecordKind.RESULT):
        while True:
            contacts += 1
            report = run_directional_contact(
                source_root, receiver_root, kind=kind, adaptive=False
            )
            receiver = reopen_endpoint(receiver_root, "check")
            active = (
                receiver.query_results.query_count
                if kind is RecordKind.QUERY
                else receiver.query_results.result_count
            )
            receiver.close()
            if active == 105:
                break
            assert not report.completed and contacts <= 6
    source = reopen_endpoint(source_root, "source-final")
    receiver = reopen_endpoint(receiver_root, "receiver-final")
    assert receiver.query_results.canonical_state() == source.query_results.canonical_state()
    source.close(); receiver.close()

