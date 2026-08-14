"""Uniform 256-symbol baseline.

This module establishes the zero point for byte-level predictive compression:
P(byte) = 1/256, hence ideal code length = 8 bits/byte.

The round-trip operation here is intentionally an identity transform. It is not
presented as a compressor; it is a correctness/control experiment that later
entropy coders must preserve while reducing realized payload size on predictable
data.
"""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path

from pollicino.common.metrics import mean_bits_per_symbol


@dataclass(frozen=True)
class UniformBaselineResult:
    path: Path
    input_bytes: int
    theoretical_bits_per_byte: float
    sha256_original: str
    sha256_decoded: str
    round_trip_ok: bool


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def evaluate_bytes(data: bytes, *, path: Path | None = None) -> UniformBaselineResult:
    # Natural-log negative log-likelihood for p = 1/256.
    import math

    nll = -math.log(1.0 / 256.0)
    bpb = mean_bits_per_symbol([nll])

    # Milestone 0 reversible control: identity payload / identity decode.
    payload = bytes(data)
    decoded = bytes(payload)

    original_hash = sha256_bytes(data)
    decoded_hash = sha256_bytes(decoded)
    return UniformBaselineResult(
        path=path or Path("<memory>"),
        input_bytes=len(data),
        theoretical_bits_per_byte=bpb,
        sha256_original=original_hash,
        sha256_decoded=decoded_hash,
        round_trip_ok=(decoded == data and decoded_hash == original_hash),
    )


def evaluate_file(path: str | Path) -> UniformBaselineResult:
    file_path = Path(path)
    return evaluate_bytes(file_path.read_bytes(), path=file_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="POLLICINO uniform-byte Milestone 0 baseline")
    parser.add_argument("file", type=Path, help="file to evaluate")
    args = parser.parse_args()

    result = evaluate_file(args.file)
    print(f"file: {result.path}")
    print(f"input_bytes: {result.input_bytes}")
    print(f"theoretical_bits_per_byte: {result.theoretical_bits_per_byte:.6f}")
    print(f"sha256_original: {result.sha256_original}")
    print(f"sha256_decoded:  {result.sha256_decoded}")
    print(f"round_trip_ok: {str(result.round_trip_ok).lower()}")
    return 0 if result.round_trip_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
