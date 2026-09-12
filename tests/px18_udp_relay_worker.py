from __future__ import annotations

import argparse
import json
import socket
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket-fd", type=int, required=True)
    parser.add_argument("--a-port", type=int, required=True)
    parser.add_argument("--b-port", type=int, required=True)
    parser.add_argument("--action", choices=("PASS", "DROP", "DROP_A_INDEX", "DUPLICATE", "REORDER", "DELAY", "CORRUPT", "PERMANENT_DROP"), default="PASS")
    parser.add_argument("--drop-index", type=int, default=1)
    args = parser.parse_args()
    active = socket.socket(fileno=args.socket_fd)
    active.settimeout(0.8)
    a = ("127.0.0.1", args.a_port)
    b = ("127.0.0.1", args.b_port)
    received = forwarded = dropped = duplicated = reordered = corrupted = 0
    from_a = 0
    held: tuple[bytes, tuple[str, int]] | None = None
    acted = False
    try:
        while True:
            try:
                payload, source = active.recvfrom(4097)
            except socket.timeout:
                break
            received += 1
            destination = b if source == a else a if source == b else None
            if destination is None:
                dropped += 1
                continue
            if args.action == "PERMANENT_DROP" and source == a:
                dropped += 1
                continue
            if source == a:
                from_a += 1
            if args.action == "DROP_A_INDEX" and source == a and from_a == args.drop_index:
                dropped += 1
                continue
            if not acted and args.action == "DROP":
                acted = True; dropped += 1; continue
            if not acted and args.action == "CORRUPT":
                acted = True; corrupted += 1
                changed = bytearray(payload); changed[-1] ^= 1; payload = bytes(changed)
            if not acted and args.action in ("REORDER", "DELAY"):
                if held is None:
                    held = (payload, destination); continue
                active.sendto(payload, destination); forwarded += 1
                active.sendto(held[0], held[1]); forwarded += 1
                held = None; acted = True; reordered += 1
                continue
            active.sendto(payload, destination); forwarded += 1
            if not acted and args.action == "DUPLICATE":
                active.sendto(payload, destination); forwarded += 1
                duplicated += 1; acted = True
        if held is not None:
            active.sendto(held[0], held[1]); forwarded += 1
    finally:
        active.close()
    print(json.dumps({
        "received": received, "forwarded": forwarded, "dropped": dropped,
        "duplicated": duplicated, "reordered": reordered, "corrupted": corrupted,
        "application_semantics": 0, "reconciliation_authority": 0, "b2_semantics": 0,
    }, sort_keys=True), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
