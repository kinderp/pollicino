from __future__ import annotations

from pathlib import Path


def read_prefix(path: str | Path, n: int = 16) -> bytes:
    if n < 0:
        raise ValueError("n must be non-negative")
    with Path(path).open("rb") as handle:
        return handle.read(n)


def describe_byte(value: int) -> dict[str, str | int]:
    if not 0 <= value <= 255:
        raise ValueError("a byte must be between 0 and 255")
    return {
        "decimal": value,
        "binary": f"{value:08b}",
        "hex": f"{value:02X}",
    }


def inspect_file(path: str | Path, n: int = 16) -> list[dict[str, str | int]]:
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
