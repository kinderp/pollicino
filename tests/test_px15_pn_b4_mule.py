from __future__ import annotations

from pathlib import Path

from pollicino.net.endpoint import RecordKind
from px10_support import persistent_endpoint, query, reference, result, reopen_endpoint
from px15_support import run_fragmented_contact, run_fragmented_reference_contact


def test_semantic_blind_fragmented_process_mule(tmp_path: Path) -> None:
    a_root, b_root, c_root = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    a = persistent_endpoint(a_root, "a")
    a.query_results.add_query(query(1, bytes(1024))); a.close()
    persistent_endpoint(b_root, "b").close(); persistent_endpoint(c_root, "c").close()
    assert run_fragmented_contact(a_root, c_root, kind=RecordKind.QUERY, mtu=128).completed
    assert run_fragmented_contact(c_root, b_root, kind=RecordKind.QUERY, mtu=128).completed
    b = reopen_endpoint(b_root, "application-b")
    b.query_results.add_result(result(1, 1)); chosen, ignored = reference(1, bytes(512)), reference(2)
    b.catalog.add_many((chosen, ignored)); b.close()
    assert run_fragmented_contact(b_root, c_root, kind=RecordKind.RESULT, mtu=128).completed
    assert run_fragmented_contact(c_root, a_root, kind=RecordKind.RESULT, mtu=128).completed
    assert run_fragmented_reference_contact(b_root, c_root, (chosen.logical_key,), mtu=128).completed
    assert run_fragmented_reference_contact(c_root, a_root, (chosen.logical_key,), mtu=128).completed
    a = reopen_endpoint(a_root, "verify")
    assert a.query_results.get_result(result(1, 1).identity) == result(1, 1)
    assert a.catalog.get(chosen.logical_key) == chosen
    assert ignored.logical_key not in a.catalog
    a.close()
