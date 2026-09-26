import json

import pytest

from pollicino.net.rf import (
    RFReplayTrace,
    RFTraceSample,
    catalog_rf_paths,
    extract_rf_trace,
    normalize_rf_evidence,
)


def test_hw006_checkpoint_preserves_ambiguous_timeout_boundary() -> None:
    record = {
        "schema": "pollicino-hw006-checkpoint-v1",
        "executed": True,
        "checkpoint": "one-wall",
        "environment": "indoor",
        "frame_bytes": 42,
        "local_measurement_info": "INFO lab=hw-006 power_dbm=2",
        "plan": {"toa_us_per_frame": 88000},
        "attempts": [
            {
                "sequence": 1,
                "measurement": {
                    "success": True,
                    "local_rssi_dbm": -70.0,
                    "remote_rssi_dbm": -68.0,
                    "local_snr_db": 8.0,
                    "remote_snr_db": 7.5,
                    "rtt_us": 181000,
                },
                "failure_class": "success",
            },
            {
                "sequence": 2,
                "measurement": {"success": False, "error": "timeout"},
                "failure_class": "timeout_ambiguous_untethered",
            },
        ],
        "summary": {
            "attempts": 2,
            "successes": 1,
            "local_rssi_dbm_mean": -70.0,
            "remote_rssi_dbm_mean": -68.0,
            "local_snr_db_mean": 8.0,
            "remote_snr_db_mean": 7.5,
            "rtt_us_mean": 181000,
        },
    }

    evidence = normalize_rf_evidence(record, source="checkpoint.json")
    trace = extract_rf_trace(record, source="checkpoint.json")

    assert evidence is not None
    assert evidence.lab == "HW-006"
    assert evidence.tx_power_dbm == 2.0
    assert evidence.attempts == 2
    assert evidence.success_rate == 0.5

    assert trace is not None
    assert trace.successes == 1
    assert trace.failures == 1
    assert trace.failure_classes == {"timeout_ambiguous_untethered": 1}
    assert trace.samples[1].remote_rssi_dbm is None


def test_hw002_raw_benchmark_becomes_replay_trace() -> None:
    record = {
        "schema": "pollicino-hw002-benchmark-v1",
        "environment": "same-bench-indoor",
        "port": "COM3",
        "samples": [
            {
                "sequence": 1,
                "bytes": 42,
                "success": True,
                "local_rssi_dbm": -39.0,
                "remote_rssi_dbm": -38.0,
                "local_snr_db": 10.25,
                "remote_snr_db": 10.25,
                "rtt_us": 181318,
                "toa_us": 88000,
            },
            {
                "sequence": 2,
                "bytes": 42,
                "success": True,
                "local_rssi_dbm": -40.0,
                "remote_rssi_dbm": -38.0,
                "local_snr_db": 9.5,
                "remote_snr_db": 9.75,
                "rtt_us": 181164,
                "toa_us": 88000,
            },
        ],
        "summary": {
            "attempts": 2,
            "successes": 2,
            "failures": 0,
            "local_rssi_dbm": {"mean": -39.5},
            "remote_rssi_dbm": {"mean": -38.0},
            "local_snr_db": {"mean": 9.875},
            "remote_snr_db": {"mean": 10.0},
            "rtt_us": {"mean": 181241},
        },
    }

    evidence = normalize_rf_evidence(record)
    trace = extract_rf_trace(record)

    assert evidence is not None
    assert evidence.lab == "HW-002"
    assert evidence.direction == "COM3"
    assert evidence.frame_bytes == 42
    assert evidence.success_rate == 1.0
    assert trace is not None
    assert tuple(sample.sequence for sample in trace.samples) == (1, 2)


def test_replay_refuses_to_invent_more_physical_samples() -> None:
    trace = RFReplayTrace(
        source="physical.json",
        lab="HW-006",
        schema="pollicino-hw006-checkpoint-v1",
        checkpoint="one-wall",
        environment="indoor",
        samples=(
            RFTraceSample(sequence=1, success=True, failure_class=None),
            RFTraceSample(
                sequence=2,
                success=False,
                failure_class="timeout_ambiguous_untethered",
            ),
        ),
    )

    with pytest.raises(ValueError, match="contains only 2"):
        trace.replay(3)

    replay = trace.replay(5, repeat=True)
    assert [sample.success for sample in replay] == [True, False, True, False, True]


def test_hw004_and_hw005_summaries_normalize_without_double_count_facets() -> None:
    hw004 = {
        "schema": "pollicino-hw004-physical-summary-v1",
        "environment": "same-bench-indoor-hw004-crc-matrix",
        "phy": {"tx_power_dbm": 10},
        "design": {"sizes_bytes": [16, 32, 42, 60, 120, 240]},
        "overall": {
            "attempts": 48,
            "successes": 48,
            "failures": 0,
            "crc_events": 0,
            "irq_to_handle_us": {"mean": 16.3125},
        },
        "by_direction": {"COM3_to_COM4": {"attempts": 24}},
        "by_frame_bytes": {"42": {"attempts": 8}},
    }
    hw005 = {
        "schema": "pollicino-hw005-physical-summary-v1",
        "environment": "same-bench-indoor-hw005-power-staircase",
        "frame_bytes": 42,
        "powers_dbm": [10, 8, 6, 4, 2],
        "attempts": 20,
        "successes": 20,
        "failures": 0,
        "irq_to_handle_us": {"mean": 24.2},
        "by_power_dbm": {"10": {"attempts": 4}, "2": {"attempts": 4}},
    }

    first = normalize_rf_evidence(hw004)
    second = normalize_rf_evidence(hw005)

    assert first is not None and first.attempts == 48 and first.crc_events == 0
    assert second is not None and second.attempts == 20
    assert second.tx_power_dbm is None


def test_catalog_reports_coverage_but_does_not_sum_overlapping_records(tmp_path) -> None:
    raw = {
        "schema": "pollicino-hw002-benchmark-v1",
        "environment": "same-bench-indoor",
        "port": "COM3",
        "samples": [{"sequence": 1, "bytes": 42, "success": True, "toa_us": 88000}],
        "summary": {"attempts": 1, "successes": 1, "failures": 0},
    }
    staircase = {
        "schema": "pollicino-hw005-physical-summary-v1",
        "environment": "same-bench-indoor-hw005-power-staircase",
        "frame_bytes": 42,
        "powers_dbm": [10, 8, 6, 4, 2],
        "attempts": 20,
        "successes": 20,
        "failures": 0,
    }
    unrelated = {"hello": "world"}

    (tmp_path / "raw.json").write_text(json.dumps(raw), encoding="utf-8")
    (tmp_path / "staircase.json").write_text(json.dumps(staircase), encoding="utf-8")
    (tmp_path / "other.json").write_text(json.dumps(unrelated), encoding="utf-8")

    catalog = catalog_rf_paths([tmp_path])

    assert catalog["files_seen"] == 3
    assert catalog["evidence_records"] == 2
    assert catalog["replay_traces"] == 1
    assert catalog["coverage"]["labs"] == ["HW-002", "HW-005"]
    assert catalog["coverage"]["frame_bytes"] == [42]
    assert catalog["coverage"]["tx_power_dbm"] == [2.0, 4.0, 6.0, 8.0, 10.0]
    assert len(catalog["ignored_files"]) == 1
    assert "Attempts are not summed" in catalog["scientific_boundary"]
