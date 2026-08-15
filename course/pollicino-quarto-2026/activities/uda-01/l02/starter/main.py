from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_hex(data: bytes) -> str:
    """Return the SHA-256 digest as lowercase hexadecimal."""
    # TODO
    raise NotImplementedError


def sha256_file(path: str | Path) -> str:
    """Return the SHA-256 of a file."""
    # TODO: read bytes, not text.
    raise NotImplementedError


def truncated_hash_int(data: bytes, bits: int) -> int:
    """Return the first *bits* of SHA-256 as an integer.

    This is only a teaching tool: truncating a cryptographic hash makes
    collisions deliberately easy to observe.
    """
    # TODO: accept bits from 1 to 256 and keep exactly the leftmost bits.
    raise NotImplementedError


def find_collision(bits: int, limit: int = 10_000) -> tuple[bytes, bytes, int] | None:
    """Search deterministic candidates for a collision of a truncated hash."""
    # TODO: store seen digest -> candidate and return two distinct inputs.
    raise NotImplementedError


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--bits", type=int, default=8)
    args = parser.parse_args()

    collision = find_collision(args.bits)
    if collision is None:
        print("No collision found in the search limit.")
        return
    left, right, digest = collision
    print(f"{left!r} and {right!r} -> truncated digest {digest}")


if __name__ == "__main__":
    main()
