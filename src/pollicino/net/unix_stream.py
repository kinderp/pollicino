from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
import os
from pathlib import Path
import socket
import stat
import time
import uuid

from .fragmentation import (
    BoundedFragmentStreamReader,
    FragmentationError,
    FragmentFrame,
    MAX_FRAGMENT_FRAME_BYTES,
    MAX_FRAGMENTS_PER_CONTACT,
    MIN_FRAGMENT_FRAME_BYTES,
)


EXPERIMENTAL_UNIX_STREAM_ADAPTER = "pollicino.experimental-unix-stream.v1"
MAX_STREAM_FRAME_BYTES = MAX_FRAGMENT_FRAME_BYTES
MAX_STREAM_READ_BYTES = MAX_FRAGMENT_FRAME_BYTES


class UnixStreamError(RuntimeError):
    pass


class UnixStreamBoundsError(UnixStreamError):
    pass


class UnixStreamTimeout(UnixStreamError):
    pass


class UnixStreamEOF(UnixStreamError):
    """Clean EOF at a B4-frame boundary."""


class UnixStreamFrameError(UnixStreamError):
    pass


class UnixStreamAddressError(UnixStreamError):
    pass


@dataclass(frozen=True, slots=True)
class StreamAccounting:
    frames_sent: int
    frame_bytes_sent: int
    frames_received: int
    frame_bytes_received: int
    stream_bytes_written: int
    stream_bytes_read: int
    write_calls: int
    read_calls: int
    send_failures: int
    receive_failures: int
    timeouts: int
    maximum_buffered_bytes: int


def _validate_frame_ceiling(max_frame_bytes: int) -> None:
    if type(max_frame_bytes) is not int or not (
        MIN_FRAGMENT_FRAME_BYTES <= max_frame_bytes <= MAX_STREAM_FRAME_BYTES
    ):
        raise UnixStreamBoundsError("stream frame ceiling is outside B4 bounds")


class UnixStreamAdapter:
    """One bounded connected byte stream carrying complete B4 frames."""

    def __init__(
        self,
        active: socket.socket,
        *,
        max_frame_bytes: int,
        timeout: float = 0.25,
        max_read_bytes: int | None = None,
        max_write_chunk_bytes: int | None = None,
        max_frames: int = MAX_FRAGMENTS_PER_CONTACT,
    ) -> None:
        _validate_frame_ceiling(max_frame_bytes)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be positive")
        read_bound = max_frame_bytes if max_read_bytes is None else max_read_bytes
        write_bound = max_frame_bytes if max_write_chunk_bytes is None else max_write_chunk_bytes
        if type(read_bound) is not int or not 1 <= read_bound <= MAX_STREAM_READ_BYTES:
            raise UnixStreamBoundsError("stream read size is outside bounds")
        if type(write_bound) is not int or not 1 <= write_bound <= max_frame_bytes:
            raise UnixStreamBoundsError("stream write chunk is outside frame bounds")
        if active.family != socket.AF_UNIX or active.type & socket.SOCK_STREAM != socket.SOCK_STREAM:
            raise UnixStreamAddressError("adapter requires a connected AF_UNIX/SOCK_STREAM socket")
        self.max_frame_bytes = max_frame_bytes
        self.timeout = float(timeout)
        self.max_read_bytes = read_bound
        self.max_write_chunk_bytes = write_bound
        self.max_buffer_bytes = max_frame_bytes + read_bound
        self._socket: socket.socket | None = active
        self._socket.settimeout(self.timeout)
        self._reader = BoundedFragmentStreamReader(
            max_frame_bytes=max_frame_bytes, max_frames=max_frames
        )
        self._ready: deque[bytes] = deque()
        self._ready_bytes = 0
        self._ended = False
        self._terminal_receive_error: str | None = None
        self._send_failed = False
        self._frames_sent = self._frame_bytes_sent = 0
        self._frames_received = self._frame_bytes_received = 0
        self._stream_bytes_written = self._stream_bytes_read = 0
        self._write_calls = self._read_calls = 0
        self._send_failures = self._receive_failures = self._timeouts = 0
        self._maximum_buffered_bytes = 0

    @classmethod
    def connect(
        cls,
        peer_path: Path,
        *,
        max_frame_bytes: int,
        timeout: float = 0.25,
        max_read_bytes: int | None = None,
        max_write_chunk_bytes: int | None = None,
        max_frames: int = MAX_FRAGMENTS_PER_CONTACT,
    ) -> "UnixStreamAdapter":
        _validate_frame_ceiling(max_frame_bytes)
        active = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        active.settimeout(float(timeout))
        try:
            active.connect(os.fspath(peer_path))
        except (OSError, socket.timeout) as error:
            active.close()
            raise UnixStreamAddressError(f"stream connect failed: {error}") from error
        return cls(
            active,
            max_frame_bytes=max_frame_bytes,
            timeout=timeout,
            max_read_bytes=max_read_bytes,
            max_write_chunk_bytes=max_write_chunk_bytes,
            max_frames=max_frames,
        )

    @property
    def socket_buffers(self) -> tuple[int, int]:
        assert self._socket is not None
        return (
            self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF),
            self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF),
        )

    @property
    def accounting(self) -> StreamAccounting:
        return StreamAccounting(
            self._frames_sent,
            self._frame_bytes_sent,
            self._frames_received,
            self._frame_bytes_received,
            self._stream_bytes_written,
            self._stream_bytes_read,
            self._write_calls,
            self._read_calls,
            self._send_failures,
            self._receive_failures,
            self._timeouts,
            self._maximum_buffered_bytes,
        )

    def _remaining(self, deadline: float) -> float:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            self._timeouts += 1
            raise UnixStreamTimeout("stream opportunity timed out")
        return remaining

    def send_frame(self, frame: bytes) -> int:
        if self._send_failed:
            raise UnixStreamError("stream write side already failed")
        if not isinstance(frame, bytes) or not frame:
            raise UnixStreamBoundsError("frame must be non-empty bytes")
        if len(frame) > self.max_frame_bytes:
            raise UnixStreamBoundsError("outgoing frame exceeds configured ceiling")
        try:
            FragmentFrame.decode(frame, max_frame_bytes=self.max_frame_bytes)
        except FragmentationError as error:
            raise UnixStreamFrameError(f"outgoing B4 frame is invalid: {error}") from error
        assert self._socket is not None
        deadline = time.monotonic() + self.timeout
        offset = 0
        try:
            while offset < len(frame):
                self._socket.settimeout(self._remaining(deadline))
                upper = min(offset + self.max_write_chunk_bytes, len(frame))
                self._write_calls += 1
                sent = self._socket.send(memoryview(frame)[offset:upper])
                if sent <= 0:
                    raise UnixStreamError("stream write made no progress")
                offset += sent
                self._stream_bytes_written += sent
        except UnixStreamTimeout:
            self._send_failures += 1
            self._send_failed = True
            raise
        except (OSError, socket.timeout) as error:
            self._send_failures += 1
            self._send_failed = True
            if isinstance(error, socket.timeout):
                self._timeouts += 1
            raise UnixStreamError(f"stream frame write failed after {offset} bytes: {error}") from error
        finally:
            if self._socket is not None:
                self._socket.settimeout(self.timeout)
        self._frames_sent += 1
        self._frame_bytes_sent += len(frame)
        return len(frame)

    def _take_ready(self) -> bytes:
        frame = self._ready.popleft()
        self._ready_bytes -= len(frame)
        self._frames_received += 1
        self._frame_bytes_received += len(frame)
        return frame

    def receive_frame(self) -> bytes:
        if self._terminal_receive_error is not None:
            raise UnixStreamFrameError(self._terminal_receive_error)
        if self._ready:
            return self._take_ready()
        if self._ended:
            raise UnixStreamEOF("stream ended at a frame boundary")
        assert self._socket is not None
        deadline = time.monotonic() + self.timeout
        while not self._ready:
            try:
                self._socket.settimeout(self._remaining(deadline))
                self._read_calls += 1
                chunk = self._socket.recv(self.max_read_bytes)
            except UnixStreamTimeout:
                self._receive_failures += 1
                raise
            except socket.timeout as error:
                self._timeouts += 1
                self._receive_failures += 1
                raise UnixStreamTimeout("stream receive opportunity timed out") from error
            except OSError as error:
                self._receive_failures += 1
                raise UnixStreamError(f"stream receive failed: {error}") from error
            if not chunk:
                self._ended = True
                try:
                    self._reader.close()
                except FragmentationError as error:
                    self._receive_failures += 1
                    self._terminal_receive_error = f"EOF inside B4 frame: {error}"
                    raise UnixStreamFrameError(self._terminal_receive_error) from error
                raise UnixStreamEOF("stream ended at a frame boundary")
            self._stream_bytes_read += len(chunk)
            try:
                frames = self._reader.feed(chunk)
            except FragmentationError as error:
                self._receive_failures += 1
                self._terminal_receive_error = f"invalid B4 frame stream: {error}"
                raise UnixStreamFrameError(self._terminal_receive_error) from error
            self._ready.extend(frames)
            self._ready_bytes += sum(map(len, frames))
            # Frames returned by feed() and its retained partial suffix are all
            # drawn from at most the prior frame plus this bounded recv().
            self._maximum_buffered_bytes = max(
                self._maximum_buffered_bytes,
                self._ready_bytes,
                self._reader.maximum_buffer_bytes,
            )
            if self._ready_bytes > self.max_buffer_bytes:
                self._receive_failures += 1
                raise UnixStreamBoundsError("stream adapter buffer bound exceeded")
        return self._take_ready()

    def shutdown_write(self) -> None:
        assert self._socket is not None
        try:
            self._socket.shutdown(socket.SHUT_WR)
        except OSError as error:
            raise UnixStreamError(f"stream write shutdown failed: {error}") from error

    def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def __enter__(self) -> "UnixStreamAdapter":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


class UnixStreamListener:
    """Owned pathname listener for one bounded stream contact at a time."""

    def __init__(
        self,
        local_path: Path,
        *,
        max_frame_bytes: int,
        timeout: float = 0.25,
        owned_directory: Path | None = None,
        recover_stale: bool = False,
    ) -> None:
        if not hasattr(socket, "AF_UNIX"):
            raise UnixStreamAddressError("AF_UNIX is unavailable")
        _validate_frame_ceiling(max_frame_bytes)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be positive")
        self.local_path = Path(local_path)
        self.owned_directory = Path(owned_directory or self.local_path.parent).resolve()
        if self.local_path.parent.resolve() != self.owned_directory:
            raise UnixStreamAddressError("listener path is outside the owned directory")
        self.owned_directory.mkdir(parents=True, exist_ok=True)
        self.max_frame_bytes = max_frame_bytes
        self.timeout = float(timeout)
        self._owner_path = self.local_path.with_name(self.local_path.name + ".owner")
        self._token = uuid.uuid4().hex
        self._socket: socket.socket | None = None
        self._prepare_path(recover_stale)
        active = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        active.settimeout(self.timeout)
        try:
            active.bind(os.fspath(self.local_path))
            active.listen(1)
            os.chmod(self.local_path, 0o600)
            self._owner_path.write_text(json.dumps({
                "pid": os.getpid(), "token": self._token, "path": str(self.local_path)
            }))
        except Exception:
            active.close()
            try:
                self.local_path.unlink()
            except FileNotFoundError:
                pass
            try:
                self._owner_path.unlink()
            except FileNotFoundError:
                pass
            raise
        self._socket = active

    def _prepare_path(self, recover_stale: bool) -> None:
        if not self.local_path.exists():
            return
        if not recover_stale:
            raise UnixStreamAddressError("listener path already exists")
        mode = self.local_path.lstat().st_mode
        if not stat.S_ISSOCK(mode) or not self._owner_path.is_file():
            raise UnixStreamAddressError("refusing to remove an unowned path")
        try:
            owner = json.loads(self._owner_path.read_text())
            pid = int(owner["pid"])
            recorded = Path(owner["path"])
        except Exception as error:
            raise UnixStreamAddressError("invalid stream ownership marker") from error
        if recorded != self.local_path:
            raise UnixStreamAddressError("stream ownership marker does not match path")
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pass
        except PermissionError as error:
            raise UnixStreamAddressError("cannot prove stream owner is dead") from error
        else:
            raise UnixStreamAddressError("stream owner is still active")
        self.local_path.unlink()
        self._owner_path.unlink()

    def accept(
        self,
        *,
        max_read_bytes: int | None = None,
        max_write_chunk_bytes: int | None = None,
        max_frames: int = MAX_FRAGMENTS_PER_CONTACT,
    ) -> UnixStreamAdapter:
        assert self._socket is not None
        try:
            active, _address = self._socket.accept()
        except socket.timeout as error:
            raise UnixStreamTimeout("stream accept opportunity timed out") from error
        except OSError as error:
            raise UnixStreamAddressError(f"stream accept failed: {error}") from error
        return UnixStreamAdapter(
            active,
            max_frame_bytes=self.max_frame_bytes,
            timeout=self.timeout,
            max_read_bytes=max_read_bytes,
            max_write_chunk_bytes=max_write_chunk_bytes,
            max_frames=max_frames,
        )

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

    def __enter__(self) -> "UnixStreamListener":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


__all__ = [
    "EXPERIMENTAL_UNIX_STREAM_ADAPTER",
    "MAX_STREAM_FRAME_BYTES",
    "MAX_STREAM_READ_BYTES",
    "StreamAccounting",
    "UnixStreamAdapter",
    "UnixStreamAddressError",
    "UnixStreamBoundsError",
    "UnixStreamEOF",
    "UnixStreamError",
    "UnixStreamFrameError",
    "UnixStreamListener",
    "UnixStreamTimeout",
]
