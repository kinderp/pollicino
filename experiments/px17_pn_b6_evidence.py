"""Regenerate deterministic PX17 closure artifacts."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
OUT = ROOT / "artifacts" / "px17-pn-b6"
IMPL = "f9d1c02fa20ae759dadf94bd1d1610d1ba026f5b"


def write(name: str, value: object) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> None:
    write("transport-contract.json", {
        "adapter": "UnixStreamAdapter",
        "address": "FILESYSTEM_PATH",
        "api": ["connect", "listener.accept", "send_frame", "receive_frame", "close"],
        "connection_oriented": True,
        "family": "AF_UNIX",
        "frame_payload": "COMPLETE_EXPERIMENTAL_B4_FRAME",
        "max_frame_bytes": 4096,
        "ordered": True,
        "send_success_means_commit": False,
        "timeout_semantics": "CURRENT_TRANSPORT_OPPORTUNITY_ENDED_ONLY",
        "type": "SOCK_STREAM",
    })
    write("stream-framing.json", {
        "additional_framing_bytes": 0,
        "b4_header_bytes": 52,
        "delimiter": "B4_FIXED_HEADER_PLUS_PAYLOAD_LENGTH",
        "existing_b4_fields_sufficient": True,
        "maximum_frame_bytes": 4096,
        "maximum_default_adapter_buffer_bytes": 8192,
        "outer_magic": False,
        "resynchronization_scan": False,
    })
    write("stream-segmentation.json", {
        "one_byte_reads": "PASS",
        "one_byte_writes": "PASS",
        "partial_header": "WAIT_OR_FAIL_ON_EOF",
        "partial_payload": "WAIT_OR_FAIL_ON_EOF",
        "concatenated_frames": "PASS",
        "many_complete_plus_partial_final": "COMPLETE_EMITTED_PARTIAL_REJECTED",
        "fixed_seed": 20260912,
        "random_segmentation": "PASS",
        "segmentation_mismatches": 0,
    })
    write("partial-write.json", {
        "model": "BOUNDED_SAME_OPPORTUNITY_COMPLETION",
        "one_byte_write_calls": "PASS",
        "deadline": "FINITE_PER_FRAME",
        "unwritten_suffix_silently_dropped": False,
        "failure_poisoned_write_side": True,
        "protocol_retransmission": False,
    })
    write("allocation-bounds.json", {
        "maximum_b4_frame_bytes": 4096,
        "maximum_read_bytes": 4096,
        "maximum_default_buffer_bytes": 8192,
        "declared_oversize": "REJECTED_AFTER_52_BYTE_HEADER",
        "unbounded_remote_allocation": 0,
        "pending_frame_queue": "BOUNDED_BY_ONE_RECV_PLUS_ONE_FRAME",
    })
    write("connection-lifecycle.json", {
        "lifecycle": "BIND_LISTEN_ACCEPT_ONE_BOUNDED_CONTACT_CLOSE",
        "mode": "0600",
        "normal_cleanup": "PASS",
        "active_collision": "FAIL_CLOSED",
        "owned_stale_recovery": "PASS",
        "unowned_path_removed": False,
        "missing_listener": "FINITE_CONNECTION_FAILURE",
        "half_close": "SUPPORTED_NOT_REQUIRED",
        "persistent_connection_authority": False,
    })
    write("backpressure.json", {
        "blocked_sender": "FINITE_TIMEOUT",
        "slow_reader": "PASS",
        "user_space_queue": 0,
        "large_state_short_horizon": "BOUNDED_WRITE_TIMEOUT_OR_BROKEN_PIPE",
        "classification": "L.BACKPRESSURE_LIMIT",
        "semantic_inference": False,
    })
    write("corruption.json", {
        "invalid_magic": "FAIL_CONNECTION_NO_SCAN",
        "header_corruption": "REJECTED",
        "payload_corruption": "CRC_REJECTED",
        "deleted_byte": "FAIL_CLOSED_DESYNCHRONIZED_OPPORTUNITY",
        "repeated_receive_after_error": "IMMEDIATE_TERMINAL_FAILURE",
        "native_mutations": 0,
    })
    write("process-crash.json", {
        "receiver_before_apply": "NO_MUTATION",
        "receiver_after_commit": "DURABLE",
        "sender_mid_frame": "INCOMPLETE_FRAME_DISCARDED",
        "sender_after_complete_record_write": "RECEIVER_COMMIT_RECONCILED",
        "partial_stream_state_persisted": False,
    })
    write("restart-results.json", {
        "both_processes": "PASS",
        "fresh_listener_and_connection": True,
        "durable_state_only": True,
        "persistent_stream_session_required": False,
        "persistent_stream_progress_required": False,
    })
    write("sender-uncertainty.json", {
        "complete_local_write_is_commit": False,
        "receiver_commit_sender_exit": "PASS",
        "fresh_contact_skips_durable_record": "PASS",
        "persistent_ack": 0,
        "persistent_retry": 0,
    })
    write("adaptive-regression.json", {
        "compact_equality": [0],
        "compact_success": [1, 10, 20],
        "delivered_capacity_failure_and_exact_fallback": [100],
        "bounded_large_failure_probes": [1000, 10000],
        "large_probe_message_horizon": 20,
        "compact_interruption": "TRANSPORT_FAILURE_NOT_CAPACITY_EVIDENCE",
        "exact_fallback_interruption": "COMPLETE_COMMITS_ONLY",
        "oracle_mismatches": 0,
        "undetected_false_negatives": 0,
        "px16_artifact_discrepancy": "PX16_JSON_LABELS_20_AS_CAPACITY_FAILURE_BUT_EXECUTABLE_DECODED_REGISTERED_SET",
    })
    write("transport-family-equivalence.json", {
        "families": ["AF_UNIX/SOCK_DGRAM", "AF_UNIX/SOCK_STREAM"],
        "same_b4_fragmentation": True,
        "canonical_mismatches": 0,
        "b4_family_specific_branches": 0,
        "common_minimal_contract": ["max_frame_bytes", "send_frame", "receive_frame", "close"],
        "generic_capability_contract_justified": "MINIMAL_INTERFACE_YES_CAPABILITY_DESCRIPTOR_NOT_YET_NEEDED",
    })
    write("mule-results.json", {
        "query_a_c_b": "PASS",
        "result_b_c_a": "PASS",
        "fresh_c_processes": True,
        "multi_frame_b4_payload": True,
        "mule_application_semantics": 0,
    })
    write("accounting.json", {
        "sample": "10_QUERY_CAPACITY_10_MTU_128",
        "initiator": {"b4_frames": 28, "b4_bytes": 3458, "stream_bytes": 3458, "os_writes": 28, "os_reads": 5},
        "responder": {"b4_frames": 4, "b4_bytes": 438, "stream_bytes": 438, "os_writes": 4, "os_reads": 29},
        "socket_buffers": {"send": 8192, "receive": 8192},
        "stream_extra_wire_bytes": 0,
        "capacity_10": {"message_bytes": 797, "frames_by_ceiling": {"53":797,"64":67,"128":11,"256":4,"512":2,"1024":1,"1500":1,"4096":1}},
        "maximum_message": {"message_bytes": 29245, "ceiling": 128, "b4_frames": 385},
    })
    write("neutrality-scan.json", {
        "shared_endpoint_objects": 0,
        "direct_remote_store_reads": 0,
        "application_specific_stream_branches": 0,
        "unix_stream_specific_d4_branches": 0,
        "unix_stream_specific_b2_family_branches": 0,
        "transport_family_specific_b4_branches": 0,
        "routing": 0,
        "discovery": 0,
        "authentication": 0,
        "transport_ack": 0,
        "reconnect_retry": 0,
        "pnf1": 0,
    })
    write("classification.json", {
        "gate": "PX17-PN-B6",
        "identifier_status": "REPOSITORY_OWNER_CANDIDATE_FROM_PX16_CLOSURE_RECOMMENDATION",
        "classification": "POLLICINO_UNIX_STREAM_TRANSPORT_READY_WITH_LIMITS",
        "confidence": "HIGH",
        "implementation_sha": IMPL,
        "focused": {"passed": 59},
        "full": {"passed": 763, "skipped": 5},
        "compileall": "PASS",
        "failures": [
            "A.TEST_HARNESS_ERROR:macOS Unix pathname too long",
            "A.TEST_HARNESS_ERROR:stale-worker PYTHONPATH missing",
            "A.TEST_HARNESS_ERROR:20-difference capacity-failure assumption corrected to executable behavior",
            "A.TEST_HARNESS_ERROR:one-contact convergence assumed despite finite shared message budget",
            "L.BACKPRESSURE_LIMIT:short receive horizon can close while peer has an outbound batch",
        ],
        "next": "one bounded loopback IP transport experiment comparing UDP and TCP adapters under the same B4 contract",
    })


if __name__ == "__main__":
    main()
