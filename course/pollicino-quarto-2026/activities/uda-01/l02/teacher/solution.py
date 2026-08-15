from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_hex(Path(path).read_bytes())


def truncated_hash_int(data: bytes, bits: int) -> int:
    if not 1 <= bits <= 256:
        raise ValueError("bits must be between 1 and 256")
    digest = int.from_bytes(hashlib.sha256(data).digest(), "big")
    return digest >> (256 - bits)


def find_collision(bits: int, limit: int = 10_000) -> tuple[bytes, bytes, int] | None:
    if limit < 0:
        raise ValueError("limit must be non-negative")
    seen: dict[int, bytes] = {}
    for index in range(limit):
        candidate = f"candidate-{index}".encode()
        digest = truncated_hash_int(candidate, bits)
        previous = seen.get(digest)
        if previous is not None and previous != candidate:
            return previous, candidate, digest
        seen[digest] = candidate
    return None


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
