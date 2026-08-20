#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
import time
from typing import Any

import hw002
import hw003

DEFAULT_POWERS = (10, 8, 6, 4, 2)
POWER_MIN_DBM = 2
POWER_MAX_DBM = 10
POWER_CONTROL_VERSION = 1


def parse_powers(text: str) -> tuple[int, ...]:
    values: list[int] = []
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        value = int(item)
        if not POWER_MIN_DBM <= value <= POWER_MAX_DBM:
            raise ValueError(
                f"power {value} dBm outside controlled PA_BOOST range "
                f"{POWER_MIN_DBM}..{POWER_MAX_DBM} dBm"
            )
        if value not in values:
            values.append(value)
    if not values:
        raise ValueError("at least one power level is required")
    return tuple(values)


def require_hw005_capability(info_line: str, role: str) -> dict[str, str]:
    fields = hw002.parse_key_value_line(info_line, "INFO")
    if fields.get("lab") != "hw-005":
        raise RuntimeError(f"{role} firmware is not HW-005: {info_line}")
    if fields.get("event_driven_rx") != "1":
        raise RuntimeError(f"{role} does not advertise event_driven_rx=1")
    if fields.get("scheduler_trace") != "1":
        raise RuntimeError(f"{role} does not advertise scheduler_trace=1")
    if fields.get("power_control") != "1":
        raise RuntimeError(f"{role} does not advertise power_control=1")
    if int(fields.get("power_control_version", "0")) != POWER_CONTROL_VERSION:
        raise RuntimeError(f"{role} power-control version mismatch: {info_line}")
    if int(fields.get("power_min_dbm", "999")) != POWER_MIN_DBM:
        raise RuntimeError(f"{role} power minimum mismatch: {info_line}")
    if int(fields.get("power_max_dbm", "-999")) != POWER_MAX_DBM:
        raise RuntimeError(f"{role} power maximum mismatch: {info_line}")
    if fields.get("power_path") != "pa_boost":
        raise RuntimeError(f"{role} does not confirm PA_BOOST path: {info_line}")
    return fields


def set_power(port, power_dbm: int, timeout_s: float = 3.0) -> str:
    hw002.write_line(port, f"POWER {power_dbm}")
    line = hw002.wait_prefix(port, "POWEROK ", timeout_s)
    fields = hw002.parse_key_value_line(line, "POWEROK")
    applied = int(fields["dbm"])
    if applied != power_dbm:
        raise RuntimeError(
            f"POWER confirmation mismatch: requested {power_dbm}, got {applied}"
        )
    info = hw002.query_info(port)
    info_fields = require_hw005_capability(info, f"node after POWER {power_dbm}")
    if int(info_fields["power_dbm"]) != power_dbm:
        raise RuntimeError(
            f"INFO power mismatch after POWER {power_dbm}: {info}"
        )
    return info


def build_schedule(powers: tuple[int, ...]) -> list[dict[str, Any]]:
    schedule: list[dict[str, Any]] = []
    sequence = 1
    patterns = (
        ("descending", powers, ("a_to_b", "b_to_a")),
        ("ascending", tuple(reversed(powers)), ("b_to_a", "a_to_b")),
    )
    for round_number, (power_order, round_powers, directions) in enumerate(patterns, 1):
        for power in round_powers:
            for direction in directions:
                schedule.append(
                    {
                        "sequence": sequence,
                        "round": round_number,
                        "power_order": power_order,
                        "power_dbm": power,
                        "direction": direction,
                    }
                )
                sequence += 1
    return schedule


def classify(sample: dict[str, Any]) -> str:
    measurement = sample["measurement"]
    if measurement.get("success"):
        return "success"
    tail = sample.get("responder_serial_tail") or []
    if any(line == "RXERR crc" for line in tail):
        return "responder_crc"
    if measurement.get("error") == "timeout":
        return "timeout_without_responder_crc"
    return str(measurement.get("error", "other_failure"))


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def summarize(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    by_power: dict[str, Any] = {}
    for power in sorted({int(a["power_dbm"]) for a in attempts}, reverse=True):
        subset = [a for a in attempts if int(a["power_dbm"]) == power]
        successes = [a for a in subset if a["measurement"].get("success")]
        by_direction: dict[str, Any] = {}
        for direction in ("a_to_b", "b_to_a"):
            ds = [a for a in subset if a["direction"] == direction]
            ok = [a for a in ds if a["measurement"].get("success")]
            by_direction[direction] = {
                "attempts": len(ds),
                "successes": len(ok),
                "failure_classes": {
                    name: sum(1 for a in ds if a["failure_class"] == name)
                    for name in sorted({a["failure_class"] for a in ds})
                },
                "remote_rssi_dbm_mean": _mean(
                    [float(a["measurement"]["remote_rssi_dbm"]) for a in ok]
                ),
                "local_rssi_dbm_mean": _mean(
                    [float(a["measurement"]["local_rssi_dbm"]) for a in ok]
                ),
                "remote_snr_db_mean": _mean(
                    [float(a["measurement"]["remote_snr_db"]) for a in ok]
                ),
                "local_snr_db_mean": _mean(
                    [float(a["measurement"]["local_snr_db"]) for a in ok]
                ),
                "irq_to_handle_us_mean": _mean(
                    [
                        float(a["responder_trace"]["irq_to_handle_us"])
                        for a in ok
                        if a.get("responder_trace") is not None
                    ]
                ),
            }
        by_power[str(power)] = {
            "attempts": len(subset),
            "successes": len(successes),
            "failure_classes": {
                name: sum(1 for a in subset if a["failure_class"] == name)
                for name in sorted({a["failure_class"] for a in subset})
            },
            "remote_rssi_dbm_mean": _mean(
                [float(a["measurement"]["remote_rssi_dbm"]) for a in successes]
            ),
            "local_rssi_dbm_mean": _mean(
                [float(a["measurement"]["local_rssi_dbm"]) for a in successes]
            ),
            "by_direction": by_direction,
        }

    return {
        "attempts": len(attempts),
        "successes": sum(1 for a in attempts if a["measurement"].get("success")),
        "failure_classes": {
            name: sum(1 for a in attempts if a["failure_class"] == name)
            for name in sorted({a["failure_class"] for a in attempts})
        },
        "by_power_dbm": by_power,
    }


def run_staircase(
    port_a_name: str,
    port_b_name: str,
    powers: tuple[int, ...],
    frame_bytes: int,
    timeout_ms: int,
    execute: bool,
    airtime_budget_ms: float | None,
    tx_occupancy_cap_percent: float | None,
    environment: str | None,
) -> dict[str, Any]:
    if port_a_name == port_b_name:
        raise ValueError("port A and port B must be different")
    if not 16 <= frame_bytes <= 240:
        raise ValueError("frame bytes must be in 16..240")

    schedule = build_schedule(powers)
    port_a = hw002.open_port(port_a_name)
    try:
        port_b = hw002.open_port(port_b_name)
    except Exception:
        port_a.close()
        raise

    try:
        info_a = hw002.query_info(port_a)
        info_b = hw002.query_info(port_b)
        fields_a = require_hw005_capability(info_a, "port A")
        fields_b = require_hw005_capability(info_b, "port B")
        if int(fields_a["power_dbm"]) != 10 or int(fields_b["power_dbm"]) != 10:
            raise RuntimeError("HW-005 staircase requires both nodes to start at 10 dBm")

        toa_a = hw002.query_toa(port_a, frame_bytes)
        toa_b = hw002.query_toa(port_b, frame_bytes)
        if toa_a != toa_b:
            raise RuntimeError(f"TOA mismatch between nodes: A={toa_a}, B={toa_b}")

        planned_airtime_us = toa_a * len(schedule)
        fraction = None
        estimated_wall_s = None
        if tx_occupancy_cap_percent is not None:
            if not 0.0 < tx_occupancy_cap_percent <= 100.0:
                raise ValueError("tx occupancy cap must be in (0,100]")
            fraction = tx_occupancy_cap_percent / 100.0
            start_interval_s = (toa_a / 1_000_000.0) / fraction
            if schedule:
                estimated_wall_s = start_interval_s * (len(schedule) - 1) + 2 * toa_a / 1_000_000.0

        plan = {
            "schema": "pollicino-hw005-plan-v1",
            "frame_bytes": frame_bytes,
            "powers_dbm": list(powers),
            "power_path": "pa_boost",
            "schedule": schedule,
            "transactions": len(schedule),
            "toa_us_per_frame": toa_a,
            "planned_per_node_tx_airtime_us": planned_airtime_us,
            "tx_occupancy_cap_percent": tx_occupancy_cap_percent,
            "estimated_minimum_wall_seconds_for_requested_cap": estimated_wall_s,
            "scientific_note": (
                "This is a controlled TX-power staircase at fixed PHY and geometry. "
                "It validates power-control response and link-margin trend; it is not "
                "a deployment packet-loss estimate."
            ),
        }
        if not execute:
            return {
                "schema": "pollicino-hw005-staircase-v1",
                "executed": False,
                "port_a": port_a_name,
                "port_b": port_b_name,
                "port_a_info": info_a,
                "port_b_info": info_b,
                "plan": plan,
            }

        if airtime_budget_ms is None or airtime_budget_ms <= 0:
            raise ValueError("positive --airtime-budget-ms is required with --execute")
        if tx_occupancy_cap_percent is None or fraction is None:
            raise ValueError("--tx-occupancy-cap-percent is required with --execute")
        planned_ms = planned_airtime_us / 1000.0
        if planned_ms > airtime_budget_ms:
            raise ValueError(
                f"planned per-node TX airtime {planned_ms:.3f} ms exceeds budget "
                f"{airtime_budget_ms:.3f} ms"
            )

        minimum_interval_s = (toa_a / 1_000_000.0) / fraction
        attempts: list[dict[str, Any]] = []
        previous_start: float | None = None
        current_power: int | None = None
        run_started = time.monotonic()

        for step in schedule:
            power = int(step["power_dbm"])
            if power != current_power:
                info_after_a = set_power(port_a, power)
                info_after_b = set_power(port_b, power)
                current_power = power
                time.sleep(0.05)
            else:
                info_after_a = hw002.query_info(port_a)
                info_after_b = hw002.query_info(port_b)

            if previous_start is not None:
                due = previous_start + minimum_interval_s
                remaining = due - time.monotonic()
                if remaining > 0:
                    time.sleep(remaining)
            previous_start = time.monotonic()

            if step["direction"] == "a_to_b":
                initiator, responder = port_a, port_b
                initiator_name, responder_name = port_a_name, port_b_name
            else:
                initiator, responder = port_b, port_a
                initiator_name, responder_name = port_b_name, port_a_name

            sample = hw003.measure_with_trace(
                initiator,
                responder,
                int(step["sequence"]),
                frame_bytes,
                timeout_ms,
            )
            attempt = {
                **step,
                "initiator_port": initiator_name,
                "responder_port": responder_name,
                "host_elapsed_s": time.monotonic() - run_started,
                "power_info_a": info_after_a,
                "power_info_b": info_after_b,
                **sample,
            }
            attempt["failure_class"] = classify(attempt)
            attempts.append(attempt)

        return {
            "schema": "pollicino-hw005-staircase-v1",
            "executed": True,
            "environment": environment,
            "elapsed_s": time.monotonic() - run_started,
            "port_a": port_a_name,
            "port_b": port_b_name,
            "initial_info_a": info_a,
            "initial_info_b": info_b,
            "plan": plan,
            "attempts": attempts,
            "summary": summarize(attempts),
            "semantics": {
                "power_control": (
                    "Both nodes are set to the same requested PA_BOOST TX power before "
                    "each power-level pair. INFO confirmation is fail-closed."
                ),
                "rssi_boundary": (
                    "RSSI/SNR are receiver observations for successfully decoded frames; "
                    "they are not direct calibrated measurements of conducted TX power."
                ),
                "reliability_boundary": (
                    "Success fractions are descriptive same-bench observations, not "
                    "deployment packet-loss probabilities."
                ),
            },
        }
    finally:
        # Restore the frozen 10 dBm baseline on best effort before closing ports.
        for port in (port_a, port_b):
            try:
                set_power(port, 10)
            except Exception:
                pass
        port_b.close()
        port_a.close()


def selftest() -> dict[str, bool]:
    schedule = build_schedule(DEFAULT_POWERS)
    schedule_ok = (
        len(schedule) == 20
        and schedule[0]["power_dbm"] == 10
        and schedule[0]["direction"] == "a_to_b"
        and schedule[1]["direction"] == "b_to_a"
        and schedule[10]["power_dbm"] == 2
        and schedule[10]["direction"] == "b_to_a"
        and schedule[-1]["power_dbm"] == 10
        and schedule[-1]["direction"] == "a_to_b"
    )
    parse_ok = parse_powers("10,8,6,4,2") == DEFAULT_POWERS
    classification_ok = classify(
        {
            "measurement": {"success": False, "error": "timeout"},
            "responder_serial_tail": ["RXERR crc"],
        }
    ) == "responder_crc"
    return {
        "power_parser": parse_ok,
        "counterbalanced_staircase": schedule_ok,
        "failure_classification": classification_ok,
        "success": parse_ok and schedule_ok and classification_ok,
    }


def write_result(result: dict[str, Any], output: str | None) -> None:
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pollicino HW-005 TX-power staircase")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("selftest")
    stair = sub.add_parser("staircase")
    stair.add_argument("--port-a", required=True)
    stair.add_argument("--port-b", required=True)
    stair.add_argument("--powers", default="10,8,6,4,2")
    stair.add_argument("--bytes", type=int, default=42)
    stair.add_argument("--timeout-ms", type=int, default=3000)
    stair.add_argument("--execute", action="store_true")
    stair.add_argument("--airtime-budget-ms", type=float)
    stair.add_argument("--tx-occupancy-cap-percent", type=float)
    stair.add_argument("--environment")
    stair.add_argument("--output")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "selftest":
        write_result(selftest(), None)
        return
    result = run_staircase(
        args.port_a,
        args.port_b,
        parse_powers(args.powers),
        args.bytes,
        args.timeout_ms,
        args.execute,
        args.airtime_budget_ms,
        args.tx_occupancy_cap_percent,
        args.environment,
    )
    write_result(result, args.output)


if __name__ == "__main__":
    main()
