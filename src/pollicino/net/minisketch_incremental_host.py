from __future__ import annotations

from dataclasses import dataclass
import ctypes
import os
import time

from .minisketch_host import (
    MINISKETCH_BITS,
    MINISKETCH_UPSTREAM_COMMIT,
    _MinisketchLibrary,
    _available_indices,
    _library_path,
)
from .store import AvailabilitySummary


@dataclass(frozen=True, slots=True)
class HostMinisketchSerialization:
    capacity: int
    serialized: bytes
    build_ns: int
    serialize_ns: int
    upstream_commit: str = MINISKETCH_UPSTREAM_COMMIT

    @property
    def serialized_bytes(self) -> int:
        return len(self.serialized)


@dataclass(frozen=True, slots=True)
class HostMinisketchDecodeAttempt:
    capacity: int
    native_decode_succeeded: bool
    decoded_indices: tuple[int, ...] | None
    left_only_indices: tuple[int, ...] | None
    right_only_indices: tuple[int, ...] | None
    merge_decode_ns: int
    upstream_commit: str = MINISKETCH_UPSTREAM_COMMIT


def serialize_availability_minisketch(
    summary: AvailabilitySummary,
    *,
    capacity: int,
    library_path: str | os.PathLike[str] | None = None,
) -> HostMinisketchSerialization:
    """Build one upstream sketch for incremental-serialization experiments."""

    if not isinstance(summary, AvailabilitySummary):
        raise TypeError("summary must be AvailabilitySummary")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        raise ValueError("capacity must be a positive integer")

    native = _MinisketchLibrary(_library_path(library_path))
    sketch = native.create(capacity=capacity)
    try:
        start = time.perf_counter_ns()
        for index in _available_indices(summary):
            native.lib.minisketch_add_uint64(sketch, index + 1)
        build_ns = time.perf_counter_ns() - start

        size = native.lib.minisketch_serialized_size(sketch)
        raw = (ctypes.c_ubyte * size)()
        start = time.perf_counter_ns()
        native.lib.minisketch_serialize(sketch, raw)
        serialize_ns = time.perf_counter_ns() - start
        return HostMinisketchSerialization(
            capacity=capacity,
            serialized=bytes(raw),
            build_ns=build_ns,
            serialize_ns=serialize_ns,
        )
    finally:
        native.lib.minisketch_destroy(sketch)


def attempt_decode_minisketch_prefix(
    serialized_prefix: bytes,
    receiver: AvailabilitySummary,
    *,
    capacity: int,
    library_path: str | os.PathLike[str] | None = None,
) -> HostMinisketchDecodeAttempt:
    """Try decoding one capacity-sized prefix against receiver local state.

    When a sketch is under-capacity, upstream may either return decode failure or
    (with low probability) a false decode. This research helper deliberately
    reports native success without calling it exact; experiments that know the
    ground truth must validate the decoded set separately.
    """

    if not isinstance(serialized_prefix, bytes):
        raise TypeError("serialized_prefix must be bytes")
    if not isinstance(receiver, AvailabilitySummary):
        raise TypeError("receiver must be AvailabilitySummary")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        raise ValueError("capacity must be a positive integer")

    native = _MinisketchLibrary(_library_path(library_path))
    remote = native.create(capacity=capacity)
    local = native.create(capacity=capacity)
    try:
        expected_size = native.lib.minisketch_serialized_size(remote)
        if len(serialized_prefix) != expected_size:
            raise ValueError(
                f"capacity {capacity} requires {expected_size} serialized bytes, "
                f"got {len(serialized_prefix)}"
            )

        incoming = (ctypes.c_ubyte * len(serialized_prefix)).from_buffer_copy(
            serialized_prefix
        )
        native.lib.minisketch_deserialize(remote, incoming)
        for index in _available_indices(receiver):
            native.lib.minisketch_add_uint64(local, index + 1)

        start = time.perf_counter_ns()
        merged = native.lib.minisketch_merge(local, remote)
        if merged == 0:
            return HostMinisketchDecodeAttempt(
                capacity=capacity,
                native_decode_succeeded=False,
                decoded_indices=None,
                left_only_indices=None,
                right_only_indices=None,
                merge_decode_ns=time.perf_counter_ns() - start,
            )
        output = (ctypes.c_uint64 * capacity)()
        count = native.lib.minisketch_decode(local, capacity, output)
        elapsed = time.perf_counter_ns() - start
        if count < 0:
            return HostMinisketchDecodeAttempt(
                capacity=capacity,
                native_decode_succeeded=False,
                decoded_indices=None,
                left_only_indices=None,
                right_only_indices=None,
                merge_decode_ns=elapsed,
            )

        decoded = []
        for position in range(count):
            element = int(output[position])
            if not 1 <= element <= receiver.chunk_count:
                # Treat an out-of-namespace false decode as unusable rather than
                # surfacing it as a valid Pollicino chunk index.
                return HostMinisketchDecodeAttempt(
                    capacity=capacity,
                    native_decode_succeeded=False,
                    decoded_indices=None,
                    left_only_indices=None,
                    right_only_indices=None,
                    merge_decode_ns=elapsed,
                )
            decoded.append(element - 1)
        decoded_tuple = tuple(sorted(decoded))
        receiver_set = set(_available_indices(receiver))
        left_only = tuple(
            index for index in decoded_tuple if index not in receiver_set
        )
        right_only = tuple(
            index for index in decoded_tuple if index in receiver_set
        )
        return HostMinisketchDecodeAttempt(
            capacity=capacity,
            native_decode_succeeded=True,
            decoded_indices=decoded_tuple,
            left_only_indices=left_only,
            right_only_indices=right_only,
            merge_decode_ns=elapsed,
        )
    finally:
        native.lib.minisketch_destroy(local)
        native.lib.minisketch_destroy(remote)
