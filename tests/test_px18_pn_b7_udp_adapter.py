from __future__ import annotations

import socket
import time

import pytest

from pollicino.net.fragmentation import EphemeralFragmentReassembler, fragment_message
from pollicino.net.udp import UDPAdapter, UDPAddressError, UDPBoundsError, UDPError, UDPTimeout
from test_px15_pn_b4_fragment_codec import compact_summary, maximum_message, messages


def _pair(*, sender_mtu: int = 128, receiver_mtu: int | None = None):
    left = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    right = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    left.bind(("127.0.0.1", 0)); right.bind(("127.0.0.1", 0))
    left_address, right_address = left.getsockname(), right.getsockname()
    return (
        UDPAdapter(left_address, right_address, max_frame_bytes=sender_mtu, timeout=0.05, active_socket=left),
        UDPAdapter(right_address, left_address, max_frame_bytes=receiver_mtu or sender_mtu, timeout=0.05, active_socket=right),
    )


@pytest.mark.parametrize("mtu", (53, 64, 128, 256, 512, 1024, 1500, 4096))
def test_registered_b4_ceiling_roundtrips_one_frame_per_udp_datagram(mtu: int) -> None:
    sender, receiver = _pair(sender_mtu=mtu)
    encoded = compact_summary()
    reassembler = EphemeralFragmentReassembler(max_frame_bytes=mtu)
    complete = None
    try:
        frames = tuple(frame.encode() for frame in fragment_message(encoded, max_frame_bytes=mtu))
        for frame in frames:
            assert sender.send_frame(frame) == len(frame)
            result = reassembler.add(receiver.receive_frame())
            complete = result.complete_message or complete
        assert complete == encoded
        assert sender.accounting.sent == receiver.accounting.received == len(frames)
        assert sender.accounting.sent_bytes == receiver.accounting.received_bytes == sum(map(len, frames))
    finally:
        sender.close(); receiver.close()


def test_empty_short_exact_ceiling_and_outgoing_oversize() -> None:
    sender, receiver = _pair(sender_mtu=128)
    raw = sender._socket
    assert raw is not None
    try:
        raw.send(b"")
        with pytest.raises(UDPBoundsError, match="empty"):
            receiver.receive_frame()
        for size in (1, 10, 51):
            raw.send(bytes(size))
            assert receiver.receive_frame() == bytes(size)
        exact = fragment_message(compact_summary(), max_frame_bytes=128)[0].encode()
        assert len(exact) == 128
        sender.send_frame(exact)
        assert receiver.receive_frame() == exact
        with pytest.raises(UDPBoundsError):
            sender.send_frame(bytes(129))
    finally:
        sender.close(); receiver.close()


def test_oversized_incoming_datagram_detected_without_silent_truncation() -> None:
    sender, receiver = _pair(sender_mtu=256, receiver_mtu=128)
    raw = sender._socket
    assert raw is not None
    try:
        raw.send(bytes(200))
        with pytest.raises(UDPBoundsError, match="incoming"):
            receiver.receive_frame()
        assert receiver.accounting.rejected == 1
    finally:
        sender.close(); receiver.close()


def test_connected_udp_filters_unexpected_source_without_authentication() -> None:
    sender, receiver = _pair()
    foreign = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    foreign.bind(("127.0.0.1", 0))
    try:
        foreign.sendto(fragment_message(messages()[0], max_frame_bytes=128)[0].encode(), receiver.local_address)
        with pytest.raises(UDPTimeout):
            receiver.receive_frame()
    finally:
        foreign.close(); sender.close(); receiver.close()


def test_missing_destination_send_success_is_not_delivery() -> None:
    unused = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    unused.bind(("127.0.0.1", 0)); target = unused.getsockname(); unused.close()
    adapter = UDPAdapter(("127.0.0.1", 0), target, max_frame_bytes=128, timeout=0.03)
    frame = fragment_message(messages()[0], max_frame_bytes=128)[0].encode()
    try:
        assert adapter.send_frame(frame) == len(frame)
        with pytest.raises((UDPError, UDPTimeout)):
            adapter.receive_frame()
    finally:
        adapter.close()


def test_exclusive_bind_collision_and_numeric_loopback_scope() -> None:
    occupied = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    occupied.bind(("127.0.0.1", 0))
    try:
        with pytest.raises(UDPAddressError):
            UDPAdapter(occupied.getsockname(), ("127.0.0.1", 9), max_frame_bytes=128)
        with pytest.raises(UDPAddressError):
            UDPAdapter(("localhost", 0), ("127.0.0.1", 9), max_frame_bytes=128)
        with pytest.raises(UDPAddressError):
            UDPAdapter(("127.0.0.1", 0), ("::1", 9), max_frame_bytes=128)
    finally:
        occupied.close()


def test_udp_port_is_reusable_after_adapter_close() -> None:
    peer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    peer.bind(("127.0.0.1", 0))
    adapter = UDPAdapter(("127.0.0.1", 0), peer.getsockname(), max_frame_bytes=128)
    address = adapter.local_address
    adapter.close()
    rebound = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        rebound.bind(address)
    finally:
        rebound.close(); peer.close()


def test_receive_timeout_is_finite_and_semantically_empty() -> None:
    sender, receiver = _pair()
    started = time.monotonic()
    try:
        with pytest.raises(UDPTimeout):
            receiver.receive_frame()
        assert time.monotonic() - started < 0.5
    finally:
        sender.close(); receiver.close()


def test_mtu_mismatch_rejects_larger_frame_without_negotiation() -> None:
    sender, receiver = _pair(sender_mtu=512, receiver_mtu=256)
    frame = fragment_message(compact_summary(), max_frame_bytes=512)[0].encode()
    assert len(frame) == 512
    try:
        sender.send_frame(frame)
        with pytest.raises(UDPBoundsError):
            receiver.receive_frame()
    finally:
        sender.close(); receiver.close()


def test_corrupted_udp_payload_reaches_b4_and_fails_closed() -> None:
    sender, receiver = _pair()
    raw = sender._socket
    assert raw is not None
    frame = bytearray(fragment_message(messages()[0], max_frame_bytes=128)[0].encode())
    frame[-1] ^= 1
    try:
        raw.send(bytes(frame))
        with pytest.raises(Exception, match="CRC"):
            EphemeralFragmentReassembler(max_frame_bytes=128).add(receiver.receive_frame())
    finally:
        sender.close(); receiver.close()


def test_maximum_b2_message_crosses_udp_as_385_datagrams() -> None:
    sender, receiver = _pair()
    encoded = maximum_message()
    frames = tuple(frame.encode() for frame in fragment_message(encoded, max_frame_bytes=128))
    reassembler = EphemeralFragmentReassembler(max_frame_bytes=128)
    complete = None
    try:
        for frame in frames:
            sender.send_frame(frame)
            result = reassembler.add(receiver.receive_frame())
            complete = result.complete_message or complete
        assert len(frames) == 385 and complete == encoded
    finally:
        sender.close(); receiver.close()


def test_bounded_pressure_has_no_user_space_queue_or_delivery_inference() -> None:
    sender, receiver = _pair()
    assert sender._socket is not None and receiver._socket is not None
    receiver._socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)
    frame = fragment_message(compact_summary(), max_frame_bytes=128)[0].encode()
    accepted = 0
    try:
        for _ in range(2000):
            try:
                sender.send_frame(frame)
            except UDPError:
                break
            accepted += 1
        assert accepted <= 2000
        assert sender.accounting.sent == accepted
    finally:
        sender.close(); receiver.close()
