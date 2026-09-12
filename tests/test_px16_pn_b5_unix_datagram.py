from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile

import pytest

from pollicino.net.endpoint import RecordKind, RecordMessage, encode_message
from pollicino.net.fragmentation import (
    EphemeralFragmentReassembler,
    FragmentDecodeError,
    FragmentFrame,
    fragment_message,
)
from pollicino.net.query import QueryRecord
from pollicino.net.unix_datagram import (
    UnixDatagramAdapter,
    UnixDatagramAddressError,
    UnixDatagramBoundsError,
    UnixDatagramError,
    UnixDatagramSourceError,
    UnixDatagramTimeout,
)
from px10_support import persistent_endpoint, query, reopen_endpoint
from px15_support import compact_summary
from px16_support import REPOSITORY, run_unix_contact
from test_px15_pn_b4_fragment_codec import maximum_message


def _pair(directory: Path, mtu: int = 128):
    a_path, b_path = directory / "a.sock", directory / "b.sock"
    a = UnixDatagramAdapter(a_path, b_path, max_datagram_bytes=mtu, timeout=0.05)
    b = UnixDatagramAdapter(b_path, a_path, max_datagram_bytes=mtu, timeout=0.05)
    return a, b


def _roundtrip(message: bytes, mtu: int, directory: Path) -> tuple[int, bytes]:
    a, b = _pair(directory, mtu)
    receiver = EphemeralFragmentReassembler(max_frame_bytes=mtu)
    completed = None
    try:
        frames = fragment_message(message, max_frame_bytes=mtu)
        for frame in frames:
            encoded = frame.encode(); a.send_frame(encoded)
            received = b.receive_frame()
            assert received == encoded
            completed = receiver.add(received).complete_message or completed
        assert a.accounting.sent == b.accounting.received == len(frames)
        return len(frames), completed
    finally:
        a.close(); b.close()


@pytest.mark.parametrize("mtu", (53, 64, 128, 256, 512, 1024, 1500, 4096))
def test_real_kernel_datagram_mtu_sweep(tmp_path: Path, mtu: int) -> None:
    with tempfile.TemporaryDirectory(prefix="px16-", dir="/tmp") as raw:
        count, completed = _roundtrip(compact_summary(), mtu, Path(raw))
    assert count == len(fragment_message(compact_summary(), max_frame_bytes=mtu))
    assert completed == compact_summary()


def test_maximum_message_crosses_many_real_datagrams() -> None:
    with tempfile.TemporaryDirectory(prefix="px16-", dir="/tmp") as raw:
        count, completed = _roundtrip(maximum_message(), 128, Path(raw))
    assert count == 385 and completed == maximum_message()


def test_exact_ceiling_empty_short_and_oversized_outgoing() -> None:
    with tempfile.TemporaryDirectory(prefix="px16-", dir="/tmp") as raw:
        a, b = _pair(Path(raw), 128)
        try:
            frame = fragment_message(compact_summary(), max_frame_bytes=128)[0].encode()
            assert len(frame) == 128 and a.send_frame(frame) == 128
            assert b.receive_frame() == frame
            with pytest.raises(UnixDatagramBoundsError): a.send_frame(b"")
            with pytest.raises(UnixDatagramBoundsError): a.send_frame(bytes(129))
        finally:
            a.close(); b.close()


def test_oversized_incoming_is_detected_not_silently_truncated() -> None:
    with tempfile.TemporaryDirectory(prefix="px16-", dir="/tmp") as raw:
        root = Path(raw); a_path, b_path = root / "a.sock", root / "b.sock"
        raw_sender = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM); raw_sender.bind(str(a_path))
        b = UnixDatagramAdapter(b_path, a_path, max_datagram_bytes=128, timeout=0.05)
        try:
            raw_sender.sendto(bytes(1024), str(b_path))
            with pytest.raises(UnixDatagramBoundsError): b.receive_frame()
        finally:
            raw_sender.close(); b.close()


@pytest.mark.parametrize("payload", (b"", b"x", bytes(10), bytes(51)))
def test_empty_and_short_datagrams_never_reach_b4(payload: bytes) -> None:
    with tempfile.TemporaryDirectory(prefix="px16-", dir="/tmp") as raw:
        root = Path(raw); a_path, b_path = root / "a.sock", root / "b.sock"
        sender = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM); sender.bind(str(a_path))
        b = UnixDatagramAdapter(b_path, a_path, max_datagram_bytes=128, timeout=0.05)
        try:
            sender.sendto(payload, str(b_path))
            if not payload:
                with pytest.raises(UnixDatagramBoundsError): b.receive_frame()
            else:
                received = b.receive_frame()
                with pytest.raises((FragmentDecodeError, UnixDatagramBoundsError)):
                    FragmentFrame.decode(received, max_frame_bytes=128)
        finally:
            sender.close(); b.close()


def test_timeout_missing_destination_and_unexpected_source() -> None:
    with tempfile.TemporaryDirectory(prefix="px16-", dir="/tmp") as raw:
        root = Path(raw); a_path, missing = root / "a.sock", root / "missing.sock"
        a = UnixDatagramAdapter(a_path, missing, max_datagram_bytes=128, timeout=0.02)
        try:
            with pytest.raises(UnixDatagramError): a.send_frame(b"x")
            with pytest.raises(UnixDatagramTimeout): a.receive_frame()
        finally: a.close()
        expected, receiver_path, foreign = root / "expected.sock", root / "r.sock", root / "foreign.sock"
        expected_sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM); expected_sock.bind(str(expected))
        foreign_sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM); foreign_sock.bind(str(foreign))
        receiver = UnixDatagramAdapter(receiver_path, expected, max_datagram_bytes=128, timeout=0.05)
        try:
            foreign_sock.sendto(b"foreign", str(receiver_path))
            with pytest.raises(UnixDatagramSourceError): receiver.receive_frame()
        finally:
            expected_sock.close(); foreign_sock.close(); receiver.close()


def test_path_lifecycle_collision_cleanup_and_unowned_path_safety() -> None:
    with tempfile.TemporaryDirectory(prefix="px16-", dir="/tmp") as raw:
        root = Path(raw); a_path, b_path = root / "a.sock", root / "b.sock"
        a = UnixDatagramAdapter(a_path, b_path, max_datagram_bytes=128)
        assert a_path.exists() and (root / "a.sock.owner").exists()
        assert a_path.stat().st_mode & 0o777 == 0o600
        with pytest.raises(UnixDatagramAddressError):
            UnixDatagramAdapter(a_path, b_path, max_datagram_bytes=128)
        a.close(); assert not a_path.exists()
        a = UnixDatagramAdapter(a_path, b_path, max_datagram_bytes=128); a.close()
        unowned = root / "ordinary"; unowned.write_text("keep")
        with pytest.raises(UnixDatagramAddressError):
            UnixDatagramAdapter(unowned, b_path, max_datagram_bytes=128, recover_stale=True)
        assert unowned.read_text() == "keep"


def test_owned_stale_socket_from_dead_process_is_recovered() -> None:
    with tempfile.TemporaryDirectory(prefix="px16-", dir="/tmp") as raw:
        root = Path(raw); stale, peer = root / "stale.sock", root / "peer.sock"
        code = (
            "from pathlib import Path; import os; "
            "from pollicino.net.unix_datagram import UnixDatagramAdapter; "
            f"UnixDatagramAdapter(Path({str(stale)!r}), Path({str(peer)!r}), max_datagram_bytes=128); "
            "os._exit(0)"
        )
        environment = dict(os.environ); environment["PYTHONPATH"] = str(REPOSITORY / "src")
        subprocess.run([sys.executable, "-c", code], env=environment, check=True)
        assert stale.exists()
        recovered = UnixDatagramAdapter(
            stale, peer, max_datagram_bytes=128, recover_stale=True
        )
        recovered.close()
        assert not stale.exists()


def _seed(root: Path, count: int) -> None:
    endpoint = persistent_endpoint(root, "seed")
    endpoint.query_results.add_queries(query(index) for index in range(count))
    endpoint.close()


@pytest.mark.parametrize(("count", "expected"), ((0, "COMPACT_10"), (1, "COMPACT_10"), (10, "COMPACT_10"), (20, "COMPACT_10")))
def test_two_independent_processes_reconcile_over_real_datagrams(
    tmp_path: Path, count: int, expected: str
) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, count); persistent_endpoint(receiver, "receiver").close()
    report = run_unix_contact(source, receiver, kind=RecordKind.QUERY, mtu=128)
    check = reopen_endpoint(receiver, "verify")
    assert report.initiator_returncode == report.responder_returncode == 0
    assert report.initiator["decision"] == expected
    assert check.query_results.query_count == count
    assert report.initiator["process_id"] != report.responder["process_id"]
    check.close()


def test_exact_fair_progress_over_real_datagrams_and_fresh_processes(tmp_path: Path) -> None:
    source, receiver = tmp_path / "source", tmp_path / "receiver"
    _seed(source, 105); persistent_endpoint(receiver, "receiver").close()
    counts = []
    for _contact in range(20):
        run_unix_contact(source, receiver, kind=RecordKind.QUERY, mtu=256, exact=True)
        check = reopen_endpoint(receiver, "verify")
        counts.append(check.query_results.query_count)
        check.close()
        if counts[-1] == 105:
            break
    assert counts[-1] == 105
    assert counts == sorted(counts) and len(counts) > 1


def test_receiver_crash_before_apply_and_after_commit(tmp_path: Path) -> None:
    source, before, after = tmp_path / "source", tmp_path / "before", tmp_path / "after"
    _seed(source, 1); persistent_endpoint(before, "before").close(); persistent_endpoint(after, "after").close()
    first = run_unix_contact(source, before, kind=RecordKind.QUERY, receiver_extra=("--crash-after-reassembly",))
    check = reopen_endpoint(before, "verify"); assert first.responder_returncode == 93 and check.query_results.query_count == 0; check.close()
    second = run_unix_contact(source, after, kind=RecordKind.QUERY, receiver_extra=("--crash-after-commit",))
    check = reopen_endpoint(after, "verify"); assert second.responder_returncode == 94 and check.query_results.query_count == 1; check.close()


def test_mtu_mismatch_rejects_oversized_frame_without_mutation() -> None:
    with tempfile.TemporaryDirectory(prefix="px16-", dir="/tmp") as raw:
        root = Path(raw); a_path, b_path = root / "a.sock", root / "b.sock"
        a = UnixDatagramAdapter(a_path, b_path, max_datagram_bytes=512, timeout=0.05)
        b = UnixDatagramAdapter(b_path, a_path, max_datagram_bytes=256, timeout=0.05)
        try:
            frame = fragment_message(maximum_message(), max_frame_bytes=512)[0].encode()
            assert len(frame) == 512; a.send_frame(frame)
            with pytest.raises(UnixDatagramBoundsError): b.receive_frame()
        finally: a.close(); b.close()


def test_backpressure_is_bounded_without_user_queue() -> None:
    with tempfile.TemporaryDirectory(prefix="px16-", dir="/tmp") as raw:
        a, b = _pair(Path(raw), 128)
        attempts = successes = 0
        try:
            frame = fragment_message(compact_summary(), max_frame_bytes=128)[0].encode()
            for _ in range(10_000):
                attempts += 1
                try: a.send_frame(frame); successes += 1
                except UnixDatagramError: break
            assert attempts <= 10_000 and successes < 10_000
        finally: a.close(); b.close()
