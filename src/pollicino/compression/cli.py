from __future__ import annotations

import argparse
import json
from pathlib import Path

from .codec import decode_pol, encode_static_histogram, encode_uniform, inspect_pol


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pollicino", description="POLLICINO lossless codec tools")
    sub = parser.add_subparsers(dest="command", required=True)
    compress = sub.add_parser("compress", help="compress a file into .pol")
    compress.add_argument("input", type=Path); compress.add_argument("output", type=Path)
    compress.add_argument("--mode", choices=("static", "uniform"), default="static")
    compress.add_argument("--precision-bits", type=int, default=15)
    restore = sub.add_parser("restore", help="restore a self-contained .pol file")
    restore.add_argument("input", type=Path); restore.add_argument("output", type=Path)
    inspect = sub.add_parser("inspect", help="print .pol metadata as JSON")
    inspect.add_argument("input", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "compress":
        data = args.input.read_bytes()
        blob = encode_static_histogram(data, args.precision_bits) if args.mode == "static" else encode_uniform(data, args.precision_bits)
        args.output.write_bytes(blob); return 0
    if args.command == "restore":
        args.output.write_bytes(decode_pol(args.input.read_bytes())); return 0
    if args.command == "inspect":
        print(json.dumps(inspect_pol(args.input.read_bytes()), indent=2, sort_keys=True)); return 0
    raise AssertionError("unreachable")

if __name__ == "__main__": raise SystemExit(main())
