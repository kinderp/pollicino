from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
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
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--scenario")
    parser.add_argument("--host-role", choices=("A", "B"))
    parser.add_argument("--interface")
    parser.add_argument("--interface-mtu", type=int)
    parser.add_argument("--expected-sha")
    parser.add_argument("--require-clean", action="store_true")
    return parser


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_state() -> tuple[str, bool]:
    repository = Path(__file__).resolve().parents[3]
    sha = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=repository,
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    status = subprocess.run(
        ("git", "status", "--porcelain=v1"), cwd=repository,
        check=True, capture_output=True, text=True,
    ).stdout
    return sha, not bool(status)


def _write_evidence(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


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
    if args.evidence is not None and not all(
        (args.run_id, args.scenario, args.host_role, args.interface, args.interface_mtu)
    ):
        raise SystemExit(
            "--evidence requires --run-id, --scenario, --host-role, "
            "--interface and --interface-mtu"
        )
    catalog = query_results = adapter = None
    started = _utc_now()
    diagnostics: dict[str, object] = {
        "role": args.role,
        "transport": "AF_INET/SOCK_DGRAM/NUMERIC_IPV4",
        "root_scope": "LOCAL_ONLY",
        "shared_endpoint_objects": 0,
    }
    compact_statuses: list[str] = []
    messages_in = commits = response_batches = 0
    try:
        commit_sha, worktree_clean = _git_state()
        diagnostics.update({
            "commit_sha": commit_sha,
            "worktree_clean": worktree_clean,
            "run_id": args.run_id,
            "scenario": args.scenario,
            "host_role": args.host_role,
            "interface": args.interface,
            "interface_mtu": args.interface_mtu,
            "b4_ceiling": args.mtu,
            "root": str(args.root),
            "started_at": started,
        })
        if args.expected_sha and commit_sha != args.expected_sha:
            raise RuntimeError("worker commit does not match --expected-sha")
        if args.require_clean and not worktree_clean:
            raise RuntimeError("scientific worker requires a clean worktree")
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
        print(json.dumps({
            "event": "READY",
            "commit_sha": commit_sha,
            "role": args.role,
            "host_role": args.host_role,
            "local_address": adapter.local_address,
            "peer_address": adapter.peer_address,
            "b4_ceiling": args.mtu,
            "root": str(args.root),
            "worktree_clean": worktree_clean,
        }, sort_keys=True), file=sys.stderr, flush=True)
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
                os._exit(96)
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
                os._exit(93)
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
                os._exit(94)
            count, octets, message_octets = _send(adapter, responses, args.mtu)
            sent_frames += count; sent_bytes += octets; sent_message_bytes += message_octets
            if responses:
                response_batches += 1
                if args.crash_after_send_batch == response_batches:
                    os._exit(95)
        accounting = adapter.accounting
        diagnostics.update({
            "process_id": os.getpid(),
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
            "catalog_state_digest": catalog.state_digest.hex(),
            "query_result_state_digest": query_results.state_digest.hex(),
            "catalog_records": len(catalog),
            "query_records": query_results.query_count,
            "result_records": query_results.result_count,
            "ended_at": _utc_now(),
            "exit_outcome": "SUCCESS",
        })
        if args.evidence is not None:
            _write_evidence(args.evidence, diagnostics)
        print(json.dumps(diagnostics, sort_keys=True), file=sys.stderr)
        return 0
    except Exception as error:
        diagnostics.update({
            "error_type": type(error).__name__,
            "error": str(error),
            "compact_statuses": compact_statuses,
            "protocol_messages_in": messages_in,
            "native_commits": commits,
            "ended_at": _utc_now(),
            "exit_outcome": "FAILURE",
        })
        if args.evidence is not None and not args.evidence.exists():
            _write_evidence(args.evidence, diagnostics)
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
