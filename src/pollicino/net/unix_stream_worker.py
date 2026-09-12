from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .adaptive_reconciliation import AdaptiveIndependentEndpoint
from .compact_reconciliation import B2C_MAGIC, CompactIndependentEndpoint
from .endpoint import B2ContactBudget, RecordKind
from .fair_reconciliation import (
    FairIndependentEndpoint,
    ReferenceDirectoryRequestMessage,
    encode_fair_message,
)
from .fragmentation import EphemeralFragmentReassembler, fragment_message
from .process_worker import (
    ROLE_GENERIC,
    ROLE_INITIATOR,
    ROLE_RESPONDER,
    _adaptive_initial,
    _consume,
    _open,
    _selected,
)
from .unix_stream import UnixStreamAdapter, UnixStreamEOF, UnixStreamListener, UnixStreamTimeout


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pollicino-unix-stream-worker")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--listener", type=Path, required=True)
    parser.add_argument("--role", choices=("initiator", "responder"), required=True)
    parser.add_argument("--kind", choices=tuple(kind.name for kind in RecordKind), required=True)
    parser.add_argument("--mtu", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=0.25)
    parser.add_argument("--max-messages", type=int, default=100)
    parser.add_argument("--read-size", type=int)
    parser.add_argument("--write-chunk", type=int)
    parser.add_argument("--selected", action="append", default=[])
    parser.add_argument("--exact", action="store_true")
    parser.add_argument("--recover-stale", action="store_true")
    parser.add_argument("--crash-after-reassembly", action="store_true")
    parser.add_argument("--crash-after-commit", action="store_true")
    parser.add_argument("--crash-after-send-batch", type=int)
    return parser


def _send(adapter: UnixStreamAdapter, messages: tuple[bytes, ...], mtu: int) -> tuple[int, int]:
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
    catalog = query_results = adapter = listener = None
    diagnostics: dict[str, object] = {
        "role": args.role,
        "transport": "AF_UNIX/SOCK_STREAM",
        "root_scope": "LOCAL_ONLY",
        "shared_endpoint_objects": 0,
    }
    try:
        catalog, query_results = _open(args.root)
        compact = CompactIndependentEndpoint(catalog, query_results)
        fair = FairIndependentEndpoint(catalog, query_results)
        common = {
            "max_frame_bytes": args.mtu,
            "timeout": args.timeout,
            "max_read_bytes": args.read_size,
            "max_write_chunk_bytes": args.write_chunk,
            "max_frames": args.max_messages * 100,
        }
        if args.role == "responder":
            listener = UnixStreamListener(
                args.listener,
                max_frame_bytes=args.mtu,
                timeout=args.timeout,
                recover_stale=args.recover_stale,
            )
            adapter = listener.accept(
                max_read_bytes=args.read_size,
                max_write_chunk_bytes=args.write_chunk,
                max_frames=args.max_messages * 100,
            )
        else:
            adapter = UnixStreamAdapter.connect(args.listener, **common)
        reassembler = EphemeralFragmentReassembler(max_frame_bytes=args.mtu)
        selected = _selected(args.selected)
        sent_frames = sent_bytes = messages_in = commits = 0
        compact_statuses: list[str] = []
        response_batches = 0
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
                    B2ContactBudget(
                        max_bearer_attempts=args.max_messages,
                        max_trace_entries=args.max_messages,
                    ),
                )
                diagnostics["decision"] = decision
            count, octets = _send(adapter, outbound, args.mtu)
            sent_frames += count
            sent_bytes += octets
        while messages_in < args.max_messages:
            try:
                encoded_frame = adapter.receive_frame()
            except UnixStreamTimeout:
                diagnostics["ended"] = "IDLE_TIMEOUT"
                break
            except UnixStreamEOF:
                diagnostics["ended"] = "CLEAN_EOF"
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
            count, octets = _send(adapter, responses, args.mtu)
            sent_frames += count
            sent_bytes += octets
            if responses:
                response_batches += 1
                if args.crash_after_send_batch == response_batches:
                    __import__("os")._exit(95)
        accounting = adapter.accounting
        diagnostics.update({
            "process_id": __import__("os").getpid(),
            "protocol_messages_in": messages_in,
            "native_commits": commits,
            "compact_statuses": compact_statuses,
            "response_batches": response_batches,
            "b4_frames_sent": sent_frames,
            "b4_frame_bytes_sent": sent_bytes,
            "stream_frames_received": accounting.frames_received,
            "stream_frame_bytes_received": accounting.frame_bytes_received,
            "stream_bytes_written": accounting.stream_bytes_written,
            "stream_bytes_read": accounting.stream_bytes_read,
            "os_write_calls": accounting.write_calls,
            "os_read_calls": accounting.read_calls,
            "maximum_buffered_bytes": accounting.maximum_buffered_bytes,
            "maximum_buffer_bound": adapter.max_buffer_bytes,
            "socket_buffers": adapter.socket_buffers,
        })
        print(json.dumps(diagnostics, sort_keys=True), file=sys.stderr)
        return 0
    except Exception as error:
        diagnostics.update({
            "error_type": type(error).__name__,
            "error": str(error),
            "compact_statuses": locals().get("compact_statuses", []),
            "protocol_messages_in": locals().get("messages_in", 0),
            "native_commits": locals().get("commits", 0),
        })
        print(json.dumps(diagnostics, sort_keys=True), file=sys.stderr)
        return 2
    finally:
        if adapter is not None:
            adapter.close()
        if listener is not None:
            listener.close()
        if catalog is not None:
            catalog.close()
        if query_results is not None:
            query_results.close()


if __name__ == "__main__":
    raise SystemExit(main())
