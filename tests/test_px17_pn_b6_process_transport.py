from __future__ import annotations

from pathlib import Path
import socket

import pytest

from pollicino.net.endpoint import RecordKind
from pollicino.net.fragmentation import EphemeralFragmentReassembler, fragment_message
from pollicino.net.unix_stream import UnixStreamAdapter
from px10_support import persistent_endpoint, query, reference, reopen_endpoint, result
from px16_support import run_unix_contact
from px17_support import run_stream_contact, run_stream_reference_contact
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
    queries = run_stream_contact(source_root, receiver_root, kind=RecordKind.QUERY, mtu=128)
    results = run_stream_contact(source_root, receiver_root, kind=RecordKind.RESULT, mtu=128)
    source = reopen_endpoint(source_root, "add-reference")
    chosen, ignored = reference(7, bytes(700)), reference(8)
    source.catalog.add_many((chosen, ignored)); source.close()
    references = run_stream_reference_contact(
        source_root, receiver_root, (chosen.logical_key,), mtu=128
    )
    receiver = reopen_endpoint(receiver_root, "verify")
    try:
        assert queries.initiator_returncode == queries.responder_returncode == 0
        assert results.initiator_returncode == results.responder_returncode == 0
        assert references.initiator_returncode == references.responder_returncode == 0
        assert receiver.query_results.get_query(query(0).query_id) == query(0)
        assert receiver.query_results.get_result(result(0, 0).identity) == result(0, 0)
        assert receiver.catalog.get(chosen.logical_key) == chosen
        assert ignored.logical_key not in receiver.catalog
    finally:
        receiver.close()


@pytest.mark.parametrize("mtu", (53, 64, 128, 256, 512, 1024, 1500, 4096))
def test_b4_ceiling_matrix_crosses_independent_stream_processes(
    tmp_path: Path, mtu: int,
) -> None:
    source, receiver = tmp_path / f"source-{mtu}", tmp_path / f"receiver-{mtu}"
    _seed(source, queries=1); _empty(receiver)
    report = run_stream_contact(source, receiver, kind=RecordKind.QUERY, mtu=mtu)
    check = reopen_endpoint(receiver, "verify")
    try:
        assert report.initiator_returncode == report.responder_returncode == 0
        assert check.query_results.query_count == 1
    finally:
        check.close()


def test_one_byte_process_reads_and_writes_are_semantically_neutral(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, queries=10); _empty(receiver)
    report = run_stream_contact(
        source, receiver, kind=RecordKind.QUERY, mtu=128, read_size=1, write_chunk=1
    )
    check = reopen_endpoint(receiver, "verify")
    try:
        assert report.initiator_returncode == report.responder_returncode == 0
        assert check.query_results.query_count == 10
        assert int(report.initiator["os_write_calls"]) > int(report.initiator["b4_frames_sent"])
        assert int(report.responder["os_read_calls"]) > int(report.responder["protocol_messages_in"])
    finally:
        check.close()


@pytest.mark.parametrize(
    ("count", "expected_status"),
    ((0, "EQUAL"), (1, "DECODED"), (10, "DECODED"), (100, "CAPACITY_EXCEEDED")),
)
def test_adaptive_compact_and_exact_fallback_cross_stream(
    tmp_path: Path, count: int, expected_status: str,
) -> None:
    source, receiver = tmp_path / f"source-{count}", tmp_path / f"receiver-{count}"
    _seed(source, queries=count); _empty(receiver)
    report = run_stream_contact(source, receiver, kind=RecordKind.QUERY, mtu=128)
    check = reopen_endpoint(receiver, "verify")
    try:
        assert report.initiator_returncode == report.responder_returncode == 0
        observed = check.query_results.query_count
        statuses = tuple(report.initiator["compact_statuses"]) + tuple(
            report.responder["compact_statuses"]
        )
        assert expected_status in statuses
    finally:
        check.close()
    contacts = 1
    while observed < count:
        contacts += 1
        later = run_stream_contact(source, receiver, kind=RecordKind.QUERY, mtu=128)
        assert later.initiator_returncode == later.responder_returncode == 0
        check = reopen_endpoint(receiver, "verify-later")
        observed = check.query_results.query_count
        check.close()
        assert contacts <= 3
    assert observed == count


def test_105_record_exact_fairness_across_fresh_connections(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, queries=105); _empty(receiver)
    contacts = 0
    while True:
        contacts += 1
        report = run_stream_contact(
            source, receiver, kind=RecordKind.QUERY, mtu=256, exact=True
        )
        assert report.initiator_returncode == report.responder_returncode == 0
        check = reopen_endpoint(receiver, "count")
        count = check.query_results.query_count
        check.close()
        if count == 105:
            break
        assert contacts <= 3
    assert contacts == 2


def test_maximum_b2_message_crosses_real_stream_as_many_b4_frames() -> None:
    raw, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    sender = UnixStreamAdapter(raw, max_frame_bytes=128, timeout=0.5)
    receiver = UnixStreamAdapter(peer, max_frame_bytes=128, timeout=0.5)
    encoded = maximum_message()
    frames = tuple(frame.encode() for frame in fragment_message(encoded, max_frame_bytes=128))
    reassembler = EphemeralFragmentReassembler(max_frame_bytes=128)
    complete = None
    try:
        for frame in frames:
            sender.send_frame(frame)
            result = reassembler.add(receiver.receive_frame())
            complete = result.complete_message or complete
        assert len(frames) == 385
        assert complete == encoded
        assert sender.accounting.frame_bytes_sent == receiver.accounting.frame_bytes_received
    finally:
        sender.close(); receiver.close()


def test_unix_datagram_and_stream_canonical_state_are_equal(tmp_path: Path) -> None:
    stream_source, stream_receiver = tmp_path / "stream-source", tmp_path / "stream-receiver"
    datagram_source, datagram_receiver = tmp_path / "dgram-source", tmp_path / "dgram-receiver"
    _seed(stream_source, queries=10); _empty(stream_receiver)
    _seed(datagram_source, queries=10); _empty(datagram_receiver)
    stream = run_stream_contact(stream_source, stream_receiver, kind=RecordKind.QUERY, mtu=128)
    datagram = run_unix_contact(datagram_source, datagram_receiver, kind=RecordKind.QUERY, mtu=128)
    left = reopen_endpoint(stream_receiver, "verify-stream")
    right = reopen_endpoint(datagram_receiver, "verify-dgram")
    try:
        assert stream.initiator_returncode == stream.responder_returncode == 0
        assert datagram.initiator_returncode == datagram.responder_returncode == 0
        assert left.query_results.state_digest == right.query_results.state_digest
    finally:
        left.close(); right.close()


def test_capacity_10_frame_counts_are_transport_family_independent() -> None:
    encoded = compact_summary()
    assert len(encoded) == 797
    assert {
        mtu: len(fragment_message(encoded, max_frame_bytes=mtu))
        for mtu in (53, 64, 128, 256, 512, 1024, 1500, 4096)
    } == {53: 797, 64: 67, 128: 11, 256: 4, 512: 2, 1024: 1, 1500: 1, 4096: 1}


@pytest.mark.parametrize("count", (1_000, 10_000))
def test_large_unknown_difference_fails_compact_detectably_and_stays_bounded(
    tmp_path: Path, count: int,
) -> None:
    source, receiver = tmp_path / f"source-{count}", tmp_path / f"receiver-{count}"
    _seed(source, queries=count); _empty(receiver)
    report = run_stream_contact(
        source, receiver, kind=RecordKind.QUERY, mtu=128, max_messages=20
    )
    statuses = tuple(report.initiator.get("compact_statuses", ())) + tuple(
        report.responder.get("compact_statuses", ())
    )
    check = reopen_endpoint(receiver, "verify")
    try:
        assert "CAPACITY_EXCEEDED" in statuses
        assert check.query_results.query_count < count
        assert report.initiator_returncode in (0, 2)
        assert report.responder_returncode in (0, 2)
        assert int(report.initiator["protocol_messages_in"]) <= 20
        assert int(report.responder["protocol_messages_in"]) <= 20
        assert report.initiator["decision"] == "COMPACT_10"
    finally:
        check.close()
