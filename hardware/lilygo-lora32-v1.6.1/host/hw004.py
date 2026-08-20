#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import time
from typing import Any, Iterable

import hw002
import hw003


DEFAULT_ROUNDS = 4
SCHEDULE_PATTERN = (
    ("ascending", "a_to_b"),
    ("descending", "b_to_a"),
    ("descending", "a_to_b"),
    ("ascending", "b_to_a"),
)


def parse_info_counters(info_line: str) -> dict[str, int]:
    fields = hw002.parse_key_value_line(info_line, "INFO")
    required = (
        "task_wait_count",
        "task_wake_count",
        "task_spurious_wake_count",
        "task_mutex_timeout_count",
    )
    missing = [name for name in required if name not in fields]
    if missing:
        raise ValueError(f"missing HW-003 scheduler counters: {missing}")
    return {name: int(fields[name]) for name in required}


def counter_delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    return {name: after[name] - before[name] for name in before}


def make_schedule(
    sizes: tuple[int, ...],
    rounds: int,
    port_a: str,
    port_b: str,
) -> list[dict[str, Any]]:
    if rounds <= 0:
        raise ValueError("rounds must be positive")
    schedule: list[dict[str, Any]] = []
    sequence = 1
    order_index = 1

    for round_index in range(rounds):
        size_order_name, first_direction = SCHEDULE_PATTERN[round_index % len(SCHEDULE_PATTERN)]
        ordered_sizes = sizes if size_order_name == "ascending" else tuple(reversed(sizes))
        direction_order = (
            ("a_to_b", "b_to_a")
            if first_direction == "a_to_b"
            else ("b_to_a", "a_to_b")
        )
        for frame_bytes in ordered_sizes:
            for direction in direction_order:
                if direction == "a_to_b":
                    initiator_port, responder_port = port_a, port_b
                else:
                    initiator_port, responder_port = port_b, port_a
                schedule.append(
                    {
                        "order_index": order_index,
                        "round": round_index + 1,
                        "round_size_order": size_order_name,
                        "round_first_direction": first_direction,
                        "direction": direction,
                        "initiator_port": initiator_port,
                        "responder_port": responder_port,
                        "frame_bytes": frame_bytes,
                        "sequence": sequence,
                    }
                )
                order_index += 1
                sequence = 1 if sequence == 65535 else sequence + 1
    return schedule


def classify_attempt(sample: dict[str, Any]) -> str:
    measurement = sample["measurement"]
    if measurement.get("success"):
        return "success"

    tail = sample.get("responder_serial_tail") or []
    if any(line == "RXERR crc" for line in tail):
        return "responder_crc"
    if any(line.startswith("RXERR state=") for line in tail):
        return "responder_rx_error"
    if any(line.startswith("RXERR invalid-length=") for line in tail):
        return "responder_invalid_length"

    error = str(measurement.get("error", "unknown"))
    if error == "timeout":
        return "initiator_timeout_no_crc_observed"
    return f"initiator_{error}"


def numeric(values: Iterable[float]) -> dict[str, float | None]:
    return hw002.numeric_stats(values)


def summarize_attempts(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [attempt for attempt in attempts if attempt["failure_class"] == "success"]
    traces = [
        attempt["responder_trace"]
        for attempt in successes
        if attempt.get("responder_trace") is not None
    ]
    classes = Counter(attempt["failure_class"] for attempt in attempts)
    return {
        "attempts": len(attempts),
        "successes": len(successes),
        "failures": len(attempts) - len(successes),
        "descriptive_success_fraction": (
            len(successes) / len(attempts) if attempts else None
        ),
        "failure_classes": dict(sorted(classes.items())),
        "rtt_us": numeric(
            attempt["measurement"]["rtt_us"] for attempt in successes
        ),
        "remote_rssi_dbm": numeric(
            attempt["measurement"]["remote_rssi_dbm"] for attempt in successes
        ),
        "remote_snr_db": numeric(
            attempt["measurement"]["remote_snr_db"] for attempt in successes
        ),
        "local_rssi_dbm": numeric(
            attempt["measurement"]["local_rssi_dbm"] for attempt in successes
        ),
        "local_snr_db": numeric(
            attempt["measurement"]["local_snr_db"] for attempt in successes
        ),
        "irq_to_handle_us": numeric(
            trace["irq_to_handle_us"] for trace in traces
        ),
        "matched_responder_traces": len(traces),
        "wake_delta_equals_one": sum(
            1
            for attempt in attempts
            if attempt["responder_counter_delta"]["task_wake_count"] == 1
        ),
        "wait_delta_equals_one": sum(
            1
            for attempt in attempts
            if attempt["responder_counter_delta"]["task_wait_count"] == 1
        ),
        "spurious_wake_delta_total": sum(
            attempt["responder_counter_delta"]["task_spurious_wake_count"]
            for attempt in attempts
        ),
        "mutex_timeout_delta_total": sum(
            attempt["responder_counter_delta"]["task_mutex_timeout_count"]
            for attempt in attempts
        ),
    }


def experiment_summary(
    attempts: list[dict[str, Any]], sizes: tuple[int, ...]
) -> dict[str, Any]:
    by_direction = {
        direction: summarize_attempts(
            [attempt for attempt in attempts if attempt["direction"] == direction]
        )
        for direction in ("a_to_b", "b_to_a")
    }
    by_frame_bytes = {
        str(frame_bytes): summarize_attempts(
            [attempt for attempt in attempts if attempt["frame_bytes"] == frame_bytes]
        )
        for frame_bytes in sizes
    }
    by_cell: dict[str, Any] = {}
    for frame_bytes in sizes:
        by_cell[str(frame_bytes)] = {}
        for direction in ("a_to_b", "b_to_a"):
            by_cell[str(frame_bytes)][direction] = summarize_attempts(
                [
                    attempt
                    for attempt in attempts
                    if attempt["frame_bytes"] == frame_bytes
                    and attempt["direction"] == direction
                ]
            )

    failure_events = [
        {
            "order_index": attempt["order_index"],
            "round": attempt["round"],
            "direction": attempt["direction"],
            "frame_bytes": attempt["frame_bytes"],
            "sequence": attempt["sequence"],
            "failure_class": attempt["failure_class"],
            "measurement_error": attempt["measurement"].get("error"),
            "measurement_state": attempt["measurement"].get("state"),
            "responder_serial_tail": attempt.get("responder_serial_tail", []),
            "responder_counter_delta": attempt["responder_counter_delta"],
        }
        for attempt in attempts
        if attempt["failure_class"] != "success"
    ]

    return {
        "overall": summarize_attempts(attempts),
        "by_direction": by_direction,
        "by_frame_bytes": by_frame_bytes,
        "by_frame_bytes_and_direction": by_cell,
        "failure_events": failure_events,
        "crc_events": [
            event for event in failure_events if event["failure_class"] == "responder_crc"
        ],
    }


def build_plan(
    port_a,
    port_b,
    port_a_name: str,
    port_b_name: str,
    sizes: tuple[int, ...],
    rounds: int,
    tx_occupancy_cap_percent: float | None,
) -> dict[str, Any]:
    schedule = make_schedule(sizes, rounds, port_a_name, port_b_name)
    toa_a: dict[int, int] = {}
    toa_b: dict[int, int] = {}
    for frame_bytes in sizes:
        toa_a[frame_bytes] = hw002.query_toa(port_a, frame_bytes)
        toa_b[frame_bytes] = hw002.query_toa(port_b, frame_bytes)
        if toa_a[frame_bytes] != toa_b[frame_bytes]:
            raise RuntimeError(
                f"TOA mismatch at {frame_bytes} bytes: "
                f"{port_a_name}={toa_a[frame_bytes]} us, "
                f"{port_b_name}={toa_b[frame_bytes]} us"
            )

    transaction_toa_us = [toa_a[item["frame_bytes"]] for item in schedule]
    planned_per_node_airtime_us = sum(transaction_toa_us)
    planned_two_node_radio_bytes = sum(item["frame_bytes"] * 2 for item in schedule)
    wall_estimate = hw002.estimate_minimum_wall_seconds(
        transaction_toa_us, tx_occupancy_cap_percent
    )

    schedule_with_toa = []
    for item, toa_us in zip(schedule, transaction_toa_us):
        enriched = dict(item)
        enriched["toa_us_per_frame"] = toa_us
        schedule_with_toa.append(enriched)

    return {
        "schema": "pollicino-hw004-plan-v1",
        "design": "counterbalanced-direction-size-matrix",
        "port_a": port_a_name,
        "port_b": port_b_name,
        "sizes": list(sizes),
        "rounds": rounds,
        "transactions": len(schedule),
        "attempts_per_direction_size_cell": rounds,
        "toa_us_by_frame_bytes": {str(k): v for k, v in toa_a.items()},
        "planned_per_node_tx_airtime_us": planned_per_node_airtime_us,
        "planned_two_node_radio_bytes_if_all_successful": planned_two_node_radio_bytes,
        "tx_occupancy_cap_percent": tx_occupancy_cap_percent,
        "estimated_minimum_wall_seconds_for_requested_cap": wall_estimate,
        "schedule_pattern": [
            {"size_order": size_order, "first_direction": direction}
            for size_order, direction in SCHEDULE_PATTERN
        ],
        "schedule": schedule_with_toa,
        "regulatory_note": (
            "The occupancy cap is an experiment pacing input, not a claim of legal "
            "compliance. Verify the current regional/sub-band rules before RF execution."
        ),
        "statistical_note": (
            "Cell counts are intentionally small and exploratory. Bench success fractions "
            "must not be interpreted as deployment packet-loss probabilities."
        ),
    }


def run_matrix(
    port_a_name: str,
    port_b_name: str,
    sizes: tuple[int, ...],
    rounds: int,
    timeout_ms: int,
    execute: bool,
    airtime_budget_ms: float | None,
    tx_occupancy_cap_percent: float | None,
    environment: str | None,
    distance_m: float | None,
) -> dict[str, Any]:
    if port_a_name == port_b_name:
        raise ValueError("port A and port B must be different")

    port_a = hw002.open_port(port_a_name)
    try:
        port_b = hw002.open_port(port_b_name)
    except Exception:
        port_a.close()
        raise

    try:
        info_a = hw002.query_info(port_a)
        info_b = hw002.query_info(port_b)
        hw003.require_hw003_capability(info_a, "port A")
        hw003.require_hw003_capability(info_b, "port B")
        plan = build_plan(
            port_a,
            port_b,
            port_a_name,
            port_b_name,
            sizes,
            rounds,
            tx_occupancy_cap_percent,
        )

        base = {
            "schema": "pollicino-hw004-matrix-v1",
            "executed": execute,
            "port_a": port_a_name,
            "port_b": port_b_name,
            "port_a_info": info_a,
            "port_b_info": info_b,
            "environment": environment,
            "distance_m": distance_m,
            "timeout_ms": timeout_ms,
            "plan": plan,
            "semantics": semantics(),
        }
        if not execute:
            return base

        if airtime_budget_ms is None or airtime_budget_ms <= 0:
            raise ValueError("positive --airtime-budget-ms is required with --execute")
        if tx_occupancy_cap_percent is None:
            raise ValueError("--tx-occupancy-cap-percent is required with --execute")
        planned_ms = plan["planned_per_node_tx_airtime_us"] / 1000.0
        if planned_ms > airtime_budget_ms:
            raise ValueError(
                f"planned per-node TX airtime {planned_ms:.3f} ms exceeds explicit "
                f"budget {airtime_budget_ms:.3f} ms"
            )

        ports = {port_a_name: port_a, port_b_name: port_b}
        fraction = tx_occupancy_cap_percent / 100.0
        attempts: list[dict[str, Any]] = []
        previous_start: float | None = None
        previous_min_interval_s = 0.0
        run_started = time.monotonic()

        for item in plan["schedule"]:
            if previous_start is not None:
                due = previous_start + previous_min_interval_s
                remaining = due - time.monotonic()
                if remaining > 0:
                    time.sleep(remaining)

            initiator = ports[item["initiator_port"]]
            responder = ports[item["responder_port"]]
            before_info = hw002.query_info(responder)
            before_counters = parse_info_counters(before_info)

            previous_start = time.monotonic()
            sample = hw003.measure_with_trace(
                initiator,
                responder,
                item["sequence"],
                item["frame_bytes"],
                timeout_ms,
            )
            previous_min_interval_s = (
                item["toa_us_per_frame"] / 1_000_000.0
            ) / fraction

            after_info = hw002.query_info(responder)
            after_counters = parse_info_counters(after_info)

            attempt = dict(item)
            attempt.update(sample)
            attempt["measurement"] = sample["measurement"]
            attempt["failure_class"] = classify_attempt(sample)
            attempt["responder_info_before"] = before_info
            attempt["responder_info_after"] = after_info
            attempt["responder_counters_before"] = before_counters
            attempt["responder_counters_after"] = after_counters
            attempt["responder_counter_delta"] = counter_delta(
                before_counters, after_counters
            )
            attempt["host_elapsed_s"] = time.monotonic() - run_started
            attempts.append(attempt)

        base["elapsed_s"] = time.monotonic() - run_started
        base["attempts"] = attempts
        base["summary"] = experiment_summary(attempts, sizes)
        return base
    finally:
        port_b.close()
        port_a.close()


def semantics() -> dict[str, str]:
    return {
        "scope": (
            "HW-004 is a controlled same-bench exploratory reliability/CRC matrix using "
            "the already validated HW-003 event-driven firmware. It does not estimate "
            "deployment packet-loss probability."
        ),
        "direction": (
            "a_to_b means port A initiates and port B responds; b_to_a reverses roles."
        ),
        "failure_class_responder_crc": (
            "The initiator transaction failed and the responder USB log emitted exactly "
            "RXERR crc, corresponding to RadioLib CRC mismatch handling."
        ),
        "scheduler_counter_delta": (
            "Responder INFO counters are sampled immediately before and after each attempt. "
            "A wake delta of one on a CRC event separates task wakeup from successful frame decode."
        ),
        "order_control": (
            "A four-round counterbalancing cycle alternates ascending/descending size order "
            "and which direction is tested first within each size pair to reduce simple "
            "time/order confounding."
        ),
        "energy_boundary": (
            "No electrical current/power measurement is performed; scheduler counters and "
            "radio airtime must not be converted to joules or battery life."
        ),
        "radio_boundary": (
            "RSSI/SNR exist only for successful decoded transactions in the current firmware; "
            "CRC-failed frames therefore cannot be assigned a valid per-frame RSSI/SNR here."
        ),
    }


def selftest() -> dict[str, Any]:
    sizes = (16, 42)
    schedule = make_schedule(sizes, 4, "COM3", "COM4")
    if len(schedule) != 16:
        raise AssertionError("schedule length")
    cells = Counter((item["frame_bytes"], item["direction"]) for item in schedule)
    if set(cells.values()) != {4}:
        raise AssertionError(f"unbalanced cells: {cells}")
    if schedule[0]["frame_bytes"] != 16 or schedule[0]["direction"] != "a_to_b":
        raise AssertionError("round 1 pattern")
    round2 = [item for item in schedule if item["round"] == 2]
    if round2[0]["frame_bytes"] != 42 or round2[0]["direction"] != "b_to_a":
        raise AssertionError("round 2 pattern")

    crc_sample = {
        "measurement": {
            "success": False,
            "error": "timeout",
            "state": -6,
            "rtt_us": 3000000,
            "bytes": 42,
        },
        "responder_serial_tail": ["RXERR crc"],
    }
    if classify_attempt(crc_sample) != "responder_crc":
        raise AssertionError("CRC classification")

    timeout_sample = {
        "measurement": {
            "success": False,
            "error": "timeout",
            "state": -6,
            "rtt_us": 3000000,
            "bytes": 42,
        },
        "responder_serial_tail": [],
    }
    if classify_attempt(timeout_sample) != "initiator_timeout_no_crc_observed":
        raise AssertionError("timeout classification")

    before = {
        "task_wait_count": 9,
        "task_wake_count": 8,
        "task_spurious_wake_count": 0,
        "task_mutex_timeout_count": 0,
    }
    after = {
        "task_wait_count": 10,
        "task_wake_count": 9,
        "task_spurious_wake_count": 0,
        "task_mutex_timeout_count": 0,
    }
    delta = counter_delta(before, after)
    if delta["task_wait_count"] != 1 or delta["task_wake_count"] != 1:
        raise AssertionError("counter delta")

    return {
        "success": True,
        "counterbalanced_schedule": True,
        "failure_classification": True,
        "counter_delta": True,
    }


def write_json(result: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PollicinoNet HW-004 counterbalanced CRC/reliability matrix"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("selftest", help="pure host schedule/classification self-test")

    matrix = sub.add_parser(
        "matrix",
        help="dry-run by default; add --execute plus explicit airtime/occupancy limits",
    )
    matrix.add_argument("--port-a", required=True)
    matrix.add_argument("--port-b", required=True)
    matrix.add_argument(
        "--sizes",
        default=",".join(str(value) for value in hw002.DEFAULT_SIZES),
        help="comma-separated frame sizes",
    )
    matrix.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS)
    matrix.add_argument("--timeout-ms", type=int, default=3000)
    matrix.add_argument("--execute", action="store_true")
    matrix.add_argument("--airtime-budget-ms", type=float)
    matrix.add_argument("--tx-occupancy-cap-percent", type=float)
    matrix.add_argument("--environment")
    matrix.add_argument("--distance-m", type=float)
    matrix.add_argument("--output", type=Path)

    args = parser.parse_args()
    if args.command == "selftest":
        write_json(selftest(), None)
        return 0

    if args.rounds <= 0 or args.rounds > 100:
        raise SystemExit("--rounds must be in 1..100")
    try:
        sizes = hw002.parse_sizes(args.sizes)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    result = run_matrix(
        args.port_a,
        args.port_b,
        sizes,
        args.rounds,
        args.timeout_ms,
        args.execute,
        args.airtime_budget_ms,
        args.tx_occupancy_cap_percent,
        args.environment,
        args.distance_m,
    )
    write_json(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
