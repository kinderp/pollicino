from __future__ import annotations

from pathlib import Path

import pytest

from pollicino.net.endpoint import RecordKind
from px10_support import persistent_endpoint, query, result, reopen_endpoint
from px16_support import run_relay_contact, run_unix_contact


def _seed(root: Path, count: int) -> None:
    endpoint = persistent_endpoint(root, "seed")
    endpoint.query_results.add_queries(query(index) for index in range(count))
    endpoint.close()


def test_pass_relay_matches_direct_kernel_transport(tmp_path: Path) -> None:
    direct_source, direct_receiver = tmp_path / "ds", tmp_path / "dr"
    relay_source, relay_receiver = tmp_path / "rs", tmp_path / "rr"
    _seed(direct_source, 10); _seed(relay_source, 10)
    persistent_endpoint(direct_receiver, "dr").close(); persistent_endpoint(relay_receiver, "rr").close()
    direct = run_unix_contact(direct_source, direct_receiver, kind=RecordKind.QUERY)
    relayed = run_relay_contact(relay_source, relay_receiver, kind=RecordKind.QUERY)
    one = reopen_endpoint(direct_receiver, "one"); two = reopen_endpoint(relay_receiver, "two")
    assert direct.initiator_returncode == relayed.initiator_returncode == 0
    assert one.query_results.canonical_state() == two.query_results.canonical_state()
    assert relayed.relay and relayed.relay["application_semantics"] == 0
    one.close(); two.close()


@pytest.mark.parametrize("action", ("DUP", "REORDER", "DELAY"))
def test_duplicate_reorder_and_delay_whole_datagrams(tmp_path: Path, action: str) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, 10); persistent_endpoint(receiver, "receiver").close()
    report = run_relay_contact(source, receiver, kind=RecordKind.QUERY, actions=(action,))
    check = reopen_endpoint(receiver, "verify")
    assert report.initiator_returncode == report.responder_returncode == 0
    assert check.query_results.query_count == 10
    check.close()


@pytest.mark.parametrize("action", ("DROP", "CORRUPT"))
def test_compact_datagram_loss_or_corruption_is_not_capacity_evidence(
    tmp_path: Path, action: str
) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, 20); persistent_endpoint(receiver, "receiver").close()
    report = run_relay_contact(source, receiver, kind=RecordKind.QUERY, actions=(action,))
    check = reopen_endpoint(receiver, "verify")
    assert check.query_results.query_count == 0
    assert report.initiator.get("decision") == "COMPACT_10"
    check.close()


def test_permanent_loss_contacts_return_without_false_convergence(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, 1); persistent_endpoint(receiver, "receiver").close()
    for _ in range(3):
        run_relay_contact(source, receiver, kind=RecordKind.QUERY, actions=("DROP",))
    check = reopen_endpoint(receiver, "verify")
    assert check.query_results.query_count == 0
    check.close()


def test_datagram_loss_during_exact_fallback_preserves_only_full_commits(
    tmp_path: Path,
) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, 20); persistent_endpoint(receiver, "receiver").close()
    run_relay_contact(
        source,
        receiver,
        kind=RecordKind.QUERY,
        actions=tuple(["PASS"] * 24 + ["DROP"]),
    )
    before = reopen_endpoint(receiver, "before")
    committed = before.query_results.query_count
    before.close()
    run_unix_contact(source, receiver, kind=RecordKind.QUERY)
    after = reopen_endpoint(receiver, "after")
    assert committed <= after.query_results.query_count == 20
    after.close()


def test_crash_before_apply_then_fresh_contact_recovers(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, 1); persistent_endpoint(receiver, "receiver").close()
    first = run_unix_contact(
        source, receiver, kind=RecordKind.QUERY,
        receiver_extra=("--crash-after-reassembly",),
    )
    check = reopen_endpoint(receiver, "before"); assert first.responder_returncode == 93 and check.query_results.query_count == 0; check.close()
    second = run_unix_contact(source, receiver, kind=RecordKind.QUERY)
    check = reopen_endpoint(receiver, "after"); assert second.initiator_returncode == 0 and check.query_results.query_count == 1; check.close()


def test_crash_after_commit_sender_uncertainty_skips_on_fresh_contact(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, 1); persistent_endpoint(receiver, "receiver").close()
    first = run_unix_contact(
        source, receiver, kind=RecordKind.QUERY,
        receiver_extra=("--crash-after-commit",),
    )
    assert first.responder_returncode == 94
    second = run_unix_contact(source, receiver, kind=RecordKind.QUERY)
    check = reopen_endpoint(receiver, "verify")
    assert second.responder.get("native_commits") == 0
    assert check.query_results.query_count == 1
    check.close()


def test_semantic_blind_real_datagram_mule(tmp_path: Path) -> None:
    a_root, b_root, c_root = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    _seed(a_root, 1); persistent_endpoint(b_root, "b").close(); persistent_endpoint(c_root, "c").close()
    assert run_unix_contact(a_root, c_root, kind=RecordKind.QUERY).responder_returncode == 0
    assert run_unix_contact(c_root, b_root, kind=RecordKind.QUERY).responder_returncode == 0
    b = reopen_endpoint(b_root, "application"); b.query_results.add_result(result(0, 1)); b.close()
    assert run_unix_contact(b_root, c_root, kind=RecordKind.RESULT).responder_returncode == 0
    assert run_unix_contact(c_root, a_root, kind=RecordKind.RESULT).responder_returncode == 0
    a = reopen_endpoint(a_root, "verify")
    assert a.query_results.get_result(result(0, 1).identity) == result(0, 1)
    a.close()
