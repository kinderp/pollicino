from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import socket

from .fragmentation import MAX_FRAGMENT_FRAME_BYTES, MIN_FRAGMENT_FRAME_BYTES


EXPERIMENTAL_UDP_ADAPTER = "pollicino.experimental-udp-ipv4-loopback.v1"
UDP_LOOPBACK_ADDRESS = "127.0.0.1"
MAX_UDP_FRAME_BYTES = MAX_FRAGMENT_FRAME_BYTES
UDPAddress = tuple[str, int]


class UDPError(RuntimeError):
    pass


class UDPBoundsError(UDPError):
    pass


class UDPTimeout(UDPError):
    pass


class UDPAddressError(UDPError):
    pass


@dataclass(frozen=True, slots=True)
class UDPAccounting:
    sent: int
    sent_bytes: int
    received: int
    received_bytes: int
    rejected: int
    send_failures: int
    receive_failures: int
    receive_timeouts: int


def _address(value: UDPAddress, *, allow_zero_port: bool) -> UDPAddress:
    if not isinstance(value, tuple) or len(value) != 2:
        raise UDPAddressError("UDP address must be an (IPv4, port) tuple")
    host, port = value
    if not isinstance(host, str):
        raise UDPAddressError("UDP host must be a numeric IPv4 string")
    try:
        parsed = ipaddress.IPv4Address(host)
    except ipaddress.AddressValueError as error:
        raise UDPAddressError("UDP host must be numeric IPv4") from error
    if parsed.is_unspecified or parsed.is_multicast or parsed.is_reserved:
        raise UDPAddressError("UDP host must be a numeric unicast IPv4 address")
    minimum = 0 if allow_zero_port else 1
    if type(port) is not int or not minimum <= port <= 65535:
        raise UDPAddressError("UDP port is outside bounds")
    return str(parsed), port


class UDPAdapter:
    """Connected IPv4 adapter: one complete B4 frame per datagram."""

    def __init__(
        self,
        local_address: UDPAddress,
        peer_address: UDPAddress,
        *,
        max_frame_bytes: int,
        timeout: float = 0.25,
        active_socket: socket.socket | None = None,
    ) -> None:
        if type(max_frame_bytes) is not int or not (
            MIN_FRAGMENT_FRAME_BYTES <= max_frame_bytes <= MAX_UDP_FRAME_BYTES
        ):
            raise UDPBoundsError("UDP frame ceiling is outside B4 bounds")
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be positive")
        local = _address(local_address, allow_zero_port=True)
        peer = _address(peer_address, allow_zero_port=False)
        if active_socket is None:
            active = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                active.bind(local)
            except OSError as error:
                active.close()
                raise UDPAddressError(f"UDP bind failed: {error}") from error
        else:
            active = active_socket
            if active.family != socket.AF_INET or active.type & socket.SOCK_DGRAM != socket.SOCK_DGRAM:
                raise UDPAddressError("active socket must be AF_INET/SOCK_DGRAM")
            bound = active.getsockname()
            if bound[0] != local[0] or (local[1] and bound[1] != local[1]):
                raise UDPAddressError("active socket does not match configured local address")
        active.settimeout(float(timeout))
        try:
            active.connect(peer)
        except OSError as error:
            if active_socket is None:
                active.close()
            raise UDPAddressError(f"UDP peer configuration failed: {error}") from error
        self._socket: socket.socket | None = active
        self.local_address: UDPAddress = (active.getsockname()[0], active.getsockname()[1])
        self.peer_address = peer
        self.max_frame_bytes = max_frame_bytes
        self.timeout = float(timeout)
        self._sent = self._sent_bytes = self._received = self._received_bytes = 0
        self._rejected = self._send_failures = self._receive_failures = 0
        self._receive_timeouts = 0

    @property
    def socket_buffers(self) -> tuple[int, int]:
        assert self._socket is not None
        return (
            self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF),
            self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF),
        )

    @property
    def accounting(self) -> UDPAccounting:
        return UDPAccounting(
            self._sent,
            self._sent_bytes,
            self._received,
            self._received_bytes,
            self._rejected,
            self._send_failures,
            self._receive_failures,
            self._receive_timeouts,
        )

    def send_frame(self, frame: bytes) -> int:
        if not isinstance(frame, bytes) or not frame:
            raise UDPBoundsError("frame must be non-empty bytes")
        if len(frame) > self.max_frame_bytes:
            raise UDPBoundsError("outgoing frame exceeds configured UDP ceiling")
        assert self._socket is not None
        try:
            sent = self._socket.send(frame)
        except (OSError, socket.timeout) as error:
            self._send_failures += 1
            raise UDPError(f"UDP send failed: {error}") from error
        if sent != len(frame):
            self._send_failures += 1
            raise UDPError("partial UDP datagram send")
        self._sent += 1
        self._sent_bytes += sent
        return sent

    def receive_frame(self) -> bytes:
        assert self._socket is not None
        try:
            payload = self._socket.recv(self.max_frame_bytes + 1)
        except socket.timeout as error:
            self._receive_timeouts += 1
            raise UDPTimeout("UDP receive opportunity timed out") from error
        except OSError as error:
            self._receive_failures += 1
            raise UDPError(f"UDP receive failed: {error}") from error
        if not payload:
            self._rejected += 1
            raise UDPBoundsError("empty UDP datagram is not a B4 frame")
        if len(payload) > self.max_frame_bytes:
            self._rejected += 1
            raise UDPBoundsError("incoming UDP datagram exceeds configured ceiling")
        self._received += 1
        self._received_bytes += len(payload)
        return payload

    def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def __enter__(self) -> "UDPAdapter":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


__all__ = [
    "EXPERIMENTAL_UDP_ADAPTER",
    "MAX_UDP_FRAME_BYTES",
    "UDPAccounting",
    "UDPAdapter",
    "UDPAddress",
    "UDPAddressError",
    "UDPBoundsError",
    "UDPError",
    "UDPTimeout",
    "UDP_LOOPBACK_ADDRESS",
]
