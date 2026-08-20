#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import time
from typing import Any

import hw002

BOOT_POWER_DBM = 2
POWER_MIN_DBM = 2
POWER_MAX_DBM = 10
UNTETHERED_PROFILE_VERSION = 1


def info_fields(info_line: str) -> dict[str, str]:
    return hw002.parse_key_value_line(info_line, "INFO")


def require_power_node(info_line: str, role: str) -> dict[str, str]:
    fields = info_fields(info_line)
    if fields.get("lab") not in {"hw-005", "hw-006"}:
        raise RuntimeError(f"{role} is not HW-005/HW-006: {info_line}")
    if fields.get("event_driven_rx") != "1":
        raise RuntimeError(f"{role} does not advertise event_driven_rx=1")
    if fields.get("power_control") != "1":
        raise RuntimeError(f"{role} does not advertise power_control=1")
    if fields.get("power_path") != "pa_boost":
        raise RuntimeError(f"{role} does not advertise PA_BOOST")
    if int(fields.get("power_min_dbm", "999")) != POWER_MIN_DBM:
        raise RuntimeError(f"{role} power minimum mismatch: {info_line}")
    if int(fields.get("power_max_dbm", "-999")) != POWER_MAX_DBM:
        raise RuntimeError(f"{role} power maximum mismatch: {info_line}")
    return fields


def require_hw006_remote(info_line: str, role: str = "remote") -> dict[str, str]:
    fields = require_power_node(info_line, role)
    if fields.get("lab") != "hw-006":
        raise RuntimeError(f"{role} firmware is not HW-006: {info_line}")
    if fields.get("untethered_responder") != "1":
        raise RuntimeError(f"{role} does not advertise untethered_responder=1")
    if int(fields.get("untethered_profile_version", "0")) != UNTETHERED_PROFILE_VERSION:
        raise RuntimeError(f"{role} untethered profile version mismatch: {info_line}")
    if int(fields.get("boot_power_dbm", "999")) != BOOT_POWER_DBM:
        raise RuntimeError(f"{role} boot power is not {BOOT_POWER_DBM} dBm: {info_line}")
    if int(fields.get("power_dbm", "999")) != BOOT_POWER_DBM:
        raise RuntimeError(
            f"{role} current power is not boot baseline {BOOT_POWER_DBM} dBm: {info_line}"
        )
    return fields


def set_power(port, power_dbm: int) -> str:
    if not POWER_MIN_DBM <= power_dbm <= POWER_MAX_DBM:
        raise ValueError(f"power must be in {POWER_MIN_DBM}..{POWER_MAX_DBM} dBm")
    hw002.write_line(port, f"POWER {power_dbm}")
    line = hw002.wait_prefix(port, "POWEROK ", 3.0)
    fields = hw002.parse_key_value_line(line, "POWEROK")
    if int(fields.get("dbm", "999")) != power_dbm:
        raise RuntimeError(f"POWER confirmation mismatch: {line}")
    info = hw002.query_info(port)
    applied = require_power_node(info, "node after POWER")
    if int(applied.get("power_dbm", "999")) != power_dbm:
        raise RuntimeError(f"INFO power mismatch after POWER {power_dbm}: {info}")
    return info


def compare_phy(local: dict[str, str], remote: dict[str, str]) -> None:
    for key in ("freq_mhz", "bw_khz", "sf", "cr", "max_tx"):
        if local.get(key) != remote.get(key):
            raise RuntimeError(
                f"fixed-PHY mismatch for {key}: local={local.get(key)} remote={remote.get(key)}"
            )


def classify(measurement: dict[str, Any]) -> str:
    if measurement.get("success"):
        return "success"
    if measurement.get("error") == "timeout":
        return "timeout_ambiguous_untethered"
    return str(measurement.get("error", "other_failure"))


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def summarize(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [a for a in attempts if a["measurement"].get("success")]
    classes = sorted({a["failure_class"] for a in attempts})
    return {
        "attempts": len(attempts),
        "successes": len(successful),
        "failure_classes": {
            name: sum(1 for a in attempts if a["failure_class"] == name)
            for name in classes
        },
        "successful_remote_telemetry_count": len(successful),
        "remote_rssi_dbm_mean": _mean(
            [float(a["measurement"]["remote_rssi_dbm"]) for a in successful]
        ),
        "remote_snr_db_mean": _mean(
            [float(a["measurement"]["remote_snr_db"]) for a in successful]
        ),
        "local_rssi_dbm_mean": _mean(
            [float(a["measurement"]["local_rssi_dbm"]) for a in successful]
        ),
        "local_snr_db_mean": _mean(
            [float(a["measurement"]["local_snr_db"]) for a in successful]
        ),
        "rtt_us_mean": _mean(
            [float(a["measurement"]["rtt_us"]) for a in successful]
        ),
    }


def make_plan(toa_us: int, count: int, occupancy_percent: float | None) -> dict[str, Any]:
    estimated_wall_s = None
    if occupancy_percent is not None:
        if not 0.0 < occupancy_percent <= 100.0:
            raise ValueError("tx occupancy cap must be in (0,100]")
        fraction = occupancy_percent / 100.0
        interval_s = (toa_us / 1_000_000.0) / fraction
        estimated_wall_s = interval_s * max(count - 1, 0) + 2 * toa_us / 1_000_000.0
    return {
        "frame_count": count,
        "toa_us_per_frame": toa_us,
        "planned_local_tx_airtime_us": toa_us * count,
        "planned_remote_tx_airtime_upper_bound_us": toa_us * count,
        "tx_occupancy_cap_percent": occupancy_percent,
        "estimated_minimum_wall_seconds_for_requested_cap": estimated_wall_s,
    }


def run_preflight(local_name: str, remote_name: str, frame_bytes: int) -> dict[str, Any]:
    if local_name == remote_name:
        raise ValueError("local and remote ports must differ")
    local = hw002.open_port(local_name)
    try:
        remote = hw002.open_port(remote_name)
    except Exception:
        local.close()
        raise
    try:
        local_info_initial = hw002.query_info(local)
        local_fields_initial = require_power_node(local_info_initial, "local")
        remote_info = hw002.query_info(remote)
        remote_fields = require_hw006_remote(remote_info, "remote")
        compare_phy(local_fields_initial, remote_fields)

        local_info_2dbm = set_power(local, BOOT_POWER_DBM)
        local_fields_2dbm = require_power_node(local_info_2dbm, "local at 2 dBm")
        compare_phy(local_fields_2dbm, remote_fields)

        local_toa = hw002.query_toa(local, frame_bytes)
        remote_toa = hw002.query_toa(remote, frame_bytes)
        if local_toa != remote_toa:
            raise RuntimeError(f"TOA mismatch: local={local_toa} remote={remote_toa}")

        return {
            "schema": "pollicino-hw006-preflight-v1",
            "local_port": local_name,
            "remote_port": remote_name,
            "local_initial_info": local_info_initial,
            "local_2dbm_info": local_info_2dbm,
            "remote_info": remote_info,
            "frame_bytes": frame_bytes,
            "toa_us": local_toa,
            "ready_for_untethered": True,
            "instruction": (
                "After this preflight the remote HW-006 node may be disconnected from USB "
                "and powered from a suitable USB power bank. It will boot at 2 dBm and "
                "enter event-driven receive automatically."
            ),
        }
    finally:
        try:
            set_power(local, 10)
        except Exception:
            pass
        remote.close()
        local.close()


def run_checkpoint(
    local_name: str,
    frame_bytes: int,
    count: int,
    timeout_ms: int,
    execute: bool,
    airtime_budget_ms: float | None,
    occupancy_percent: float | None,
    checkpoint: str,
    environment: str | None,
    distance_m: float | None,
) -> dict[str, Any]:
    if not 16 <= frame_bytes <= 240:
        raise ValueError("frame bytes must be in 16..240")
    if count < 1:
        raise ValueError("count must be >= 1")

    local = hw002.open_port(local_name)
    try:
        initial_info = hw002.query_info(local)
        require_power_node(initial_info, "local")
        local_2dbm_info = set_power(local, BOOT_POWER_DBM)
        toa_us = hw002.query_toa(local, frame_bytes)
        plan = make_plan(toa_us, count, occupancy_percent)

        base = {
            "schema": "pollicino-hw006-checkpoint-v1",
            "checkpoint": checkpoint,
            "environment": environment,
            "distance_m": distance_m,
            "local_port": local_name,
            "local_initial_info": initial_info,
            "local_measurement_info": local_2dbm_info,
            "remote_expected_profile": {
                "lab": "hw-006",
                "boot_power_dbm": BOOT_POWER_DBM,
                "untethered_responder": 1,
                "serial_observed_during_checkpoint": False,
            },
            "frame_bytes": frame_bytes,
            "plan": plan,
            "semantics": {
                "remote_observability": (
                    "The remote responder serial port is intentionally unavailable during "
                    "the checkpoint. Remote RSSI/SNR are available only when a valid PONG "
                    "returns them in the frozen H2 frame."
                ),
                "failure_boundary": (
                    "A timeout is ambiguous in untethered mode: it cannot by itself separate "
                    "remote CRC/decode failure, missed return PONG, remote reset/power-bank "
                    "shutdown, or other RF failure."
                ),
                "reliability_boundary": (
                    "Checkpoint success fractions are descriptive observations for the named "
                    "geometry, not deployment packet-loss probabilities."
                ),
                "energy_boundary": "No electrical energy measurement is made.",
            },
        }
        if not execute:
            return {**base, "executed": False}

        if airtime_budget_ms is None or airtime_budget_ms <= 0:
            raise ValueError("positive --airtime-budget-ms is required with --execute")
        if occupancy_percent is None:
            raise ValueError("--tx-occupancy-cap-percent is required with --execute")
        planned_ms = plan["planned_local_tx_airtime_us"] / 1000.0
        if planned_ms > airtime_budget_ms:
            raise ValueError(
                f"planned local TX airtime {planned_ms:.3f} ms exceeds explicit budget "
                f"{airtime_budget_ms:.3f} ms"
            )

        interval_s = (toa_us / 1_000_000.0) / (occupancy_percent / 100.0)
        attempts: list[dict[str, Any]] = []
        previous_start: float | None = None
        started = time.monotonic()
        for index in range(count):
            if previous_start is not None:
                due = previous_start + interval_s
                remaining = due - time.monotonic()
                if remaining > 0:
                    time.sleep(remaining)
            previous_start = time.monotonic()
            measurement = hw002.measure_once(
                local,
                index + 1,
                frame_bytes,
                timeout_ms,
            )
            attempts.append(
                {
                    "sequence": index + 1,
                    "host_elapsed_s": time.monotonic() - started,
                    "measurement": measurement,
                    "failure_class": classify(measurement),
                }
            )

        summary = summarize(attempts)
        summary["remote_confirmed_pong_tx_airtime_lower_bound_us"] = (
            toa_us * summary["successes"]
        )
        return {
            **base,
            "executed": True,
            "elapsed_s": time.monotonic() - started,
            "attempts": attempts,
            "summary": summary,
        }
    finally:
        try:
            set_power(local, 10)
        except Exception:
            pass
        local.close()


def selftest() -> dict[str, bool]:
    remote_line = (
        "INFO board=lilygo-lora32-v1.6.1 chip=sx1276 freq_mhz=868.100 "
        "bw_khz=125.0 sf=7 cr=4/5 power_dbm=2 max_tx=240 lab=hw-006 "
        "event_driven_rx=1 power_control=1 power_min_dbm=2 power_max_dbm=10 "
        "power_path=pa_boost boot_power_dbm=2 untethered_responder=1 "
        "untethered_profile_version=1"
    )
    remote_ok = require_hw006_remote(remote_line)["lab"] == "hw-006"
    timeout_ok = classify({"success": False, "error": "timeout"}) == (
        "timeout_ambiguous_untethered"
    )
    plan = make_plan(88000, 10, 1.0)
    plan_ok = (
        plan["planned_local_tx_airtime_us"] == 880000
        and abs(plan["estimated_minimum_wall_seconds_for_requested_cap"] - 79.376) < 1e-6
    )
    return {
        "untethered_profile_parser": remote_ok,
        "timeout_classification": timeout_ok,
        "checkpoint_plan": plan_ok,
        "success": remote_ok and timeout_ok and plan_ok,
    }


def emit(result: dict[str, Any], output: str | None) -> None:
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Pollicino HW-006 untethered responder lab")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("selftest")

    pre = sub.add_parser("preflight", help="verify tethered HW-005 local + HW-006 remote")
    pre.add_argument("--local-port", required=True)
    pre.add_argument("--remote-port", required=True)
    pre.add_argument("--bytes", type=int, default=42)
    pre.add_argument("--output")

    checkpoint = sub.add_parser("checkpoint", help="measure with only the local serial port")
    checkpoint.add_argument("--local-port", required=True)
    checkpoint.add_argument("--bytes", type=int, default=42)
    checkpoint.add_argument("--count", type=int, default=10)
    checkpoint.add_argument("--timeout-ms", type=int, default=3000)
    checkpoint.add_argument("--execute", action="store_true")
    checkpoint.add_argument("--airtime-budget-ms", type=float)
    checkpoint.add_argument("--tx-occupancy-cap-percent", type=float)
    checkpoint.add_argument("--checkpoint", required=True)
    checkpoint.add_argument("--environment")
    checkpoint.add_argument("--distance-m", type=float)
    checkpoint.add_argument("--output")

    args = parser.parse_args()
    if args.command == "selftest":
        result = selftest()
        emit(result, None)
        return 0 if result["success"] else 1
    if args.command == "preflight":
        emit(run_preflight(args.local_port, args.remote_port, args.bytes), args.output)
        return 0
    if args.command == "checkpoint":
        emit(
            run_checkpoint(
                args.local_port,
                args.bytes,
                args.count,
                args.timeout_ms,
                args.execute,
                args.airtime_budget_ms,
                args.tx_occupancy_cap_percent,
                args.checkpoint,
                args.environment,
                args.distance_m,
            ),
            args.output,
        )
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
