from __future__ import annotations

import hashlib
import math
import shutil
from pathlib import Path


def byte_counts(data: bytes) -> list[int]:
    """Return 256 counters, one for each possible byte."""
    # TODO
    raise NotImplementedError


def shannon_entropy(data: bytes) -> float:
    """Return zero-order Shannon entropy in bits per byte."""
    # TODO: empty input has entropy 0.
    raise NotImplementedError


def uniform_code_length_bits(data: bytes) -> int:
    """Cost of a uniform 256-symbol model."""
    # TODO
    raise NotImplementedError


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def roundtrip_copy(source: str | Path, destination: str | Path) -> tuple[str, str]:
    """Copy a file byte-for-byte and return hashes before/after."""
    # TODO: copy bytes without text decoding.
    raise NotImplementedError


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    data = Path(args.path).read_bytes()
    print(f"bytes: {len(data)}")
    print(f"uniform baseline: {uniform_code_length_bits(data)} bit")
    print(f"entropy: {shannon_entropy(data):.6f} bit/byte")
