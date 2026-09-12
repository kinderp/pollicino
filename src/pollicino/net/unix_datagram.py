from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import socket
import stat
import uuid

from .fragmentation import MAX_FRAGMENT_FRAME_BYTES, MIN_FRAGMENT_FRAME_BYTES


EXPERIMENTAL_UNIX_DATAGRAM_ADAPTER = "pollicino.experimental-unix-datagram.v1"
MAX_TRANSPORT_DATAGRAM_BYTES = MAX_FRAGMENT_FRAME_BYTES


class UnixDatagramError(RuntimeError):
    pass


class UnixDatagramBoundsError(UnixDatagramError):
    pass


class UnixDatagramTimeout(UnixDatagramError):
    pass


class UnixDatagramSourceError(UnixDatagramError):
    pass


class UnixDatagramAddressError(UnixDatagramError):
    pass


@dataclass(frozen=True, slots=True)
class DatagramAccounting:
    sent: int
    sent_bytes: int
    received: int
    received_bytes: int
    rejected: int
    send_failures: int
    receive_timeouts: int


class UnixDatagramAdapter:
    """Bounded one-B4-frame-per-datagram local transport adapter."""

    def __init__(
        self,
        local_path: Path,
        peer_path: Path,
        *,
        max_datagram_bytes: int,
        timeout: float = 0.25,
        owned_directory: Path | None = None,
        recover_stale: bool = False,
    ) -> None:
        if not hasattr(socket, "AF_UNIX"):
            raise UnixDatagramAddressError("AF_UNIX is unavailable")
        if type(max_datagram_bytes) is not int or not (
            MIN_FRAGMENT_FRAME_BYTES <= max_datagram_bytes <= MAX_TRANSPORT_DATAGRAM_BYTES
        ):
            raise UnixDatagramBoundsError("datagram ceiling is outside B4 bounds")
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be positive")
        self.local_path = Path(local_path)
        self.peer_path = Path(peer_path)
        self.owned_directory = Path(owned_directory or self.local_path.parent).resolve()
        if self.local_path.parent.resolve() != self.owned_directory:
            raise UnixDatagramAddressError("local path is outside the owned directory")
        self.owned_directory.mkdir(parents=True, exist_ok=True)
        self.max_datagram_bytes = max_datagram_bytes
        self.timeout = float(timeout)
        self._owner_path = self.local_path.with_name(self.local_path.name + ".owner")
        self._token = uuid.uuid4().hex
        self._socket: socket.socket | None = None
        self._sent = self._sent_bytes = self._received = self._received_bytes = 0
        self._rejected = self._send_failures = self._receive_timeouts = 0
        self._prepare_path(recover_stale)
        active = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        active.settimeout(self.timeout)
        try:
            active.bind(os.fspath(self.local_path))
            os.chmod(self.local_path, 0o600)
            self._owner_path.write_text(
                json.dumps({"pid": os.getpid(), "token": self._token, "path": str(self.local_path)})
            )
        except Exception:
            active.close()
            raise
        self._socket = active

    def _prepare_path(self, recover_stale: bool) -> None:
        if not self.local_path.exists():
            return
        if not recover_stale:
            raise UnixDatagramAddressError("local socket path already exists")
        mode = self.local_path.lstat().st_mode
        if not stat.S_ISSOCK(mode) or not self._owner_path.is_file():
            raise UnixDatagramAddressError("refusing to remove an unowned path")
        try:
            owner = json.loads(self._owner_path.read_text())
            pid = int(owner["pid"])
            recorded = Path(owner["path"])
        except Exception as error:
            raise UnixDatagramAddressError("invalid socket ownership marker") from error
        if recorded != self.local_path:
            raise UnixDatagramAddressError("socket ownership marker does not match path")
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pass
        except PermissionError as error:
            raise UnixDatagramAddressError("cannot prove socket owner is dead") from error
        else:
            raise UnixDatagramAddressError("socket owner is still active")
        self.local_path.unlink()
        self._owner_path.unlink()

    @property
    def socket_buffers(self) -> tuple[int, int]:
        assert self._socket is not None
        return (
            self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF),
            self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF),
        )

    @property
    def accounting(self) -> DatagramAccounting:
        return DatagramAccounting(
            self._sent, self._sent_bytes, self._received, self._received_bytes,
            self._rejected, self._send_failures, self._receive_timeouts,
        )

    def send_frame(self, frame: bytes) -> int:
        if not isinstance(frame, bytes) or not frame:
            raise UnixDatagramBoundsError("frame must be non-empty bytes")
        if len(frame) > self.max_datagram_bytes:
            raise UnixDatagramBoundsError("outgoing frame exceeds configured datagram ceiling")
        assert self._socket is not None
        try:
            sent = self._socket.sendto(frame, os.fspath(self.peer_path))
        except (OSError, socket.timeout) as error:
            self._send_failures += 1
            raise UnixDatagramError(f"datagram send failed: {error}") from error
        if sent != len(frame):
            self._send_failures += 1
            raise UnixDatagramError("partial datagram send")
        self._sent += 1
        self._sent_bytes += sent
        return sent

    def receive_frame(self) -> bytes:
        assert self._socket is not None
        try:
            payload, source = self._socket.recvfrom(self.max_datagram_bytes + 1)
        except socket.timeout as error:
            self._receive_timeouts += 1
            raise UnixDatagramTimeout("receive opportunity timed out") from error
        except OSError as error:
            raise UnixDatagramError(f"datagram receive failed: {error}") from error
        if Path(source) != self.peer_path:
            self._rejected += 1
            raise UnixDatagramSourceError("datagram arrived from unexpected source")
        if not payload:
            self._rejected += 1
            raise UnixDatagramBoundsError("empty datagram is not a B4 frame")
        if len(payload) > self.max_datagram_bytes:
            self._rejected += 1
            raise UnixDatagramBoundsError("incoming datagram exceeds configured ceiling")
        self._received += 1
        self._received_bytes += len(payload)
        return payload

    def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None
        try:
            owner = json.loads(self._owner_path.read_text())
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return
        if owner.get("token") == self._token:
            try:
                self.local_path.unlink()
            except FileNotFoundError:
                pass
            try:
                self._owner_path.unlink()
            except FileNotFoundError:
                pass

    def __enter__(self) -> "UnixDatagramAdapter":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


__all__ = [
    "DatagramAccounting",
    "EXPERIMENTAL_UNIX_DATAGRAM_ADAPTER",
    "MAX_TRANSPORT_DATAGRAM_BYTES",
    "UnixDatagramAdapter",
    "UnixDatagramAddressError",
    "UnixDatagramBoundsError",
    "UnixDatagramError",
    "UnixDatagramSourceError",
    "UnixDatagramTimeout",
]
