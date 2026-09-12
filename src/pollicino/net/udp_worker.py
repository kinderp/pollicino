from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket
import sys

from .adaptive_reconciliation import AdaptiveIndependentEndpoint
from .compact_reconciliation import B2C_MAGIC, CompactIndependentEndpoint
from .endpoint import B2ContactBudget, RecordKind
from .fair_reconciliation import FairIndependentEndpoint, ReferenceDirectoryRequestMessage, encode_fair_message
from .fragmentation import EphemeralFragmentReassembler, fragment_message
from .process_worker import ROLE_GENERIC, ROLE_INITIATOR, ROLE_RESPONDER, _adaptive_initial, _consume, _open, _selected
from .udp import UDPAdapter, UDPTimeout


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pollicino-udp-worker")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--local-host", default="127.0.0.1")
    parser.add_argument("--local-port", type=int, required=True)
    parser.add_argument("--peer-host", default="127.0.0.1")
    parser.add_argument("--peer-port", type=int, required=True)
    parser.add_argument("--socket-fd", type=int)
    parser.add_argument("--role", choices=("initiator", "responder"), required=True)
    parser.add_argument("--kind", choices=tuple(kind.name for kind in RecordKind), required=True)
    parser.add_argument("--mtu", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=0.25)
    parser.add_argument("--max-messages", type=int, default=100)
    parser.add_argument("--exact", action="store_true")
    parser.add_argument("--selected", action="append", default=[])
    parser.add_argument("--crash-after-reassembly", action="store_true")
    parser.add_argument("--crash-after-commit", action="store_true")
    parser.add_argument("--crash-after-send-batch", type=int)
    parser.add_argument("--crash-after-initial-send", action="store_true")
    return parser


def _send(adapter: UDPAdapter, messages: tuple[bytes, ...], mtu: int) -> tuple[int, int, int]:
    frames = octets = 0
    message_octets = sum(len(message) for message in messages)
    for message in messages:
        for frame in fragment_message(message, max_frame_bytes=mtu):
            encoded = frame.encode()
            adapter.send_frame(encoded)
            frames += 1
            octets += len(encoded)
    return frames, octets, message_octets


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    catalog = query_results = adapter = None
    diagnostics: dict[str, object] = {
        "role": args.role,
        "transport": "AF_INET/SOCK_DGRAM/127.0.0.1",
        "root_scope": "LOCAL_ONLY",
        "shared_endpoint_objects": 0,
    }
    compact_statuses: list[str] = []
    messages_in = commits = response_batches = 0
    try:
        catalog, query_results = _open(args.root)
        compact = CompactIndependentEndpoint(catalog, query_results)
        fair = FairIndependentEndpoint(catalog, query_results)
        active = socket.socket(fileno=args.socket_fd) if args.socket_fd is not None else None
        adapter = UDPAdapter(
            (args.local_host, args.local_port),
            (args.peer_host, args.peer_port),
            max_frame_bytes=args.mtu,
            timeout=args.timeout,
            active_socket=active,
        )
        reassembler = EphemeralFragmentReassembler(max_frame_bytes=args.mtu)
        selected = _selected(args.selected)
        sent_frames = sent_bytes = sent_message_bytes = 0
        first_compact = True
        if args.role == "initiator":
            kind = RecordKind[args.kind]
            if kind is RecordKind.REFERENCE and selected:
                outbound = (encode_fair_message(ReferenceDirectoryRequestMessage()),)
                diagnostics["decision"] = "EXPLICIT_REFERENCE"
            elif args.exact:
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
            count, octets, message_octets = _send(adapter, outbound, args.mtu)
            sent_frames += count; sent_bytes += octets; sent_message_bytes += message_octets
            if args.crash_after_initial_send:
                __import__("os")._exit(96)
        while messages_in < args.max_messages:
            try:
                encoded_frame = adapter.receive_frame()
            except UDPTimeout:
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
            responses, local = _consume(
                compact,
                fair,
                result.complete_message,
                role=role,
                selected=selected if args.role == "initiator" else (),
            )
            commits += int(local.get("durable_commits", 0))
            if "compact_status" in local:
                compact_statuses.append(str(local["compact_status"]))
            if args.crash_after_commit and commits:
                __import__("os")._exit(94)
            count, octets, message_octets = _send(adapter, responses, args.mtu)
            sent_frames += count; sent_bytes += octets; sent_message_bytes += message_octets
            if responses:
                response_batches += 1
                if args.crash_after_send_batch == response_batches:
                    __import__("os")._exit(95)
        accounting = adapter.accounting
        diagnostics.update({
            "process_id": __import__("os").getpid(),
            "local_address": adapter.local_address,
            "peer_address": adapter.peer_address,
            "protocol_messages_in": messages_in,
            "native_commits": commits,
            "compact_statuses": compact_statuses,
            "response_batches": response_batches,
            "b4_frames_sent": sent_frames,
            "b4_frame_bytes_sent": sent_bytes,
            "b2_message_bytes_sent": sent_message_bytes,
            "udp_datagrams_sent": accounting.sent,
            "udp_payload_bytes_sent": accounting.sent_bytes,
            "udp_datagrams_received": accounting.received,
            "udp_payload_bytes_received": accounting.received_bytes,
            "receive_timeouts": accounting.receive_timeouts,
            "socket_buffers": adapter.socket_buffers,
        })
        print(json.dumps(diagnostics, sort_keys=True), file=sys.stderr)
        return 0
    except Exception as error:
        diagnostics.update({
            "error_type": type(error).__name__,
            "error": str(error),
            "compact_statuses": compact_statuses,
            "protocol_messages_in": messages_in,
            "native_commits": commits,
        })
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
