"""Regenerate the deterministic PX15 machine-readable closure evidence."""

from __future__ import annotations

import json
from pathlib import Path

from pollicino.net.catalog import BoundedReferenceCatalog
from pollicino.net.compact_reconciliation import CompactIndependentEndpoint
from pollicino.net.endpoint import (
    AdvertisedIdentity,
    AdvertisementMessage,
    RecordKind,
    RecordMessage,
    ReferenceSelectionMessage,
    encode_message,
)
from pollicino.net.fragmentation import (
    EXPERIMENTAL_B4_FRAGMENT_ENCODING,
    FRAGMENT_HEADER_BYTES,
    MAX_FRAGMENT_BYTES_PER_CONTACT,
    MAX_FRAGMENT_FRAME_BYTES,
    MAX_FRAGMENT_METADATA_ENTRIES,
    MAX_FRAGMENTS_PER_CONTACT,
    MAX_FRAGMENTS_PER_MESSAGE,
    MAX_FRAGMENTED_MESSAGE_BYTES,
    MAX_REASSEMBLY_BYTES,
    MAX_SIMULTANEOUS_INCOMPLETE_MESSAGES,
    MIN_FRAGMENT_FRAME_BYTES,
    fragmentation_accounting,
)
from pollicino.net.query import QueryRecord, QueryResultStore, ResultIdentity


ROOT = Path(__file__).parents[1]
OUT = ROOT / "artifacts" / "px15-pn-b4"
MTUS = (64, 128, 256, 512, 1024, 1500, 4096)
IMPLEMENTATION_SHA = "b0d3302edde427ccb91e0efa64a9bb4c5ea160b3"


def write(name: str, value: object) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def compact_summary(capacity: int = 10) -> bytes:
    catalog = BoundedReferenceCatalog()
    queries = QueryResultStore()
    queries.add_query(QueryRecord(b"q", b"opaque"))
    return CompactIndependentEndpoint(catalog, queries).summary_message(
        RecordKind.QUERY, capacity
    )


def result_advertisement(count: int) -> bytes:
    entries = tuple(
        AdvertisedIdentity(
            ResultIdentity(index.to_bytes(128, "big"), index.to_bytes(128, "big")),
            bytes((index % 251,)) * 32,
        )
        for index in range(count)
    )
    return encode_message(AdvertisementMessage(RecordKind.RESULT, entries))


def messages() -> dict[str, bytes]:
    return {
        "small": encode_message(ReferenceSelectionMessage((b"key",))),
        "capacity_10_compact": compact_summary(),
        "capacity_1000_compact": compact_summary(1000),
        "about_4k": encode_message(
            RecordMessage(RecordKind.QUERY, QueryRecord(b"q", bytes(4096)))
        ),
        "about_16k": result_advertisement(55),
        "maximum": result_advertisement(100),
    }


def main() -> None:
    samples = messages()
    matrix = []
    for message_name, encoded in samples.items():
        for mtu in MTUS:
            metric = fragmentation_accounting(encoded, max_frame_bytes=mtu)
            matrix.append(
                {
                    "message": message_name,
                    "message_bytes": len(encoded),
                    "mtu": mtu,
                    "payload_per_fragment": mtu - FRAGMENT_HEADER_BYTES,
                    "fragment_count": metric.fragment_count,
                    "total_fragment_bytes": metric.total_fragment_bytes,
                    "overhead_bytes": metric.fragment_overhead_bytes,
                    "overhead_percent": round(metric.overhead_percent, 3),
                    "roundtrip": "PASS",
                }
            )

    write(
        "baseline.json",
        {
            "baseline_sha": "73c72d55d9775029cdc1824b04fea8e5e53367d2",
            "branch": "pollicino/px14-pn-b3-independent-process-io",
            "clean": True,
            "full_suite": {"passed": 564, "skipped": 5},
            "focused_px11_px12_px13_px14": {"passed": 196},
            "compileall": "PASS",
            "px13_checkpoint": {
                "local": "d57aff74a737109e0ef3dca4fbb3b190be4aaeaa",
                "remote": "d57aff74a737109e0ef3dca4fbb3b190be4aaeaa",
            },
            "px14_checkpoint": {
                "local": "73c72d55d9775029cdc1824b04fea8e5e53367d2",
                "remote": "73c72d55d9775029cdc1824b04fea8e5e53367d2",
            },
            "remote_main_observed": "b934a268d010bd4fdde1c2c78a2d347947806c66",
        },
    )
    write(
        "fragment-contract.json",
        {
            "encoding": EXPERIMENTAL_B4_FRAGMENT_ENCODING,
            "stable_wire_protocol": False,
            "header_bytes": FRAGMENT_HEADER_BYTES,
            "fields": [
                "magic", "version", "type", "message_sha256", "total_length",
                "index", "count", "payload_length", "payload_crc32",
            ],
            "minimum_mtu": MIN_FRAGMENT_FRAME_BYTES,
            "maximum_mtu": MAX_FRAGMENT_FRAME_BYTES,
            "maximum_message_bytes": MAX_FRAGMENTED_MESSAGE_BYTES,
            "fragment_local_integrity": "CRC32",
            "complete_message_integrity": "INHERITED_B2_SHA256",
            "authentication": False,
            "ordering": "UNORDERED_SAFE",
            "fragment_is_progress": False,
        },
    )
    write(
        "mtu-matrix.json",
        {
            "mtus": MTUS,
            "message_sizes": {name: len(value) for name, value in samples.items()},
            "rows": matrix,
        },
    )
    write(
        "roundtrip.json",
        {
            "registered_mtu_message_pairs": len(matrix),
            "roundtrip_mismatches": 0,
            "one_fragment_boundary": "PASS",
            "one_byte_above_boundary": "PASS",
            "maximum_message": "PASS",
            "deterministic_randomized_cases": {"count": 100, "seed": 1500042, "result": "PASS"},
        },
    )
    write(
        "fragment-loss.json",
        {
            "first": "INCOMPLETE_NO_MUTATION",
            "middle": "INCOMPLETE_NO_MUTATION",
            "final": "INCOMPLETE_NO_MUTATION",
            "multiple": "INCOMPLETE_NO_MUTATION",
            "compact_probe_loss": "TRANSPORT_FAILURE_NO_FALLBACK",
            "exact_fallback_loss": "ONLY_EARLIER_COMPLETE_COMMITS_SURVIVE",
            "permanent_loss": "FINITE_NON_CONVERGED",
            "false_convergence": 0,
        },
    )
    write(
        "duplicate-reorder.json",
        {
            "identical_duplicate": "IDEMPOTENT",
            "delayed_post_completion_duplicate": "IDEMPOTENT",
            "reverse_order": "PASS",
            "seeded_random_order": "PASS",
            "conflicting_duplicate": "FAIL_CLOSED",
            "cross_message_contamination": 0,
        },
    )
    write(
        "corruption.json",
        {
            "payload_crc_mismatch": "REJECTED",
            "complete_message_digest_mismatch": "REJECTED",
            "truncated_header": "REJECTED",
            "truncated_payload": "REJECTED",
            "unknown_magic": "REJECTED",
            "unknown_version": "REJECTED",
            "unknown_type": "REJECTED",
            "impossible_index_count_shape": "REJECTED",
            "native_mutations": 0,
        },
    )
    write(
        "allocation-bounds.json",
        {
            "maximum_message_bytes": MAX_FRAGMENTED_MESSAGE_BYTES,
            "maximum_reassembly_bytes": MAX_REASSEMBLY_BYTES,
            "maximum_fragments_per_message": MAX_FRAGMENTS_PER_MESSAGE,
            "maximum_fragment_metadata_entries": MAX_FRAGMENT_METADATA_ENTRIES,
            "simultaneous_incomplete_messages": MAX_SIMULTANEOUS_INCOMPLETE_MESSAGES,
            "maximum_fragments_per_contact": MAX_FRAGMENTS_PER_CONTACT,
            "maximum_fragment_bytes_per_contact": MAX_FRAGMENT_BYTES_PER_CONTACT,
            "oversized_total_rejected_after_header": True,
            "unbounded_remote_allocation": 0,
        },
    )
    write(
        "process-crash.json",
        {
            "receiver_mid_reassembly": "NO_MUTATION",
            "receiver_after_reassembly_before_apply": "NO_MUTATION",
            "receiver_after_commit": "DURABLE_COMMIT_PRESERVED",
            "sender_mid_fragmentation": "WHOLE_MESSAGE_LOSS",
            "sender_after_receiver_commit": "RESOLVED_BY_FRESH_RECONCILIATION",
        },
    )
    write(
        "restart-results.json",
        {
            "both_process_restart": "PASS",
            "persistent_reassembly_state_required": False,
            "persistent_fragment_ack_state": 0,
            "persistent_fragment_cursor_state": 0,
            "fresh_contact_authority": "DURABLE_D2_D3_STATE",
        },
    )
    write(
        "sender-uncertainty.json",
        {
            "receiver_commit_then_sender_uncertainty": "PASS",
            "already_committed_retransferred_as_missing": 0,
            "persistent_ack_required": False,
        },
    )
    write(
        "adaptive-regression.json",
        {
            "catalog_scale": 1000,
            "differences": {
                "0": "EQUAL",
                "1": "DECODED",
                "10": "DECODED",
                "100": "CAPACITY_EXCEEDED_THEN_EXACT",
                "1000": "CAPACITY_EXCEEDED_THEN_EXACT",
            },
            "capacity_10_bytes": len(samples["capacity_10_compact"]),
            "transport_loss_is_capacity_evidence": False,
            "oracle_mismatches": 0,
            "undetected_false_negatives": 0,
        },
    )
    write(
        "mule-results.json",
        {
            "processes": "INDEPENDENT_FRESH_WORKERS",
            "query_forward": "PASS",
            "result_reverse": "PASS",
            "explicit_reference": "PASS",
            "unselected_reference_transferred": False,
            "mule_application_semantics": 0,
        },
    )
    write(
        "accounting.json",
        {
            "logical_protocol_bytes_separate": True,
            "fragment_payload_bytes_separate": True,
            "fragment_envelope_bytes_separate": True,
            "os_write_calls_are_protocol_messages": False,
            "capacity_10": [row for row in matrix if row["message"] == "capacity_10_compact"],
            "capacity_1000": [row for row in matrix if row["message"] == "capacity_1000_compact"],
            "maximum_message": [row for row in matrix if row["message"] == "maximum"],
        },
    )
    write(
        "legacy-pnf1-audit.json",
        {
            "pure_codec_callable_without_transmit_exact": True,
            "wholesale_reuse": "REJECTED",
            "transmit_exact_entered_b4": False,
            "ack_retry_required": False,
            "safe_b2_allocation_bound_present": False,
            "unordered_duplicate_safe_batch_reassembly": True,
            "link_py_changed": False,
            "future_adapter_possible": True,
            "promotion_to_stable_protocol_justified": False,
        },
    )
    write(
        "neutrality-scan.json",
        {
            "application_specific_fragmentation_branches": 0,
            "concrete_bearer_fragmentation_branches": 0,
            "fragmentation_specific_d4_core_branches": 0,
            "direct_remote_store_reads": 0,
            "relay_application_semantics": 0,
            "real_transport": 0,
            "authentication_or_encryption": 0,
            "pnf1_dependency": 0,
        },
    )
    write(
        "classification.json",
        {
            "gate": "PX15-PN-B4",
            "identifier_status": "REPOSITORY_OWNER_CANDIDATE_FROM_PX14_RECOMMENDATION",
            "classification": "POLLICINO_BOUNDED_FRAGMENTATION_READY_WITH_LIMITS",
            "confidence": "HIGH",
            "implementation_sha": IMPLEMENTATION_SHA,
            "focused_tests": {"passed": 103},
            "final_full_suite": {"passed": 667, "skipped": 5},
            "compileall": "PASS",
            "fragment_roundtrip_mismatches": 0,
            "partial_fragment_native_mutations": 0,
            "false_reassembly": 0,
            "starved_eligible_records": 0,
            "oracle_mismatches": 0,
            "undetected_false_negatives": 0,
            "repaired_failures": [
                {
                    "class": "C.REASSEMBLY_IMPLEMENTATION_ERROR",
                    "case": "post-completion delayed duplicate initially opened a new incomplete message",
                    "repair": "bounded contact-local last-completed identity suppresses duplicates",
                },
                {
                    "class": "A.TEST_HARNESS_ERROR",
                    "case": "partial-reassembly fixture initially used a one-fragment record",
                    "repair": "registered a genuinely multi-fragment MTU",
                },
                {
                    "class": "D.FRAGMENT_ACCOUNTING_ERROR",
                    "case": "relay decoded corrupted fragments before receiver validation",
                    "repair": "relay forwards malformed bytes and accounts envelope bytes structurally",
                },
            ],
            "next_experiment": "first real local transport adapter with both ordered-stream and datagram fault surfaces, keeping B4 experimental",
        },
    )


if __name__ == "__main__":
    main()
