from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import struct
from typing import BinaryIO, Sequence
import zlib

from .endpoint import MAX_B2_MESSAGE_BYTES
from .process_io import validate_complete_message


EXPERIMENTAL_B4_FRAGMENT_ENCODING = "pollicino.experimental-b4-fragment.v1"
B4_FRAGMENT_MAGIC = b"PB4F"
B4_FRAGMENT_VERSION = 1
B4_FRAGMENT_TYPE_DATA = 1
B4_MESSAGE_ID_BYTES = 32

_FRAGMENT_HEADER = struct.Struct(">4sBB32sIHHHI")
FRAGMENT_HEADER_BYTES = _FRAGMENT_HEADER.size
MIN_FRAGMENT_FRAME_BYTES = FRAGMENT_HEADER_BYTES + 1
MAX_FRAGMENT_FRAME_BYTES = 4096
MAX_FRAGMENTED_MESSAGE_BYTES = MAX_B2_MESSAGE_BYTES
MAX_FRAGMENTS_PER_MESSAGE = math.ceil(
    MAX_FRAGMENTED_MESSAGE_BYTES / (64 - FRAGMENT_HEADER_BYTES)
)
MAX_SIMULTANEOUS_INCOMPLETE_MESSAGES = 1
MAX_REASSEMBLY_BYTES = MAX_FRAGMENTED_MESSAGE_BYTES
MAX_FRAGMENT_METADATA_ENTRIES = MAX_FRAGMENTS_PER_MESSAGE
MAX_FRAGMENTS_PER_CONTACT = 10_000
MAX_FRAGMENT_BYTES_PER_CONTACT = MAX_FRAGMENTS_PER_CONTACT * MAX_FRAGMENT_FRAME_BYTES


class FragmentationError(ValueError):
    pass


class FragmentBoundsError(FragmentationError):
    pass


class FragmentDecodeError(FragmentationError):
    pass


class IncompleteFragmentStreamError(FragmentationError):
    pass


class IncompleteReassemblyError(FragmentationError):
    pass


class CrossMessageFragmentError(FragmentationError):
    pass


class ConflictingFragmentError(FragmentationError):
    pass


def _validate_mtu(max_frame_bytes: int) -> None:
    if type(max_frame_bytes) is not int:
        raise TypeError("max_frame_bytes must be int")
    if not MIN_FRAGMENT_FRAME_BYTES <= max_frame_bytes <= MAX_FRAGMENT_FRAME_BYTES:
        raise FragmentBoundsError(
            f"max_frame_bytes must be between {MIN_FRAGMENT_FRAME_BYTES} "
            f"and {MAX_FRAGMENT_FRAME_BYTES}"
        )


@dataclass(frozen=True, slots=True)
class FragmentFrame:
    message_id: bytes
    total_length: int
    index: int
    count: int
    payload: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.message_id, bytes) or len(self.message_id) != B4_MESSAGE_ID_BYTES:
            raise FragmentBoundsError("message_id must be a SHA-256 digest")
        if type(self.total_length) is not int or not 1 <= self.total_length <= MAX_FRAGMENTED_MESSAGE_BYTES:
            raise FragmentBoundsError("declared total length is outside B2 bounds")
        if type(self.count) is not int or not 1 <= self.count <= MAX_FRAGMENTS_PER_MESSAGE:
            raise FragmentBoundsError("fragment count is outside bounds")
        if type(self.index) is not int or not 0 <= self.index < self.count:
            raise FragmentBoundsError("fragment index is outside count")
        if not isinstance(self.payload, bytes) or not self.payload:
            raise FragmentBoundsError("fragment payload must be non-empty bytes")
        if len(self.payload) > 0xFFFF:
            raise FragmentBoundsError("fragment payload exceeds length field")

    def encode(self) -> bytes:
        checksum = zlib.crc32(self.payload) & 0xFFFFFFFF
        return _FRAGMENT_HEADER.pack(
            B4_FRAGMENT_MAGIC,
            B4_FRAGMENT_VERSION,
            B4_FRAGMENT_TYPE_DATA,
            self.message_id,
            self.total_length,
            self.index,
            self.count,
            len(self.payload),
            checksum,
        ) + self.payload

    @classmethod
    def decode(cls, data: bytes, *, max_frame_bytes: int) -> FragmentFrame:
        _validate_mtu(max_frame_bytes)
        if not isinstance(data, bytes):
            raise TypeError("fragment data must be bytes")
        if len(data) > max_frame_bytes:
            raise FragmentBoundsError("encoded fragment exceeds configured MTU")
        if len(data) < FRAGMENT_HEADER_BYTES:
            raise FragmentDecodeError("fragment header is truncated")
        (
            magic,
            version,
            frame_type,
            message_id,
            total_length,
            index,
            count,
            payload_length,
            expected_crc,
        ) = _FRAGMENT_HEADER.unpack_from(data)
        if magic != B4_FRAGMENT_MAGIC:
            raise FragmentDecodeError("invalid fragment magic")
        if version != B4_FRAGMENT_VERSION:
            raise FragmentDecodeError("unsupported fragment version")
        if frame_type != B4_FRAGMENT_TYPE_DATA:
            raise FragmentDecodeError("unknown fragment type")
        if payload_length > max_frame_bytes - FRAGMENT_HEADER_BYTES:
            raise FragmentBoundsError("declared fragment payload exceeds MTU")
        if len(data) != FRAGMENT_HEADER_BYTES + payload_length:
            raise FragmentDecodeError("fragment length mismatch")
        payload = data[FRAGMENT_HEADER_BYTES:]
        if zlib.crc32(payload) & 0xFFFFFFFF != expected_crc:
            raise FragmentDecodeError("fragment CRC mismatch")
        try:
            return cls(message_id, total_length, index, count, payload)
        except FragmentBoundsError:
            raise
        except (TypeError, ValueError) as error:
            raise FragmentDecodeError("invalid fragment metadata") from error


def fragment_message(encoded: bytes, *, max_frame_bytes: int) -> tuple[FragmentFrame, ...]:
    _validate_mtu(max_frame_bytes)
    if not isinstance(encoded, bytes):
        raise TypeError("encoded message must be bytes")
    if not 1 <= len(encoded) <= MAX_FRAGMENTED_MESSAGE_BYTES:
        raise FragmentBoundsError("encoded message is outside inherited B2 bounds")
    validate_complete_message(encoded)
    payload_capacity = max_frame_bytes - FRAGMENT_HEADER_BYTES
    count = math.ceil(len(encoded) / payload_capacity)
    if count > MAX_FRAGMENTS_PER_MESSAGE:
        raise FragmentBoundsError("message requires too many fragments")
    message_id = hashlib.sha256(encoded).digest()
    return tuple(
        FragmentFrame(
            message_id,
            len(encoded),
            index,
            count,
            encoded[index * payload_capacity : (index + 1) * payload_capacity],
        )
        for index in range(count)
    )


@dataclass(frozen=True, slots=True)
class ReassemblyResult:
    complete_message: bytes | None
    duplicate: bool
    buffered_fragments: int
    buffered_bytes: int


class EphemeralFragmentReassembler:
    """One bounded, unordered, duplicate-safe in-flight B2 message."""

    def __init__(self, *, max_frame_bytes: int) -> None:
        _validate_mtu(max_frame_bytes)
        self.max_frame_bytes = max_frame_bytes
        self._message_id: bytes | None = None
        self._total_length: int | None = None
        self._count: int | None = None
        self._payloads: dict[int, bytes] = {}
        self._buffered_bytes = 0
        self._completed: tuple[bytes, int, int] | None = None

    @property
    def incomplete(self) -> bool:
        return self._message_id is not None

    @property
    def buffered_bytes(self) -> int:
        return self._buffered_bytes

    @property
    def buffered_fragments(self) -> int:
        return len(self._payloads)

    def discard(self) -> None:
        self._clear_incomplete()
        self._completed = None

    def _clear_incomplete(self) -> None:
        self._message_id = None
        self._total_length = None
        self._count = None
        self._payloads.clear()
        self._buffered_bytes = 0

    def _validate_canonical_shape(self, frame: FragmentFrame) -> None:
        capacity = self.max_frame_bytes - FRAGMENT_HEADER_BYTES
        expected_count = math.ceil(frame.total_length / capacity)
        if frame.count != expected_count:
            raise FragmentBoundsError("fragment count is inconsistent with total length and MTU")
        expected_length = (
            capacity
            if frame.index < frame.count - 1
            else frame.total_length - capacity * (frame.count - 1)
        )
        if len(frame.payload) != expected_length:
            raise FragmentBoundsError("fragment payload length is inconsistent with canonical shape")

    def add(self, encoded_frame: bytes) -> ReassemblyResult:
        frame = FragmentFrame.decode(encoded_frame, max_frame_bytes=self.max_frame_bytes)
        self._validate_canonical_shape(frame)
        identity = (frame.message_id, frame.total_length, frame.count)
        if identity == self._completed:
            return ReassemblyResult(None, True, 0, 0)
        if self._completed is not None and self._message_id is None:
            self._completed = None
        if self._message_id is None:
            self._message_id = frame.message_id
            self._total_length = frame.total_length
            self._count = frame.count
        elif (
            frame.message_id != self._message_id
            or frame.total_length != self._total_length
            or frame.count != self._count
        ):
            raise CrossMessageFragmentError("fragment belongs to a different in-flight message")
        previous = self._payloads.get(frame.index)
        if previous is not None:
            if previous != frame.payload:
                raise ConflictingFragmentError("conflicting duplicate fragment")
            return ReassemblyResult(None, True, len(self._payloads), self._buffered_bytes)
        if self._buffered_bytes + len(frame.payload) > MAX_REASSEMBLY_BYTES:
            raise FragmentBoundsError("reassembly byte bound exceeded")
        self._payloads[frame.index] = frame.payload
        self._buffered_bytes += len(frame.payload)
        if len(self._payloads) != self._count:
            return ReassemblyResult(None, False, len(self._payloads), self._buffered_bytes)
        assert self._count is not None and self._total_length is not None and self._message_id is not None
        message = b"".join(self._payloads[index] for index in range(self._count))
        if len(message) != self._total_length:
            raise FragmentDecodeError("reassembled message length mismatch")
        if hashlib.sha256(message).digest() != self._message_id:
            raise FragmentDecodeError("reassembled message identity mismatch")
        validate_complete_message(message)
        self._clear_incomplete()
        self._completed = identity
        return ReassemblyResult(message, False, 0, 0)


class BoundedFragmentStreamReader:
    """Recover complete B4 frames from arbitrary ordered-stream reads."""

    def __init__(self, *, max_frame_bytes: int, max_frames: int = MAX_FRAGMENTS_PER_CONTACT) -> None:
        _validate_mtu(max_frame_bytes)
        if type(max_frames) is not int or not 1 <= max_frames <= MAX_FRAGMENTS_PER_CONTACT:
            raise FragmentBoundsError("frame count bound is outside limits")
        self.max_frame_bytes = max_frame_bytes
        self.max_frames = max_frames
        self._buffer = bytearray()
        self._expected: int | None = None
        self._closed = False
        self.frame_count = 0
        self.maximum_buffer_bytes = 0

    def feed(self, data: bytes) -> tuple[bytes, ...]:
        if self._closed:
            raise FragmentationError("fragment stream reader is closed")
        if not isinstance(data, bytes):
            raise TypeError("stream data must be bytes")
        frames: list[bytes] = []
        view = memoryview(data)
        offset = 0
        while offset < len(view):
            target = FRAGMENT_HEADER_BYTES if self._expected is None else self._expected
            take = min(target - len(self._buffer), len(view) - offset)
            self._buffer.extend(view[offset : offset + take])
            offset += take
            self.maximum_buffer_bytes = max(self.maximum_buffer_bytes, len(self._buffer))
            if self.maximum_buffer_bytes > self.max_frame_bytes:
                raise FragmentBoundsError("fragment stream buffer exceeded MTU")
            if self._expected is None and len(self._buffer) == FRAGMENT_HEADER_BYTES:
                magic, version, frame_type, _mid, total, index, count, payload_len, _crc = _FRAGMENT_HEADER.unpack(self._buffer)
                if magic != B4_FRAGMENT_MAGIC:
                    raise FragmentDecodeError("invalid fragment magic")
                if version != B4_FRAGMENT_VERSION:
                    raise FragmentDecodeError("unsupported fragment version")
                if frame_type != B4_FRAGMENT_TYPE_DATA:
                    raise FragmentDecodeError("unknown fragment type")
                if not 1 <= total <= MAX_FRAGMENTED_MESSAGE_BYTES:
                    raise FragmentBoundsError("declared total length is outside B2 bounds")
                if not 1 <= count <= MAX_FRAGMENTS_PER_MESSAGE or index >= count:
                    raise FragmentBoundsError("fragment index/count is outside bounds")
                if not 1 <= payload_len <= self.max_frame_bytes - FRAGMENT_HEADER_BYTES:
                    raise FragmentBoundsError("declared fragment payload exceeds MTU")
                self._expected = FRAGMENT_HEADER_BYTES + payload_len
            if self._expected is not None and len(self._buffer) == self._expected:
                if self.frame_count >= self.max_frames:
                    raise FragmentBoundsError("fragment stream exceeds contact frame bound")
                frame = bytes(self._buffer)
                FragmentFrame.decode(frame, max_frame_bytes=self.max_frame_bytes)
                frames.append(frame)
                self.frame_count += 1
                self._buffer.clear()
                self._expected = None
        return tuple(frames)

    def close(self) -> None:
        self._closed = True
        if self._buffer:
            raise IncompleteFragmentStreamError("EOF inside B4 fragment")


@dataclass(frozen=True, slots=True)
class FragmentAccounting:
    message_bytes: int
    fragment_count: int
    fragment_payload_bytes: int
    total_fragment_bytes: int
    fragment_overhead_bytes: int
    overhead_percent: float


def fragmentation_accounting(encoded: bytes, *, max_frame_bytes: int) -> FragmentAccounting:
    frames = fragment_message(encoded, max_frame_bytes=max_frame_bytes)
    total = sum(len(frame.encode()) for frame in frames)
    overhead = total - len(encoded)
    return FragmentAccounting(
        len(encoded), len(frames), len(encoded), total, overhead, overhead * 100 / len(encoded)
    )


def read_fragmented_messages(
    source: BinaryIO,
    *,
    max_frame_bytes: int,
    read_size: int = 4096,
) -> tuple[tuple[bytes, ...], int, int]:
    if type(read_size) is not int or not 1 <= read_size <= MAX_FRAGMENTED_MESSAGE_BYTES:
        raise FragmentBoundsError("read size is outside bounds")
    stream = BoundedFragmentStreamReader(max_frame_bytes=max_frame_bytes)
    reassembler = EphemeralFragmentReassembler(max_frame_bytes=max_frame_bytes)
    messages: list[bytes] = []
    read_calls = 0
    while True:
        chunk = source.read(read_size)
        read_calls += 1
        if not chunk:
            break
        for frame in stream.feed(chunk):
            result = reassembler.add(frame)
            if result.complete_message is not None:
                messages.append(result.complete_message)
    stream.close()
    if reassembler.incomplete:
        raise IncompleteReassemblyError("contact ended with an incomplete fragmented message")
    return tuple(messages), read_calls, stream.frame_count


__all__ = [
    "B4_FRAGMENT_MAGIC",
    "B4_FRAGMENT_TYPE_DATA",
    "B4_FRAGMENT_VERSION",
    "BoundedFragmentStreamReader",
    "ConflictingFragmentError",
    "CrossMessageFragmentError",
    "EXPERIMENTAL_B4_FRAGMENT_ENCODING",
    "EphemeralFragmentReassembler",
    "FRAGMENT_HEADER_BYTES",
    "FragmentAccounting",
    "FragmentBoundsError",
    "FragmentDecodeError",
    "FragmentFrame",
    "FragmentationError",
    "IncompleteFragmentStreamError",
    "IncompleteReassemblyError",
    "MAX_FRAGMENTED_MESSAGE_BYTES",
    "MAX_FRAGMENT_BYTES_PER_CONTACT",
    "MAX_FRAGMENT_FRAME_BYTES",
    "MAX_FRAGMENT_METADATA_ENTRIES",
    "MAX_FRAGMENTS_PER_CONTACT",
    "MAX_FRAGMENTS_PER_MESSAGE",
    "MAX_REASSEMBLY_BYTES",
    "MAX_SIMULTANEOUS_INCOMPLETE_MESSAGES",
    "MIN_FRAGMENT_FRAME_BYTES",
    "ReassemblyResult",
    "fragment_message",
    "fragmentation_accounting",
    "read_fragmented_messages",
]
