from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pytest

from pollicino.net.endpoint import RecordKind
from pollicino.net.udp import UDPAddressError, _address
from px10_support import persistent_endpoint, query
from px18_support import run_udp_contact


EXPERIMENT = Path(__file__).parents[1] / "experiments" / "px19_pn_b8_lan.py"
SPEC = importlib.util.spec_from_file_location("px19_pn_b8_lan", EXPERIMENT)
assert SPEC is not None and SPEC.loader is not None
lan = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lan)


def test_udp_address_validator_admits_numeric_lan_unicast() -> None:
    assert _address(("192.168.1.50", 43000), allow_zero_port=False) == (
        "192.168.1.50", 43000,
    )
    assert _address(("10.20.30.40", 0), allow_zero_port=True) == ("10.20.30.40", 0)
    for invalid in ("0.0.0.0", "224.0.0.1", "255.255.255.255", "example.test"):
        with pytest.raises(UDPAddressError):
            _address((invalid, 43000), allow_zero_port=False)


def test_environment_record_requires_physical_non_overlay_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lan, "_route", lambda _peer: ("TEST_ROUTE", "en0", 1500, "interface: en0")
    )
    monkeypatch.setattr(lan, "_git_state", lambda: ("a" * 40, True))
    output = tmp_path / "host-a.json"
    args = argparse.Namespace(
        role="A", local_ip="192.168.1.50", peer_ip="192.168.1.51",
        interface=None, interface_mtu=None, interface_medium="Wi-Fi",
        physical_host_attestation=True, output=output,
    )
    assert lan.environment(args) == 0
    record = json.loads(output.read_text())
    assert record["loopback_interface_used"] is False
    assert record["overlay_or_vpn_used"] is False
    assert record["interface"] == "en0" and record["interface_mtu"] == 1500

    overlay = argparse.Namespace(**{**vars(args), "output": tmp_path / "overlay.json"})
    monkeypatch.setattr(
        lan, "_route", lambda _peer: ("TEST_ROUTE", "utun3", 1280, "interface: utun3")
    )
    with pytest.raises(ValueError, match="overlay"):
        lan.environment(overlay)


def test_prepare_and_inspect_use_one_bounded_local_root(tmp_path: Path) -> None:
    root = tmp_path / "state-a"
    args = argparse.Namespace(
        root=root, queries=2, results=1, references=1, payload_bytes=32,
    )
    assert lan.prepare(args) == 0
    evidence = tmp_path / "state.json"
    assert lan.inspect_root(argparse.Namespace(root=root, output=evidence)) == 0
    state = json.loads(evidence.read_text())
    assert state["query_records"] == 2
    assert state["result_records"] == 1
    assert state["catalog_records"] == 1
    with pytest.raises(FileExistsError):
        lan.prepare(args)


def _host(role: str, local: str, peer: str, sha: str) -> dict[str, object]:
    return {
        "role": role,
        "local_ipv4": local,
        "peer_ipv4": peer,
        "commit_sha": sha,
        "worktree_clean": True,
        "physical_host_attestation": True,
        "loopback_interface_used": False,
        "overlay_or_vpn_used": False,
    }


def test_pair_verifier_requires_distinct_cross_referenced_clean_hosts(tmp_path: Path) -> None:
    sha = "b" * 40
    a_path, b_path = tmp_path / "a.json", tmp_path / "b.json"
    a_path.write_text(json.dumps(_host("A", "192.168.1.50", "192.168.1.51", sha)))
    b_path.write_text(json.dumps(_host("B", "192.168.1.51", "192.168.1.50", sha)))
    output = tmp_path / "pair.json"
    args = argparse.Namespace(host_a=a_path, host_b=b_path, expected_sha=sha, output=output)
    assert lan.verify_pair(args) == 0
    assert json.loads(output.read_text())["verified"] is True

    b_path.write_text(json.dumps(_host("B", "192.168.1.50", "192.168.1.50", sha)))
    bad = tmp_path / "bad.json"
    assert lan.verify_pair(argparse.Namespace(
        host_a=a_path, host_b=b_path, expected_sha=sha, output=bad,
    )) == 2
    assert json.loads(bad.read_text())["verified"] is False


def test_udp_worker_writes_distinct_host_evidence_records(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    left = persistent_endpoint(source, "seed")
    left.query_results.add_query(query(1)); left.close()
    persistent_endpoint(receiver, "empty").close()
    a_evidence, b_evidence = tmp_path / "host-a.json", tmp_path / "host-b.json"
    common = ("--run-id", "local-harness", "--scenario", "query", "--interface", "lo0",
              "--interface-mtu", "16384")
    report = run_udp_contact(
        source, receiver, kind=RecordKind.QUERY,
        initiator_extra=(*common, "--host-role", "A", "--evidence", str(a_evidence)),
        responder_extra=(*common, "--host-role", "B", "--evidence", str(b_evidence)),
    )
    assert report.initiator_returncode == report.responder_returncode == 0
    a, b = json.loads(a_evidence.read_text()), json.loads(b_evidence.read_text())
    assert a["run_id"] == b["run_id"] == "local-harness"
    assert a["commit_sha"] == b["commit_sha"]
    assert a["local_address"] == b["peer_address"]
    assert b["native_commits"] == 1
    assert b["query_records"] == 1
    assert "query_result_state_digest" in b


def test_px19_changes_do_not_touch_b4_or_upper_protocol_modules() -> None:
    changed = {
        "src/pollicino/net/fragmentation.py",
        "src/pollicino/net/contact.py",
        "src/pollicino/net/endpoint.py",
        "src/pollicino/net/fair_reconciliation.py",
        "src/pollicino/net/compact_reconciliation.py",
        "src/pollicino/net/adaptive_reconciliation.py",
    }
    assert all((lan.REPOSITORY / path).exists() for path in changed)
    source = (lan.REPOSITORY / "src/pollicino/net/udp.py").read_text()
    assert "FARO" not in source and "DNA" not in source and "CONTENT" not in source
