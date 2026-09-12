from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .endpoint import B2ContactBudget, RecordKind
from .fragmentation import EphemeralFragmentReassembler, fragment_message
from .process_worker import (
    ROLE_GENERIC,
    ROLE_INITIATOR,
    ROLE_RESPONDER,
    _adaptive_initial,
    _consume,
    _open,
)
from .adaptive_reconciliation import AdaptiveIndependentEndpoint
from .compact_reconciliation import B2C_MAGIC, CompactIndependentEndpoint
from .fair_reconciliation import FairIndependentEndpoint
from .unix_datagram import UnixDatagramAdapter, UnixDatagramTimeout


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pollicino-unix-datagram-worker")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--local", type=Path, required=True)
    parser.add_argument("--peer", type=Path, required=True)
    parser.add_argument("--role", choices=("initiator", "responder"), required=True)
    parser.add_argument("--kind", choices=tuple(kind.name for kind in RecordKind), required=True)
    parser.add_argument("--mtu", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=0.25)
    parser.add_argument("--max-messages", type=int, default=100)
    parser.add_argument("--exact", action="store_true")
    parser.add_argument("--recover-stale", action="store_true")
    parser.add_argument("--crash-after-reassembly", action="store_true")
    parser.add_argument("--crash-after-commit", action="store_true")
    return parser


def _send(adapter: UnixDatagramAdapter, messages: tuple[bytes, ...], mtu: int) -> tuple[int, int]:
    frames = octets = 0
    for message in messages:
        for frame in fragment_message(message, max_frame_bytes=mtu):
            encoded = frame.encode()
            adapter.send_frame(encoded)
            frames += 1
            octets += len(encoded)
    return frames, octets


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    catalog = query_results = adapter = None
    diagnostics: dict[str, object] = {
        "role": args.role,
        "transport": "AF_UNIX/SOCK_DGRAM",
        "root_scope": "LOCAL_ONLY",
        "shared_endpoint_objects": 0,
    }
    try:
        catalog, query_results = _open(args.root)
        compact = CompactIndependentEndpoint(catalog, query_results)
        fair = FairIndependentEndpoint(catalog, query_results)
        adapter = UnixDatagramAdapter(
            args.local,
            args.peer,
            max_datagram_bytes=args.mtu,
            timeout=args.timeout,
            recover_stale=args.recover_stale,
        )
        reassembler = EphemeralFragmentReassembler(max_frame_bytes=args.mtu)
        sent_frames = sent_bytes = messages_in = commits = 0
        first_compact = True
        if args.role == "initiator":
            kind = RecordKind[args.kind]
            if args.exact:
                outbound = fair.directory_messages(kind)
                diagnostics["decision"] = "EXACT"
            else:
                outbound, decision = _adaptive_initial(
                    AdaptiveIndependentEndpoint(catalog, query_results),
                    kind,
                    (),
                    B2ContactBudget(max_bearer_attempts=args.max_messages, max_trace_entries=args.max_messages),
                )
                diagnostics["decision"] = decision
            count, octets = _send(adapter, outbound, args.mtu)
            sent_frames += count; sent_bytes += octets
        while messages_in < args.max_messages:
            try:
                encoded_frame = adapter.receive_frame()
            except UnixDatagramTimeout:
                diagnostics["ended"] = "IDLE_TIMEOUT"
                break
            result = reassembler.add(encoded_frame)
            if result.complete_message is None:
                continue
            if args.crash_after_reassembly:
                __import__("os")._exit(93)
            messages_in += 1
            role = ROLE_GENERIC
            if first_compact and result.complete_message[:4] == B2C_MAGIC:
                role = ROLE_INITIATOR if args.role == "initiator" else ROLE_RESPONDER
                first_compact = False
            responses, local = _consume(compact, fair, result.complete_message, role=role, selected=())
            commits += int(local.get("durable_commits", 0))
            if args.crash_after_commit and commits:
                __import__("os")._exit(94)
            count, octets = _send(adapter, responses, args.mtu)
            sent_frames += count; sent_bytes += octets
        diagnostics.update(
            {
                "process_id": __import__("os").getpid(),
                "protocol_messages_in": messages_in,
                "native_commits": commits,
                "datagrams_sent": adapter.accounting.sent,
                "datagram_bytes_sent": adapter.accounting.sent_bytes,
                "datagrams_received": adapter.accounting.received,
                "datagram_bytes_received": adapter.accounting.received_bytes,
                "receive_timeouts": adapter.accounting.receive_timeouts,
                "socket_buffers": adapter.socket_buffers,
                "b4_frames_sent": sent_frames,
                "b4_frame_bytes_sent": sent_bytes,
            }
        )
        print(json.dumps(diagnostics, sort_keys=True), file=sys.stderr)
        return 0
    except Exception as error:
        diagnostics.update({"error_type": type(error).__name__, "error": str(error)})
        print(json.dumps(diagnostics, sort_keys=True), file=sys.stderr)
        return 2
    finally:
        if adapter is not None:
            adapter.close()
        if catalog is not None:
            catalog.close()
        if query_results is not None:
            query_results.close()


if __name__ == "__main__":
    raise SystemExit(main())
