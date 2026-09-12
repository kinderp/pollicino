from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time

import pytest
import random

from pollicino.net.fragmentation import (
    FRAGMENT_HEADER_BYTES,
    EphemeralFragmentReassembler,
    FragmentFrame,
    fragment_message,
)
from pollicino.net.unix_stream import (
    MAX_STREAM_FRAME_BYTES,
    UnixStreamAdapter,
    UnixStreamAddressError,
    UnixStreamBoundsError,
    UnixStreamEOF,
    UnixStreamError,
    UnixStreamFrameError,
    UnixStreamListener,
    UnixStreamTimeout,
)
from test_px15_pn_b4_fragment_codec import MTUS, compact_summary, maximum_message, messages


def _pair(
    *, mtu: int = 128, read_size: int | None = None, write_chunk: int | None = None,
) -> tuple[UnixStreamAdapter, UnixStreamAdapter]:
    left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    return (
        UnixStreamAdapter(
            left, max_frame_bytes=mtu, timeout=0.1,
            max_read_bytes=read_size, max_write_chunk_bytes=write_chunk,
        ),
        UnixStreamAdapter(
            right, max_frame_bytes=mtu, timeout=0.1,
            max_read_bytes=read_size, max_write_chunk_bytes=write_chunk,
        ),
    )


def _frame(mtu: int = 128, message: bytes | None = None) -> bytes:
    encoded = messages()[0] if message is None else message
    return fragment_message(encoded, max_frame_bytes=mtu)[0].encode()


def test_contract_uses_existing_b4_header_without_outer_framing() -> None:
    assert FRAGMENT_HEADER_BYTES == 52
    assert MAX_STREAM_FRAME_BYTES == 4096
    frame = _frame()
    assert len(frame) == FRAGMENT_HEADER_BYTES + len(FragmentFrame.decode(frame, max_frame_bytes=128).payload)


@pytest.mark.parametrize("mtu", (53, *MTUS))
def test_every_registered_b4_ceiling_roundtrips_over_real_stream(mtu: int) -> None:
    sender, receiver = _pair(mtu=mtu)
    encoded = compact_summary()
    reassembler = EphemeralFragmentReassembler(max_frame_bytes=mtu)
    completed = None
    try:
        for value in fragment_message(encoded, max_frame_bytes=mtu):
            frame = value.encode()
            assert sender.send_frame(frame) == len(frame)
            result = reassembler.add(receiver.receive_frame())
            completed = result.complete_message or completed
        assert completed == encoded
        assert sender.accounting.stream_bytes_written == receiver.accounting.stream_bytes_read
    finally:
        sender.close(); receiver.close()


def test_one_byte_writes_and_reads_preserve_one_frame() -> None:
    sender, receiver = _pair(mtu=128, read_size=1, write_chunk=1)
    frame = _frame()
    try:
        sender.send_frame(frame)
        assert receiver.receive_frame() == frame
        assert sender.accounting.write_calls == len(frame)
        assert receiver.accounting.read_calls == len(frame)
        assert receiver.accounting.frames_received == 1
    finally:
        sender.close(); receiver.close()


def test_concatenated_frames_in_one_read_are_emitted_individually() -> None:
    raw, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    receiver = UnixStreamAdapter(peer, max_frame_bytes=128, timeout=0.1, max_read_bytes=4096)
    frames = tuple(frame.encode() for frame in fragment_message(compact_summary(), max_frame_bytes=128))
    try:
        raw.sendall(b"".join(frames))
        assert tuple(receiver.receive_frame() for _ in frames) == frames
        assert receiver.accounting.read_calls < len(frames)
    finally:
        raw.close(); receiver.close()


@pytest.mark.parametrize("cut", (1, FRAGMENT_HEADER_BYTES - 1, FRAGMENT_HEADER_BYTES + 1))
def test_eof_inside_header_or_payload_fails_closed(cut: int) -> None:
    raw, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    receiver = UnixStreamAdapter(peer, max_frame_bytes=128, timeout=0.1, max_read_bytes=7)
    frame = _frame()
    raw.sendall(frame[:cut]); raw.shutdown(socket.SHUT_WR)
    try:
        with pytest.raises(UnixStreamFrameError, match="EOF inside B4 frame"):
            receiver.receive_frame()
        assert receiver.accounting.frames_received == 0
    finally:
        raw.close(); receiver.close()


def test_clean_eof_after_complete_frame_keeps_frame_valid() -> None:
    raw, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    receiver = UnixStreamAdapter(peer, max_frame_bytes=128, timeout=0.1)
    frame = _frame()
    raw.sendall(frame); raw.shutdown(socket.SHUT_WR)
    try:
        assert receiver.receive_frame() == frame
        with pytest.raises(UnixStreamEOF):
            receiver.receive_frame()
    finally:
        raw.close(); receiver.close()


def test_complete_frames_before_partial_final_remain_available() -> None:
    raw, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    receiver = UnixStreamAdapter(peer, max_frame_bytes=128, timeout=0.1, max_read_bytes=4096)
    frames = tuple(frame.encode() for frame in fragment_message(compact_summary(), max_frame_bytes=128))
    raw.sendall(b"".join(frames) + frames[0][:17]); raw.shutdown(socket.SHUT_WR)
    try:
        assert tuple(receiver.receive_frame() for _ in frames) == frames
        with pytest.raises(UnixStreamFrameError):
            receiver.receive_frame()
    finally:
        raw.close(); receiver.close()


def test_invalid_magic_terminates_without_resynchronization() -> None:
    raw, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    receiver = UnixStreamAdapter(peer, max_frame_bytes=128, timeout=0.1)
    bad = bytearray(_frame()); bad[0] ^= 1
    raw.sendall(bytes(bad) + _frame())
    try:
        with pytest.raises(UnixStreamFrameError, match="invalid fragment magic"):
            receiver.receive_frame()
        started = time.monotonic()
        with pytest.raises(UnixStreamFrameError, match="invalid fragment magic"):
            receiver.receive_frame()
        assert time.monotonic() - started < 0.05
        assert receiver.accounting.frames_received == 0
    finally:
        raw.close(); receiver.close()


def test_oversized_payload_declaration_rejected_before_body_read() -> None:
    raw, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    receiver = UnixStreamAdapter(peer, max_frame_bytes=128, timeout=0.1)
    header = bytearray(_frame()[:FRAGMENT_HEADER_BYTES])
    header[46:48] = (77).to_bytes(2, "big")
    raw.sendall(header)
    try:
        with pytest.raises(UnixStreamFrameError, match="payload exceeds MTU"):
            receiver.receive_frame()
        assert receiver.accounting.stream_bytes_read == FRAGMENT_HEADER_BYTES
        assert receiver.accounting.maximum_buffered_bytes <= receiver.max_buffer_bytes
    finally:
        raw.close(); receiver.close()


@pytest.mark.parametrize("offset", (5, -1))
def test_header_or_payload_corruption_fails_closed(offset: int) -> None:
    raw, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    receiver = UnixStreamAdapter(peer, max_frame_bytes=128, timeout=0.1)
    bad = bytearray(_frame()); bad[offset] ^= 1
    raw.sendall(bad)
    try:
        with pytest.raises(UnixStreamFrameError):
            receiver.receive_frame()
        assert receiver.accounting.frames_received == 0
    finally:
        raw.close(); receiver.close()


def test_deleted_byte_desynchronization_fails_current_stream() -> None:
    raw, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    receiver = UnixStreamAdapter(peer, max_frame_bytes=128, timeout=0.1, max_read_bytes=4096)
    first, second = _frame(), _frame()
    raw.sendall(first[:60] + first[61:] + second)
    try:
        with pytest.raises(UnixStreamFrameError):
            receiver.receive_frame()
        assert receiver.accounting.frames_received == 0
    finally:
        raw.close(); receiver.close()


def test_fixed_seed_random_write_and_read_segmentation_is_exact() -> None:
    raw, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    receiver = UnixStreamAdapter(peer, max_frame_bytes=128, timeout=0.5, max_read_bytes=17)
    frames = tuple(frame.encode() for frame in fragment_message(compact_summary(), max_frame_bytes=128))
    wire = b"".join(frames)
    sizes: list[int] = []
    randomizer = random.Random(20260912)
    remaining = len(wire)
    while remaining:
        value = min(remaining, randomizer.randint(1, 31))
        sizes.append(value); remaining -= value

    def write() -> None:
        offset = 0
        for size in sizes:
            raw.sendall(wire[offset : offset + size])
            offset += size

    thread = threading.Thread(target=write)
    thread.start()
    try:
        assert tuple(receiver.receive_frame() for _ in frames) == frames
        thread.join(1)
        assert not thread.is_alive()
    finally:
        raw.close(); receiver.close()


def test_timeout_is_finite_transport_outcome() -> None:
    sender, receiver = _pair()
    started = time.monotonic()
    try:
        with pytest.raises(UnixStreamTimeout):
            receiver.receive_frame()
        assert time.monotonic() - started < 0.5
    finally:
        sender.close(); receiver.close()


def test_outgoing_nonframe_and_oversize_are_rejected_locally() -> None:
    sender, receiver = _pair()
    try:
        with pytest.raises(UnixStreamFrameError):
            sender.send_frame(b"x")
        with pytest.raises(UnixStreamBoundsError):
            sender.send_frame(bytes(129))
    finally:
        sender.close(); receiver.close()


def test_half_close_preserves_opposite_direction() -> None:
    left, right = _pair()
    frame = _frame()
    try:
        left.send_frame(frame); left.shutdown_write()
        assert right.receive_frame() == frame
        with pytest.raises(UnixStreamEOF):
            right.receive_frame()
        right.send_frame(frame)
        assert left.receive_frame() == frame
    finally:
        left.close(); right.close()


def test_listener_connect_cleanup_and_active_collision() -> None:
    with tempfile.TemporaryDirectory(prefix="px17-path-", dir="/tmp") as raw:
        path = Path(raw) / "stream.sock"
        listener = UnixStreamListener(path, max_frame_bytes=128, timeout=0.2)
        accepted: list[UnixStreamAdapter] = []
        thread = threading.Thread(target=lambda: accepted.append(listener.accept()))
        thread.start()
        client = UnixStreamAdapter.connect(path, max_frame_bytes=128, timeout=0.2)
        thread.join(1)
        try:
            assert accepted
            with pytest.raises(UnixStreamAddressError):
                UnixStreamListener(path, max_frame_bytes=128)
            assert path.stat().st_mode & 0o777 == 0o600
        finally:
            client.close()
            for value in accepted: value.close()
            listener.close()
        assert not path.exists() and not Path(str(path) + ".owner").exists()


def test_missing_listener_fails_finitely(tmp_path: Path) -> None:
    with pytest.raises(UnixStreamAddressError):
        UnixStreamAdapter.connect(tmp_path / "missing.sock", max_frame_bytes=128, timeout=0.02)


def test_unowned_path_is_never_removed(tmp_path: Path) -> None:
    path = tmp_path / "foreign"
    path.write_bytes(b"not ours")
    with pytest.raises(UnixStreamAddressError):
        UnixStreamListener(path, max_frame_bytes=128, recover_stale=True)
    assert path.read_bytes() == b"not ours"


def test_owned_stale_listener_can_be_recovered() -> None:
    with tempfile.TemporaryDirectory(prefix="px17-stale-", dir="/tmp") as raw:
        path = Path(raw) / "stale.sock"
        code = (
            "from pathlib import Path; import os; "
            "from pollicino.net.unix_stream import UnixStreamListener; "
            f"UnixStreamListener(Path({str(path)!r}), max_frame_bytes=128); os._exit(0)"
        )
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(Path(__file__).parents[1] / "src")
        subprocess.run([sys.executable, "-c", code], check=True, env=environment)
        recovered = UnixStreamListener(path, max_frame_bytes=128, recover_stale=True)
        recovered.close()
        assert not path.exists()


def test_backpressure_ends_within_bounded_send_opportunity() -> None:
    raw, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    raw.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
    sender = UnixStreamAdapter(raw, max_frame_bytes=4096, timeout=0.02)
    frame = fragment_message(maximum_message(), max_frame_bytes=4096)[0].encode()
    successes = 0
    started = time.monotonic()
    try:
        with pytest.raises(UnixStreamError):
            while successes < 10_000:
                sender.send_frame(frame)
                successes += 1
        assert successes < 10_000
        assert time.monotonic() - started < 1
        assert sender.accounting.send_failures >= 1
    finally:
        peer.close(); sender.close()


def test_peer_exit_after_connect_is_bounded_broken_pipe() -> None:
    raw, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    sender = UnixStreamAdapter(raw, max_frame_bytes=128, timeout=0.05)
    peer.close()
    try:
        with pytest.raises(UnixStreamError):
            sender.send_frame(_frame())
        assert sender.accounting.send_failures == 1
    finally:
        sender.close()


def test_slow_reader_does_not_require_user_space_queue() -> None:
    raw, peer = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    raw.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
    sender = UnixStreamAdapter(raw, max_frame_bytes=4096, timeout=0.5)
    frame = fragment_message(maximum_message(), max_frame_bytes=4096)[0].encode()
    received = bytearray()

    def drain() -> None:
        while len(received) < len(frame):
            block = peer.recv(17)
            if not block:
                break
            received.extend(block)
            time.sleep(0.0001)

    thread = threading.Thread(target=drain)
    thread.start()
    try:
        assert sender.send_frame(frame) == len(frame)
        thread.join(1)
        assert bytes(received) == frame
        assert sender.accounting.frames_sent == 1
    finally:
        peer.close(); sender.close()
