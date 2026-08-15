from __future__ import annotations

import random
from pathlib import Path


def read_bytes(path: str | Path) -> bytes:
    # TODO: read binary bytes
    raise NotImplementedError


def contiguous_split(data: bytes, train_fraction: float = 0.8, val_fraction: float = 0.1) -> tuple[bytes, bytes, bytes]:
    """Split bytes contiguously into train/validation/test without overlap."""
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be in (0, 1)")
    if not 0 <= val_fraction < 1:
        raise ValueError("val_fraction must be in [0, 1)")
    if train_fraction + val_fraction >= 1:
        raise ValueError("train + val fractions must be < 1")
    # TODO: contiguous non-overlapping split
    raise NotImplementedError


def make_examples(data: bytes, context_length: int, stride: int = 1) -> list[tuple[list[int], list[int]]]:
    """Return autoregressive (x, y) windows where y is x shifted by one byte."""
    if context_length <= 0 or stride <= 0:
        raise ValueError("context_length and stride must be positive")
    if len(data) <= context_length:
        return []
    # TODO: build x and shifted y windows
    raise NotImplementedError


def batch_iter(examples: list[tuple[list[int], list[int]]], batch_size: int, *, shuffle: bool = False, seed: int = 0):
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    indices=list(range(len(examples)))
    if shuffle:
        random.Random(seed).shuffle(indices)
    for start in range(0, len(indices), batch_size):
        chunk=indices[start:start+batch_size]
        yield [examples[i][0] for i in chunk], [examples[i][1] for i in chunk]
