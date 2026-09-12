from __future__ import annotations

from pathlib import Path

import pytest

from pollicino.net.endpoint import RecordKind
from px10_support import persistent_endpoint, query, reopen_endpoint, result
from px18_support import run_udp_contact, run_udp_relay_contact


def _seed(root: Path, count: int = 1) -> None:
    endpoint = persistent_endpoint(root, "seed")
    endpoint.query_results.add_queries(query(index, bytes(512)) for index in range(count))
    endpoint.close()


def _empty(root: Path) -> None:
    persistent_endpoint(root, "empty").close()


def test_receiver_crash_before_apply_has_no_mutation_and_recovers(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source); _empty(receiver)
    crashed = run_udp_contact(source, receiver, kind=RecordKind.QUERY,
                              responder_extra=("--crash-after-reassembly",))
    check = reopen_endpoint(receiver, "after-crash")
    assert crashed.responder_returncode == 93
    assert check.query_results.query_count == 0
    check.close()
    recovered = run_udp_contact(source, receiver, kind=RecordKind.QUERY)
    check = reopen_endpoint(receiver, "after-recovery")
    assert recovered.initiator_returncode == recovered.responder_returncode == 0
    assert check.query_results.query_count == 1
    check.close()


def test_receiver_crash_after_commit_preserves_durable_progress(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source); _empty(receiver)
    crashed = run_udp_contact(source, receiver, kind=RecordKind.QUERY,
                              responder_extra=("--crash-after-commit",))
    check = reopen_endpoint(receiver, "after-crash")
    assert crashed.responder_returncode == 94
    assert check.query_results.query_count == 1
    check.close()
    fresh = run_udp_contact(source, receiver, kind=RecordKind.QUERY)
    check = reopen_endpoint(receiver, "fresh")
    assert fresh.initiator_returncode == fresh.responder_returncode == 0
    assert check.query_results.query_count == 1
    check.close()


def test_interrupted_fallback_and_both_restart_use_durable_state(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, 100); _empty(receiver)
    first = run_udp_contact(source, receiver, kind=RecordKind.QUERY,
                            responder_extra=("--crash-after-commit",))
    check = reopen_endpoint(receiver, "partial")
    count = check.query_results.query_count
    check.close()
    assert first.responder_returncode == 94
    assert 0 < count < 100
    contacts = 0
    while count < 100:
        contacts += 1
        report = run_udp_contact(source, receiver, kind=RecordKind.QUERY)
        assert report.initiator_returncode == report.responder_returncode == 0
        check = reopen_endpoint(receiver, "fresh-process-pair")
        count = check.query_results.query_count
        check.close()
        assert contacts <= 3
    assert count == 100


def test_sender_crash_after_send_is_resolved_by_receiver_durable_state(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source); _empty(receiver)
    crashed = run_udp_contact(source, receiver, kind=RecordKind.QUERY,
                              initiator_extra=("--crash-after-send-batch", "2"))
    check = reopen_endpoint(receiver, "after-sender-crash")
    assert crashed.initiator_returncode == 95
    assert check.query_results.query_count == 1
    check.close()


def test_sender_exit_immediately_after_udp_send_is_not_delivery_evidence(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source); _empty(receiver)
    crashed = run_udp_contact(
        source, receiver, kind=RecordKind.QUERY,
        initiator_extra=("--crash-after-initial-send",),
    )
    assert crashed.initiator_returncode == 96
    check = reopen_endpoint(receiver, "after-send")
    assert check.query_results.query_count == 0
    check.close()
    fresh = run_udp_contact(source, receiver, kind=RecordKind.QUERY)
    check = reopen_endpoint(receiver, "fresh-after-send")
    assert fresh.initiator_returncode == fresh.responder_returncode == 0
    assert check.query_results.query_count == 1
    check.close()
    fresh = run_udp_contact(source, receiver, kind=RecordKind.QUERY)
    check = reopen_endpoint(receiver, "fresh")
    assert fresh.initiator_returncode == fresh.responder_returncode == 0
    assert check.query_results.query_count == 1
    check.close()


@pytest.mark.parametrize("action", ("PASS", "DUPLICATE", "REORDER", "DELAY"))
def test_real_udp_relay_impairments_that_deliver_all_frames_converge(
    tmp_path: Path, action: str,
) -> None:
    source, receiver = tmp_path / f"source-{action}", tmp_path / f"receiver-{action}"
    _seed(source); _empty(receiver)
    report = run_udp_relay_contact(source, receiver, kind=RecordKind.QUERY, action=action)
    check = reopen_endpoint(receiver, "verify")
    try:
        assert report.initiator_returncode == report.responder_returncode == 0
        assert report.relay is not None and int(report.relay["forwarded"]) > 0
        assert check.query_results.query_count == 1
    finally:
        check.close()


@pytest.mark.parametrize("action", ("DROP", "PERMANENT_DROP", "CORRUPT"))
def test_udp_loss_or_corruption_never_causes_false_convergence(
    tmp_path: Path, action: str,
) -> None:
    source, receiver = tmp_path / f"source-{action}", tmp_path / f"receiver-{action}"
    _seed(source); _empty(receiver)
    report = run_udp_relay_contact(source, receiver, kind=RecordKind.QUERY, action=action)
    check = reopen_endpoint(receiver, "verify")
    try:
        assert check.query_results.query_count == 0
        assert report.relay is not None
        affected = int(report.relay.get("dropped", 0)) + int(
            report.relay.get("corrupted", 0)
        )
        assert affected >= 1
        if action != "PERMANENT_DROP":
            assert affected == 1
    finally:
        check.close()


def test_lost_compact_datagram_is_transport_failure_not_capacity_evidence(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, 100); _empty(receiver)
    report = run_udp_relay_contact(source, receiver, kind=RecordKind.QUERY, action="DROP")
    statuses = tuple(report.initiator.get("compact_statuses", ())) + tuple(
        report.responder.get("compact_statuses", ())
    )
    check = reopen_endpoint(receiver, "verify")
    try:
        assert "CAPACITY_EXCEEDED" not in statuses
        assert check.query_results.query_count == 0
    finally:
        check.close()


def test_loss_during_exact_fallback_preserves_only_complete_messages(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, 100); _empty(receiver)
    # The 797-byte compact message uses 11 frames at MTU 128. Drop A's
    # twelfth datagram without giving the relay B4 or B2 semantics.
    report = run_udp_relay_contact(
        source, receiver, kind=RecordKind.QUERY,
        action="DROP_A_INDEX", drop_index=12,
    )
    statuses = tuple(report.initiator.get("compact_statuses", ())) + tuple(
        report.responder.get("compact_statuses", ())
    )
    check = reopen_endpoint(receiver, "verify-fallback-loss")
    try:
        assert "CAPACITY_EXCEEDED" in statuses
        assert report.relay is not None and report.relay["dropped"] == 1
        assert check.query_results.query_count == 0
    finally:
        check.close()


def test_semantic_blind_udp_mule_with_restart(tmp_path: Path) -> None:
    a_root, b_root, c_root = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    _seed(a_root); _empty(b_root); _empty(c_root)
    ac = run_udp_contact(a_root, c_root, kind=RecordKind.QUERY)
    cb = run_udp_contact(c_root, b_root, kind=RecordKind.QUERY)
    b = reopen_endpoint(b_root, "result")
    carried = result(0, 0, (b"selected-reference-key",))
    b.query_results.add_result(carried); b.close()
    bc = run_udp_contact(b_root, c_root, kind=RecordKind.RESULT)
    ca = run_udp_contact(c_root, a_root, kind=RecordKind.RESULT)
    a = reopen_endpoint(a_root, "verify")
    try:
        assert all(report.initiator_returncode == report.responder_returncode == 0
                   for report in (ac, cb, bc, ca))
        assert a.query_results.get_result(carried.identity) == carried
    finally:
        a.close()
