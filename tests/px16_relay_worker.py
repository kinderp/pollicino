from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", type=Path, required=True)
    parser.add_argument("--a", type=Path, required=True)
    parser.add_argument("--b", type=Path, required=True)
    parser.add_argument("--actions", default="")
    parser.add_argument("--timeout", type=float, default=0.6)
    args = parser.parse_args()
    actions = args.actions.split(",") if args.actions else []
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.settimeout(args.timeout)
    sock.bind(os.fspath(args.local))
    received = forwarded = dropped = duplicated = reordered = corrupted = send_failures = 0
    held: tuple[bytes, Path] | None = None
    try:
        while True:
            try:
                payload, source = sock.recvfrom(4097)
            except socket.timeout:
                break
            received += 1
            source_path = Path(source)
            destination = args.b if source_path == args.a else args.a
            action = actions[received - 1] if received <= len(actions) else "PASS"
            if action == "DROP":
                dropped += 1; continue
            if action == "CORRUPT":
                value = bytearray(payload); value[-1] ^= 1; payload = bytes(value); corrupted += 1
            if action in ("DELAY", "REORDER"):
                held = (payload, destination); reordered += 1; continue
            try:
                sock.sendto(payload, os.fspath(destination)); forwarded += 1
            except OSError:
                send_failures += 1
                continue
            if action == "DUP":
                try:
                    sock.sendto(payload, os.fspath(destination)); forwarded += 1; duplicated += 1
                except OSError:
                    send_failures += 1
            if held is not None:
                delayed, target = held
                try:
                    sock.sendto(delayed, os.fspath(target)); forwarded += 1
                except OSError:
                    send_failures += 1
                held = None
    finally:
        sock.close()
        try: args.local.unlink()
        except FileNotFoundError: pass
    print(json.dumps({"received": received, "forwarded": forwarded, "dropped": dropped,
                      "duplicated": duplicated, "reordered": reordered,
                      "corrupted": corrupted, "send_failures": send_failures,
                      "application_semantics": 0}), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
