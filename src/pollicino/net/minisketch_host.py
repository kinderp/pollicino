from __future__ import annotations

from dataclasses import dataclass
import ctypes
import os
from pathlib import Path
import time

from .store import AvailabilitySummary, MAX_CHUNKS


MINISKETCH_UPSTREAM_COMMIT = "4a179c61e3cbe3ac2b3c027764ce8eb5183155e1"
MINISKETCH_BITS = 16
MINISKETCH_IMPLEMENTATION = 0
MINISKETCH_LIBRARY_ENV = "POLLICINO_MINISKETCH_LIB"


class MinisketchUnavailable(RuntimeError):
    """Raised when the optional host-side libminisketch cannot be loaded."""


class MinisketchDecodeError(RuntimeError):
    """Raised when libminisketch cannot decode within the requested capacity."""


@dataclass(frozen=True, slots=True)
class HostMinisketchTimings:
    build_left_ns: int
    build_right_ns: int
    serialize_left_ns: int
    merge_decode_ns: int


@dataclass(frozen=True, slots=True)
class HostMinisketchReconciliation:
    bits: int
    capacity: int
    serialized_sketch: bytes
    symmetric_difference_indices: tuple[int, ...]
    left_only_indices: tuple[int, ...]
    right_only_indices: tuple[int, ...]
    timings: HostMinisketchTimings
    upstream_commit: str = MINISKETCH_UPSTREAM_COMMIT
    evidence_class: str = "host_optional_native"

    @property
    def serialized_sketch_bytes(self) -> int:
        return len(self.serialized_sketch)


class _MinisketchLibrary:
    def __init__(self, path: str | os.PathLike[str]) -> None:
        library_path = Path(path)
        if not library_path.is_file():
            raise MinisketchUnavailable(
                f"libminisketch does not exist at {library_path}"
            )
        try:
            lib = ctypes.CDLL(str(library_path))
        except OSError as exc:
            raise MinisketchUnavailable(
                f"cannot load libminisketch at {library_path}: {exc}"
            ) from exc

        ptr = ctypes.c_void_p
        lib.minisketch_bits_supported.argtypes = [ctypes.c_uint32]
        lib.minisketch_bits_supported.restype = ctypes.c_int
        lib.minisketch_implementation_supported.argtypes = [
            ctypes.c_uint32,
            ctypes.c_uint32,
        ]
        lib.minisketch_implementation_supported.restype = ctypes.c_int
        lib.minisketch_create.argtypes = [
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_size_t,
        ]
        lib.minisketch_create.restype = ptr
        lib.minisketch_destroy.argtypes = [ptr]
        lib.minisketch_destroy.restype = None
        lib.minisketch_set_seed.argtypes = [ptr, ctypes.c_uint64]
        lib.minisketch_set_seed.restype = None
        lib.minisketch_add_uint64.argtypes = [ptr, ctypes.c_uint64]
        lib.minisketch_add_uint64.restype = None
        lib.minisketch_serialized_size.argtypes = [ptr]
        lib.minisketch_serialized_size.restype = ctypes.c_size_t
        lib.minisketch_serialize.argtypes = [ptr, ctypes.POINTER(ctypes.c_ubyte)]
        lib.minisketch_serialize.restype = None
        lib.minisketch_deserialize.argtypes = [
            ptr,
            ctypes.POINTER(ctypes.c_ubyte),
        ]
        lib.minisketch_deserialize.restype = None
        lib.minisketch_merge.argtypes = [ptr, ptr]
        lib.minisketch_merge.restype = ctypes.c_size_t
        lib.minisketch_decode.argtypes = [
            ptr,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint64),
        ]
        lib.minisketch_decode.restype = ctypes.c_ssize_t
        self.lib = lib

    def create(self, *, capacity: int) -> ctypes.c_void_p:
        if self.lib.minisketch_bits_supported(MINISKETCH_BITS) != 1:
            raise MinisketchUnavailable(
                f"loaded libminisketch lacks {MINISKETCH_BITS}-bit field support"
            )
        if (
            self.lib.minisketch_implementation_supported(
                MINISKETCH_BITS,
                MINISKETCH_IMPLEMENTATION,
            )
            != 1
        ):
            raise MinisketchUnavailable(
                "loaded libminisketch lacks implementation 0 for 16-bit fields"
            )
        sketch = self.lib.minisketch_create(
            MINISKETCH_BITS,
            MINISKETCH_IMPLEMENTATION,
            capacity,
        )
        if not sketch:
            raise MinisketchUnavailable("minisketch_create returned NULL")
        # Upstream documents UINT64_MAX (C API seed=-1) as deterministic testing
        # behavior. Do not use this deterministic seed in a security-sensitive
        # production protocol.
        self.lib.minisketch_set_seed(sketch, ctypes.c_uint64(0xFFFFFFFFFFFFFFFF))
        return sketch


def _library_path(explicit: str | os.PathLike[str] | None) -> Path:
    if explicit is not None:
        return Path(explicit)
    configured = os.environ.get(MINISKETCH_LIBRARY_ENV)
    if not configured:
        raise MinisketchUnavailable(
            f"optional host adapter requires {MINISKETCH_LIBRARY_ENV}"
        )
    return Path(configured)


def _validate_summary_pair(
    left: AvailabilitySummary,
    right: AvailabilitySummary,
) -> None:
    if not isinstance(left, AvailabilitySummary) or not isinstance(
        right, AvailabilitySummary
    ):
        raise TypeError("left/right must be AvailabilitySummary values")
    if left.manifest_fingerprint != right.manifest_fingerprint:
        raise ValueError("minisketch peers must target the same manifest")
    if left.chunk_count != right.chunk_count:
        raise ValueError("minisketch peers must have the same chunk_count")
    if left.chunk_count > MAX_CHUNKS:
        raise ValueError("chunk_count exceeds current PCM1 limit")


def _available_indices(summary: AvailabilitySummary) -> tuple[int, ...]:
    return tuple(
        index for index in range(summary.chunk_count) if summary.has(index)
    )


def reconcile_partial_caches_with_minisketch(
    left: AvailabilitySummary,
    right: AvailabilitySummary,
    *,
    capacity: int,
    library_path: str | os.PathLike[str] | None = None,
) -> HostMinisketchReconciliation:
    """Run the optional upstream libminisketch adapter on two partial caches.

    Chunk index ``i`` is represented as 16-bit field element ``i + 1`` because
    libminisketch treats element 0 as a no-op. Current PCM1 indices 0..65,534
    therefore map exactly to 1..65,535 without hashing or collisions.

    The returned LEFT/RIGHT classification uses only RIGHT's local membership,
    matching the standard symmetric-difference reconciliation pattern: a decoded
    element that RIGHT already has is RIGHT-only; otherwise it is LEFT-only.
    """

    _validate_summary_pair(left, right)
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        raise ValueError("capacity must be a positive integer")

    native = _MinisketchLibrary(_library_path(library_path))
    left_indices = _available_indices(left)
    right_indices = _available_indices(right)
    right_set = set(right_indices)

    sketch_left = native.create(capacity=capacity)
    sketch_right = native.create(capacity=capacity)
    received_left = None
    try:
        start = time.perf_counter_ns()
        for index in left_indices:
            native.lib.minisketch_add_uint64(sketch_left, index + 1)
        build_left_ns = time.perf_counter_ns() - start

        start = time.perf_counter_ns()
        for index in right_indices:
            native.lib.minisketch_add_uint64(sketch_right, index + 1)
        build_right_ns = time.perf_counter_ns() - start

        serialized_size = native.lib.minisketch_serialized_size(sketch_left)
        raw_buffer = (ctypes.c_ubyte * serialized_size)()
        start = time.perf_counter_ns()
        native.lib.minisketch_serialize(sketch_left, raw_buffer)
        serialize_left_ns = time.perf_counter_ns() - start
        serialized = bytes(raw_buffer)

        received_left = native.create(capacity=capacity)
        incoming_buffer = (ctypes.c_ubyte * len(serialized)).from_buffer_copy(
            serialized
        )
        native.lib.minisketch_deserialize(received_left, incoming_buffer)

        start = time.perf_counter_ns()
        merged_capacity = native.lib.minisketch_merge(sketch_right, received_left)
        if merged_capacity == 0:
            raise MinisketchDecodeError("minisketch_merge rejected compatible sketches")
        output = (ctypes.c_uint64 * capacity)()
        decoded_count = native.lib.minisketch_decode(
            sketch_right,
            capacity,
            output,
        )
        merge_decode_ns = time.perf_counter_ns() - start
        if decoded_count < 0:
            raise MinisketchDecodeError(
                "symmetric difference exceeds capacity or decode failed"
            )

        decoded_indices = []
        for position in range(decoded_count):
            element = int(output[position])
            if not 1 <= element <= left.chunk_count:
                raise MinisketchDecodeError(
                    f"decoded field element {element} is outside manifest namespace"
                )
            decoded_indices.append(element - 1)
        decoded = tuple(sorted(decoded_indices))
        left_only = tuple(index for index in decoded if index not in right_set)
        right_only = tuple(index for index in decoded if index in right_set)

        return HostMinisketchReconciliation(
            bits=MINISKETCH_BITS,
            capacity=capacity,
            serialized_sketch=serialized,
            symmetric_difference_indices=decoded,
            left_only_indices=left_only,
            right_only_indices=right_only,
            timings=HostMinisketchTimings(
                build_left_ns=build_left_ns,
                build_right_ns=build_right_ns,
                serialize_left_ns=serialize_left_ns,
                merge_decode_ns=merge_decode_ns,
            ),
        )
    finally:
        if received_left:
            native.lib.minisketch_destroy(received_left)
        native.lib.minisketch_destroy(sketch_right)
        native.lib.minisketch_destroy(sketch_left)
