from __future__ import annotations

from dataclasses import dataclass
import struct
from typing import BinaryIO

from .compact_reconciliation import (
    B2C_MAGIC,
    MAX_COMPACT_MESSAGE_BYTES,
    decode_compact_message,
)
from .endpoint import B2_MAGIC, MAX_B2_MESSAGE_BYTES, decode_message
from .fair_reconciliation import (
    B2F_MAGIC,
    MAX_B2F_MESSAGE_BYTES,
    decode_fair_message,
)


EXPERIMENTAL_PROCESS_IO = "pollicino.experimental-b3-process-io.v1"
PROCESS_IO_EXTRA_WIRE_BYTES = 0
PROCESS_STREAM_HEADER_BYTES = 42
MAX_PROCESS_IO_MESSAGE_BYTES = MAX_B2_MESSAGE_BYTES
MAX_PROCESS_IO_MESSAGES = 200
MAX_PROCESS_IO_READ_BYTES = MAX_PROCESS_IO_MESSAGE_BYTES

_ENVELOPE_HEADER = struct.Struct(">4sBBI32s")
if _ENVELOPE_HEADER.size != PROCESS_STREAM_HEADER_BYTES:
    raise RuntimeError("unexpected inherited B2 envelope header size")

_MESSAGE_LIMITS = {
    B2_MAGIC: MAX_B2_MESSAGE_BYTES,
    B2F_MAGIC: MAX_B2F_MESSAGE_BYTES,
    B2C_MAGIC: MAX_COMPACT_MESSAGE_BYTES,
}


class ProcessIOError(RuntimeError):
    pass


class ProcessIOBoundsError(ProcessIOError):
    pass


class IncompleteProcessMessageError(ProcessIOError):
    pass


@dataclass(frozen=True, slots=True)
class StreamAccounting:
    read_calls: int
    stream_chunks: int
    encoded_bytes: int
    complete_messages: int
    maximum_buffer_bytes: int


class BoundedMessageStreamReader:
    """Incrementally recover existing B2-family envelopes from an ordered stream.

    This is stream reassembly, not Pollicino fragmentation. The reader adds no
    bytes and never buffers a declared body before checking its native limit.
    """

    def __init__(self, *, max_messages: int = MAX_PROCESS_IO_MESSAGES) -> None:
        if type(max_messages) is not int or not 1 <= max_messages <= MAX_PROCESS_IO_MESSAGES:
            raise ProcessIOBoundsError("stream message bound is outside limits")
        self._max_messages = max_messages
        self._buffer = bytearray()
        self._expected_total: int | None = None
        self._closed = False
        self._messages = 0
        self._encoded_bytes = 0
        self._chunks = 0
        self._maximum_buffer = 0

    @property
    def buffered_bytes(self) -> int:
        return len(self._buffer)

    @property
    def maximum_buffer_bytes(self) -> int:
        return self._maximum_buffer

    @property
    def complete_messages(self) -> int:
        return self._messages

    @property
    def encoded_bytes(self) -> int:
        return self._encoded_bytes

    @property
    def stream_chunks(self) -> int:
        return self._chunks

    def _observe_buffer(self) -> None:
        self._maximum_buffer = max(self._maximum_buffer, len(self._buffer))
        if self._maximum_buffer > MAX_PROCESS_IO_MESSAGE_BYTES:
            raise ProcessIOBoundsError("receive buffer exceeded inherited message bound")

    def _parse_header(self) -> None:
        magic, _version, _message_type, body_length, _digest = _ENVELOPE_HEADER.unpack(
            self._buffer
        )
        maximum = _MESSAGE_LIMITS.get(magic)
        if maximum is None:
            raise ProcessIOError("unknown experimental B2 envelope magic")
        maximum_body = maximum - _ENVELOPE_HEADER.size
        if body_length > maximum_body:
            raise ProcessIOBoundsError("declared body length exceeds native envelope bound")
        self._expected_total = _ENVELOPE_HEADER.size + body_length

    def feed(self, data: bytes) -> tuple[bytes, ...]:
        if self._closed:
            raise ProcessIOError("stream reader is closed")
        if not isinstance(data, bytes):
            raise TypeError("stream data must be bytes")
        if not data:
            return ()
        self._chunks += 1
        frames: list[bytes] = []
        view = memoryview(data)
        offset = 0
        while offset < len(view):
            target = (
                _ENVELOPE_HEADER.size
                if self._expected_total is None
                else self._expected_total
            )
            needed = target - len(self._buffer)
            take = min(needed, len(view) - offset)
            self._buffer.extend(view[offset : offset + take])
            offset += take
            self._observe_buffer()
            if self._expected_total is None and len(self._buffer) == _ENVELOPE_HEADER.size:
                self._parse_header()
                assert self._expected_total is not None
                if len(self._buffer) < self._expected_total:
                    continue
            if self._expected_total is not None and len(self._buffer) == self._expected_total:
                if self._messages >= self._max_messages:
                    raise ProcessIOBoundsError("stream message count exceeds contact bound")
                frame = bytes(self._buffer)
                frames.append(frame)
                self._messages += 1
                self._encoded_bytes += len(frame)
                self._buffer.clear()
                self._expected_total = None
        return tuple(frames)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._buffer:
            where = "header" if self._expected_total is None else "body"
            raise IncompleteProcessMessageError(f"EOF in partial B2 {where}")


def validate_complete_message(encoded: bytes) -> object:
    """Apply the existing structural decoder after stream delimiting."""

    if encoded[:4] == B2_MAGIC:
        return decode_message(encoded)
    if encoded[:4] == B2F_MAGIC:
        return decode_fair_message(encoded)
    if encoded[:4] == B2C_MAGIC:
        return decode_compact_message(encoded)
    raise ProcessIOError("unknown experimental B2 envelope magic")


def read_bounded_messages(
    source: BinaryIO,
    *,
    read_size: int = 4096,
    max_messages: int = MAX_PROCESS_IO_MESSAGES,
) -> tuple[tuple[bytes, ...], StreamAccounting]:
    if type(read_size) is not int or not 1 <= read_size <= MAX_PROCESS_IO_READ_BYTES:
        raise ProcessIOBoundsError("read size is outside bounds")
    reader = BoundedMessageStreamReader(max_messages=max_messages)
    frames: list[bytes] = []
    read_calls = 0
    while True:
        chunk = source.read(read_size)
        read_calls += 1
        if not chunk:
            break
        frames.extend(reader.feed(chunk))
    reader.close()
    for frame in frames:
        validate_complete_message(frame)
    return tuple(frames), StreamAccounting(
        read_calls,
        reader.stream_chunks,
        reader.encoded_bytes,
        reader.complete_messages,
        reader.maximum_buffer_bytes,
    )


__all__ = [
    "BoundedMessageStreamReader",
    "EXPERIMENTAL_PROCESS_IO",
    "IncompleteProcessMessageError",
    "MAX_PROCESS_IO_MESSAGE_BYTES",
    "MAX_PROCESS_IO_MESSAGES",
    "MAX_PROCESS_IO_READ_BYTES",
    "PROCESS_IO_EXTRA_WIRE_BYTES",
    "PROCESS_STREAM_HEADER_BYTES",
    "ProcessIOBoundsError",
    "ProcessIOError",
    "StreamAccounting",
    "read_bounded_messages",
    "validate_complete_message",
]
