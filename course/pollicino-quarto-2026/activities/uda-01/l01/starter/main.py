from __future__ import annotations

from pathlib import Path


def read_prefix(path: str | Path, n: int = 16) -> bytes:
    """Return at most the first *n* bytes of *path*.

    TODO: open the file in binary mode and return its first n bytes.
    """
    raise NotImplementedError


def describe_byte(value: int) -> dict[str, str | int]:
    """Describe one byte in decimal, binary and hexadecimal.

    TODO: validate that value is in [0, 255] and complete the dictionary.
    """
    raise NotImplementedError


def inspect_file(path: str | Path, n: int = 16) -> list[dict[str, str | int]]:
    """Return a row for each byte in the file prefix."""
    return [describe_byte(value) for value in read_prefix(path, n)]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Inspect the first bytes of a file.")
    parser.add_argument("path")
    parser.add_argument("-n", type=int, default=16)
    args = parser.parse_args()

    for index, row in enumerate(inspect_file(args.path, args.n)):
        print(
            f"{index:02d}  dec={row['decimal']:3d}  "
            f"bin={row['binary']}  hex={row['hex']}"
        )


if __name__ == "__main__":
    main()
