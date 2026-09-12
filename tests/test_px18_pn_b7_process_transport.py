from __future__ import annotations

from pathlib import Path
import socket

import pytest

from pollicino.net.endpoint import RecordKind
from pollicino.net.fragmentation import EphemeralFragmentReassembler, fragment_message
from pollicino.net.udp import UDPAdapter
from px10_support import persistent_endpoint, query, reference, reopen_endpoint, result
from px16_support import run_unix_contact
from px17_support import run_stream_contact
from px18_support import run_udp_contact, run_udp_reference_contact
from test_px15_pn_b4_fragment_codec import compact_summary, maximum_message


def _seed(root: Path, *, queries: int = 0, results: int = 0) -> None:
    endpoint = persistent_endpoint(root, "seed")
    endpoint.query_results.add_queries(query(index) for index in range(queries))
    endpoint.query_results.add_results(result(index, index) for index in range(results))
    endpoint.close()


def _empty(root: Path) -> None:
    persistent_endpoint(root, "empty").close()


def test_independent_process_query_result_and_explicit_reference(tmp_path: Path) -> None:
    source_root, receiver_root = tmp_path / "source", tmp_path / "receiver"
    _seed(source_root, queries=1, results=1); _empty(receiver_root)
    queries = run_udp_contact(source_root, receiver_root, kind=RecordKind.QUERY)
    results = run_udp_contact(source_root, receiver_root, kind=RecordKind.RESULT)
    source = reopen_endpoint(source_root, "add-reference")
    chosen, ignored = reference(7, bytes(700)), reference(8)
    source.catalog.add_many((chosen, ignored)); source.close()
    references = run_udp_reference_contact(source_root, receiver_root, (chosen.logical_key,))
    receiver = reopen_endpoint(receiver_root, "verify")
    try:
        assert all(
            report.initiator_returncode == report.responder_returncode == 0
            for report in (queries, results, references)
        )
        assert receiver.query_results.get_query(query(0).query_id) == query(0)
        assert receiver.query_results.get_result(result(0, 0).identity) == result(0, 0)
        assert receiver.catalog.get(chosen.logical_key) == chosen
        assert ignored.logical_key not in receiver.catalog
        assert int(queries.initiator["process_id"]) != int(queries.responder["process_id"])
        assert queries.initiator["shared_endpoint_objects"] == 0
    finally:
        receiver.close()


@pytest.mark.parametrize("mtu", (53, 64, 128, 256, 512, 1024, 1500, 4096))
def test_b4_ceiling_matrix_crosses_independent_udp_processes(
    tmp_path: Path, mtu: int,
) -> None:
    source, receiver = tmp_path / f"source-{mtu}", tmp_path / f"receiver-{mtu}"
    _seed(source, queries=1); _empty(receiver)
    report = run_udp_contact(source, receiver, kind=RecordKind.QUERY, mtu=mtu)
    check = reopen_endpoint(receiver, "verify")
    try:
        assert report.initiator_returncode == report.responder_returncode == 0
        assert check.query_results.query_count == 1
        assert report.initiator["udp_datagrams_sent"] == report.initiator["b4_frames_sent"]
        assert report.initiator["udp_payload_bytes_sent"] == report.initiator["b4_frame_bytes_sent"]
    finally:
        check.close()


@pytest.mark.parametrize(
    ("count", "expected_status"),
    ((0, "EQUAL"), (1, "DECODED"), (10, "DECODED"), (100, "CAPACITY_EXCEEDED")),
)
def test_adaptive_compact_and_exact_fallback_cross_udp(
    tmp_path: Path, count: int, expected_status: str,
) -> None:
    source, receiver = tmp_path / f"source-{count}", tmp_path / f"receiver-{count}"
    _seed(source, queries=count); _empty(receiver)
    report = run_udp_contact(source, receiver, kind=RecordKind.QUERY)
    statuses = tuple(report.initiator.get("compact_statuses", ())) + tuple(
        report.responder.get("compact_statuses", ())
    )
    assert report.initiator_returncode == report.responder_returncode == 0
    assert expected_status in statuses
    contacts = 1
    while True:
        check = reopen_endpoint(receiver, "verify")
        observed = check.query_results.query_count
        check.close()
        if observed == count:
            break
        contacts += 1
        later = run_udp_contact(source, receiver, kind=RecordKind.QUERY)
        assert later.initiator_returncode == later.responder_returncode == 0
        assert contacts <= 3


def test_105_record_exact_fairness_across_fresh_udp_contacts(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, queries=105); _empty(receiver)
    contacts = 0
    while True:
        contacts += 1
        report = run_udp_contact(source, receiver, kind=RecordKind.QUERY, mtu=256, exact=True)
        assert report.initiator_returncode == report.responder_returncode == 0
        check = reopen_endpoint(receiver, "count")
        count = check.query_results.query_count
        check.close()
        if count == 105:
            break
        assert contacts <= 3
    assert contacts == 2


def test_maximum_b2_message_crosses_udp_as_385_datagrams() -> None:
    left = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    right = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    left.bind(("127.0.0.1", 0)); right.bind(("127.0.0.1", 0))
    sender = UDPAdapter(left.getsockname(), right.getsockname(), max_frame_bytes=128,
                        timeout=0.5, active_socket=left)
    receiver = UDPAdapter(right.getsockname(), sender.local_address, max_frame_bytes=128,
                          timeout=0.5, active_socket=right)
    encoded = maximum_message()
    frames = tuple(frame.encode() for frame in fragment_message(encoded, max_frame_bytes=128))
    reassembler = EphemeralFragmentReassembler(max_frame_bytes=128)
    complete = None
    try:
        for frame in frames:
            sender.send_frame(frame)
            outcome = reassembler.add(receiver.receive_frame())
            complete = outcome.complete_message or complete
        assert len(frames) == 385
        assert complete == encoded
        assert sender.accounting.sent_bytes == receiver.accounting.received_bytes
    finally:
        sender.close(); receiver.close()


def test_three_transport_families_have_equal_canonical_state(tmp_path: Path) -> None:
    roots = {
        name: (tmp_path / f"{name}-source", tmp_path / f"{name}-receiver")
        for name in ("unix-dgram", "unix-stream", "udp")
    }
    for source, receiver in roots.values():
        _seed(source, queries=10); _empty(receiver)
    datagram = run_unix_contact(*roots["unix-dgram"], kind=RecordKind.QUERY, mtu=128)
    stream = run_stream_contact(*roots["unix-stream"], kind=RecordKind.QUERY, mtu=128)
    udp = run_udp_contact(*roots["udp"], kind=RecordKind.QUERY, mtu=128)
    endpoints = [reopen_endpoint(receiver, f"verify-{name}") for name, (_, receiver) in roots.items()]
    try:
        assert all(report.initiator_returncode == report.responder_returncode == 0
                   for report in (datagram, stream, udp))
        assert len({endpoint.query_results.state_digest for endpoint in endpoints}) == 1
    finally:
        for endpoint in endpoints:
            endpoint.close()


def test_capacity_10_frame_counts_remain_transport_independent() -> None:
    encoded = compact_summary()
    assert len(encoded) == 797
    assert {mtu: len(fragment_message(encoded, max_frame_bytes=mtu))
            for mtu in (53, 64, 128, 256, 512, 1024, 1500, 4096)} == {
        53: 797, 64: 67, 128: 11, 256: 4,
        512: 2, 1024: 1, 1500: 1, 4096: 1,
    }


@pytest.mark.parametrize("count", (1_000, 10_000))
def test_large_unknown_difference_fails_compact_detectably_and_is_bounded(
    tmp_path: Path, count: int,
) -> None:
    source, receiver = tmp_path / f"source-{count}", tmp_path / f"receiver-{count}"
    _seed(source, queries=count); _empty(receiver)
    report = run_udp_contact(
        source, receiver, kind=RecordKind.QUERY, max_messages=20,
        timeout=2.0 if count == 10_000 else 0.45,
    )
    statuses = tuple(report.initiator.get("compact_statuses", ())) + tuple(
        report.responder.get("compact_statuses", ())
    )
    check = reopen_endpoint(receiver, "verify")
    try:
        if count == 1_000:
            assert "CAPACITY_EXCEEDED" in statuses
            assert report.initiator["decision"] == "COMPACT_10"
        else:
            assert "CAPACITY_EXCEEDED" in statuses
            assert report.initiator["decision"] == "COMPACT_10"
        assert check.query_results.query_count < count
        assert report.initiator_returncode in (0, 2)
        assert report.responder_returncode in (0, 2)
        assert int(report.initiator["protocol_messages_in"]) <= 20
        assert int(report.responder["protocol_messages_in"]) <= 20
    finally:
        check.close()
