from __future__ import annotations

import hashlib
import math
from pathlib import Path


def byte_counts(data: bytes) -> list[int]:
    counts = [0] * 256
    for value in data:
        counts[value] += 1
    return counts


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    total = len(data)
    entropy = 0.0
    for count in byte_counts(data):
        if count:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def uniform_code_length_bits(data: bytes) -> int:
    return 8 * len(data)


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def roundtrip_copy(source: str | Path, destination: str | Path) -> tuple[str, str]:
    source = Path(source)
    destination = Path(destination)
    original = source.read_bytes()
    before = hashlib.sha256(original).hexdigest()
    destination.write_bytes(original)
    after = hashlib.sha256(destination.read_bytes()).hexdigest()
    return before, after


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    data = Path(args.path).read_bytes()
    print(f"bytes: {len(data)}")
    print(f"uniform baseline: {uniform_code_length_bits(data)} bit")
    print(f"entropy: {shannon_entropy(data):.6f} bit/byte")
