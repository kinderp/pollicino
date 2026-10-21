from __future__ import annotations

import ctypes
import os

from .minisketch_host import (
    MINISKETCH_BITS,
    MINISKETCH_UPSTREAM_COMMIT,
    _MinisketchLibrary,
    _library_path,
)


def compute_host_minisketch_capacity(
    max_elements: int,
    *,
    fpbits: int,
    library_path: str | os.PathLike[str] | None = None,
) -> int:
    """Call upstream ``minisketch_compute_capacity`` for the 16-bit host model.

    ``max_elements`` is the difference count the protocol wants to decode while
    ``fpbits`` requests an upper bound of roughly 2^-fpbits for false-positive
    decodes when the true difference is larger. This is upstream's capacity
    policy helper, not a Pollicino security recommendation.
    """

    if (
        isinstance(max_elements, bool)
        or not isinstance(max_elements, int)
        or max_elements <= 0
    ):
        raise ValueError("max_elements must be a positive integer")
    if isinstance(fpbits, bool) or not isinstance(fpbits, int) or fpbits < 0:
        raise ValueError("fpbits must be a non-negative integer")

    native = _MinisketchLibrary(_library_path(library_path))
    fn = native.lib.minisketch_compute_capacity
    fn.argtypes = [ctypes.c_uint32, ctypes.c_size_t, ctypes.c_uint32]
    fn.restype = ctypes.c_size_t
    capacity = int(fn(MINISKETCH_BITS, max_elements, fpbits))
    if capacity < max_elements:
        raise AssertionError("upstream capacity helper returned below max_elements")
    return capacity


def compute_host_minisketch_max_elements(
    capacity: int,
    *,
    fpbits: int,
    library_path: str | os.PathLike[str] | None = None,
) -> int:
    """Call upstream inverse helper for one 16-bit serialized capacity."""

    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        raise ValueError("capacity must be a positive integer")
    if isinstance(fpbits, bool) or not isinstance(fpbits, int) or fpbits < 0:
        raise ValueError("fpbits must be a non-negative integer")

    native = _MinisketchLibrary(_library_path(library_path))
    fn = native.lib.minisketch_compute_max_elements
    fn.argtypes = [ctypes.c_uint32, ctypes.c_size_t, ctypes.c_uint32]
    fn.restype = ctypes.c_size_t
    return int(fn(MINISKETCH_BITS, capacity, fpbits))


def modeled_raw_sketch_bytes(capacity: int) -> int:
    """Exact serialized size for 16-bit upstream sketches: 2 bytes/capacity."""

    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        raise ValueError("capacity must be a positive integer")
    return (MINISKETCH_BITS * capacity + 7) // 8


UPSTREAM_PIN = MINISKETCH_UPSTREAM_COMMIT
