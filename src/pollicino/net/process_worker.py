from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .adaptive_reconciliation import AdaptiveIndependentEndpoint, AdaptivePolicy
from .compact_reconciliation import (
    B2C_MAGIC,
    CompactDecodeStatus,
    CompactIndependentEndpoint,
    FingerprintRequestMessage,
    IdentityRevealMessage,
    SketchSummaryMessage,
    decode_compact_message,
)
from .endpoint import B2_MAGIC, B2ContactBudget, RecordKind
from .fair_reconciliation import (
    B2F_MAGIC,
    FairIndependentEndpoint,
    ReferenceDirectoryRequestMessage,
    encode_fair_message,
)
from .persistent_catalog import PersistentBoundedReferenceCatalog
from .persistent_query import PersistentQueryResultStore
from .process_io import read_bounded_messages


ROLE_RESPONDER = "RESPONDER"
ROLE_INITIATOR = "INITIATOR"
ROLE_GENERIC = "GENERIC"


def _kind(raw: str) -> RecordKind:
    try:
        return RecordKind[raw]
    except KeyError as error:
        raise ValueError("unknown record kind") from error


def _selected(values: Sequence[str]) -> tuple[bytes, ...]:
    return tuple(bytes.fromhex(value) for value in values)


def _write_protocol(messages: Sequence[bytes], chunk_size: int) -> tuple[int, int]:
    writes = 0
    octets = 0
    for message in messages:
        for offset in range(0, len(message), chunk_size):
            block = message[offset : offset + chunk_size]
            sys.stdout.buffer.write(block)
            sys.stdout.buffer.flush()
            writes += 1
            octets += len(block)
    return writes, octets


def _open(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    catalog = PersistentBoundedReferenceCatalog(root / "catalog")
    query_results = PersistentQueryResultStore(root / "query-result")
    return catalog, query_results


def _adaptive_initial(
    endpoint: AdaptiveIndependentEndpoint,
    kind: RecordKind,
    selected: tuple[bytes, ...],
    budget: B2ContactBudget,
) -> tuple[tuple[bytes, ...], str]:
    policy = AdaptivePolicy.selected_cost_aware()
    capacity = policy.capacities[0]
    estimate = endpoint.exact_control_upper_bound(kind, selected)
    summary_bytes = endpoint.compact_summary_bytes(kind, capacity, selected)
    remaining_attempts = budget.max_bearer_attempts
    exact_reason = None
    if summary_bytes >= estimate:
        exact_reason = "EXACT_COST_BOUND"
    elif summary_bytes > policy.max_summary_bytes:
        exact_reason = "SUMMARY_PRESSURE"
    elif summary_bytes > policy.max_compact_control_bytes:
        exact_reason = "COMPACT_BYTE_LIMIT"
    elif remaining_attempts <= policy.exact_progress_reserve_attempts + 1:
        exact_reason = "EXACT_RESERVE"
    elif summary_bytes > budget.max_control_bytes:
        exact_reason = "CONTACT_CONTROL_BUDGET"
    if exact_reason is not None:
        return endpoint.exact.directory_messages(kind), exact_reason
    return (endpoint.compact.summary_message(kind, capacity, selected),), "COMPACT_10"


def _consume(
    compact: CompactIndependentEndpoint,
    fair: FairIndependentEndpoint,
    encoded: bytes,
    *,
    role: str,
    selected: tuple[bytes, ...],
) -> tuple[tuple[bytes, ...], dict[str, object]]:
    if encoded[:4] == B2C_MAGIC:
        message = decode_compact_message(encoded)
        if isinstance(message, SketchSummaryMessage):
            if role not in (ROLE_RESPONDER, ROLE_INITIATOR):
                raise ValueError("compact summary requires an endpoint contact role")
            received = compact.receive_summary(encoded, selected)
            assert received.difference is not None
            status = received.difference.status
            if received.outbound_messages:
                outbound = received.outbound_messages
            elif role == ROLE_RESPONDER:
                # Existing B2C bytes carry equality/failure evidence back to the
                # initiator; the relay never interprets the status.
                outbound = (
                    compact.summary_message(message.kind, message.capacity, selected),
                )
            elif status in (
                CompactDecodeStatus.CAPACITY_EXCEEDED,
                CompactDecodeStatus.ROOT_MISMATCH,
            ):
                outbound = fair.directory_messages(message.kind)
            else:
                outbound = ()
            return outbound, {
                "compact_status": status.value,
                "durable_commits": received.durable_commits,
            }
        if isinstance(message, FingerprintRequestMessage):
            received = compact.receive_fingerprint_request(encoded, selected)
        elif isinstance(message, IdentityRevealMessage):
            received = compact.receive_identity_reveal(encoded)
        else:
            raise ValueError("unsupported compact message")
        return received.outbound_messages, {
            "durable_commits": received.durable_commits,
            "already_known": received.already_known,
        }
    if encoded[:4] in (B2F_MAGIC, B2_MAGIC):
        received = fair.receive_message(encoded, selected_references=selected)
        return received.outbound_messages, {
            "durable_commits": received.durable_commits,
            "already_known": received.already_known,
        }
    raise ValueError("unknown protocol envelope")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pollicino-process-worker")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--operation",
        choices=("adaptive-start", "exact-start", "reference-start", "consume"),
        required=True,
    )
    parser.add_argument("--kind", choices=tuple(kind.name for kind in RecordKind))
    parser.add_argument("--role", choices=(ROLE_RESPONDER, ROLE_INITIATOR, ROLE_GENERIC), default=ROLE_GENERIC)
    parser.add_argument("--selected", action="append", default=[])
    parser.add_argument("--read-size", type=int, default=4096)
    parser.add_argument("--write-chunk-size", type=int, default=65536)
    parser.add_argument("--max-attempts", type=int, default=100)
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--crash-after-commit", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not 1 <= args.write_chunk_size <= 65536:
        raise ValueError("write chunk size is outside bounds")
    selected = _selected(args.selected)
    catalog = query_results = None
    diagnostics: dict[str, object] = {
        "operation": args.operation,
        "root_scope": "LOCAL_ONLY",
        "protocol_stdout_only": True,
    }
    try:
        catalog, query_results = _open(args.root)
        compact = CompactIndependentEndpoint(catalog, query_results)
        fair = FairIndependentEndpoint(catalog, query_results)
        if args.operation == "adaptive-start":
            if args.kind is None:
                raise ValueError("kind is required")
            adaptive = AdaptiveIndependentEndpoint(catalog, query_results)
            outbound, decision = _adaptive_initial(
                adaptive,
                _kind(args.kind),
                selected,
                B2ContactBudget(
                    max_bearer_attempts=args.max_attempts,
                    max_trace_entries=args.max_attempts,
                ),
            )
            diagnostics["decision"] = decision
            accounting = None
        elif args.operation == "exact-start":
            if args.kind is None:
                raise ValueError("kind is required")
            outbound = fair.directory_messages(_kind(args.kind))
            accounting = None
        elif args.operation == "reference-start":
            outbound = (encode_fair_message(ReferenceDirectoryRequestMessage()),)
            accounting = None
        else:
            incoming, accounting = read_bounded_messages(
                sys.stdin.buffer, read_size=args.read_size
            )
            responses: list[bytes] = []
            commits = 0
            statuses: list[str] = []
            for encoded in incoming:
                active, local = _consume(
                    compact,
                    fair,
                    encoded,
                    role=args.role,
                    selected=selected,
                )
                responses.extend(active)
                commits += int(local.get("durable_commits", 0))
                if "compact_status" in local:
                    statuses.append(str(local["compact_status"]))
            outbound = tuple(responses)
            diagnostics["durable_commits"] = commits
            diagnostics["compact_statuses"] = statuses
            if args.crash_after_commit and commits:
                # Deterministic PX14 fault point: native persistence has already
                # committed, while no response or diagnostic can reach the peer.
                __import__("os")._exit(91)
        writes, octets = _write_protocol(outbound, args.write_chunk_size)
        diagnostics.update(
            {
                "process_id": __import__("os").getpid(),
                "protocol_messages_out": len(outbound),
                "protocol_bytes_out": octets,
                "os_write_calls": writes,
            }
        )
        if accounting is not None:
            diagnostics.update(
                {
                    "os_read_calls": accounting.read_calls,
                    "stream_chunks": accounting.stream_chunks,
                    "protocol_messages_in": accounting.complete_messages,
                    "protocol_bytes_in": accounting.encoded_bytes,
                    "maximum_buffer_bytes": accounting.maximum_buffer_bytes,
                }
            )
        if args.diagnostic:
            diagnostics["diagnostic_probe"] = "stderr-only"
        print(json.dumps(diagnostics, sort_keys=True), file=sys.stderr)
        return 0
    except Exception as error:
        diagnostics.update(
            {
                "error_type": type(error).__name__,
                "error": str(error),
            }
        )
        print(json.dumps(diagnostics, sort_keys=True), file=sys.stderr)
        return 2
    finally:
        if catalog is not None:
            catalog.close()
        if query_results is not None:
            query_results.close()


if __name__ == "__main__":
    raise SystemExit(main())
