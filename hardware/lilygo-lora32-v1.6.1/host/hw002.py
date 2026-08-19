#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import time
from typing import Any, Iterable

DEFAULT_SIZES = (16, 32, 42, 60, 120, 240)
MAX_FRAME_BYTES = 240
MIN_FRAME_BYTES = 16


def _serial_module():
    try:
        import serial  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "pyserial is required for hardware access. Install it with: "
            "python -m pip install pyserial"
        ) from exc
    return serial


def open_port(name: str):
    serial = _serial_module()
    port = serial.Serial(name, baudrate=115200, timeout=0.2, write_timeout=2)
    # Opening an ESP32 serial port may reset the board.
    time.sleep(1.5)
    port.reset_input_buffer()
    return port


def write_line(port, text: str) -> None:
    port.write((text + "\n").encode("ascii"))
    port.flush()


def read_line(port, deadline: float) -> str | None:
    while time.monotonic() < deadline:
        raw = port.readline()
        if not raw:
            continue
        return raw.decode("utf-8", errors="replace").strip()
    return None


def wait_prefix(port, prefix: str, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    seen: list[str] = []
    while time.monotonic() < deadline:
        line = read_line(port, deadline)
        if line is None:
            break
        seen.append(line)
        if line.startswith("ERR "):
            raise RuntimeError(f"device rejected command: {line}")
        if line.startswith(prefix):
            return line
    raise TimeoutError(f"did not receive {prefix!r}; seen={seen[-8:]}")


def parse_key_value_line(line: str, prefix: str) -> dict[str, str]:
    parts = line.split()
    if not parts or parts[0] != prefix:
        raise ValueError(f"expected {prefix!r} line, got {line!r}")
    parsed: dict[str, str] = {}
    for token in parts[1:]:
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        if not key or key in parsed:
            raise ValueError(f"malformed or duplicate field in {line!r}")
        parsed[key] = value
    return parsed


def parse_toa_line(line: str) -> dict[str, int]:
    fields = parse_key_value_line(line, "TOA")
    return {"bytes": int(fields["bytes"]), "toa_us": int(fields["us"])}


def parse_measurement_line(line: str) -> dict[str, Any]:
    fields = parse_key_value_line(line, "MRESULT")
    result: dict[str, Any] = {
        "sequence": int(fields["seq"]),
        "bytes": int(fields["bytes"]),
        "success": fields["success"] == "1",
        "rtt_us": int(fields["rtt_us"]),
        "tx_block_us": int(fields["tx_block_us"]),
        "toa_us": int(fields["toa_us"]),
    }
    if result["success"]:
        result.update(
            remote_rssi_dbm=float(fields["remote_rssi_dbm"]),
            remote_snr_db=float(fields["remote_snr_db"]),
            local_rssi_dbm=float(fields["local_rssi_dbm"]),
            local_snr_db=float(fields["local_snr_db"]),
        )
    else:
        result["error"] = fields.get("error", "unknown")
        result["state"] = int(fields.get("state", "0"))
    return result


def parse_sizes(text: str) -> tuple[int, ...]:
    values: list[int] = []
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        value = int(item)
        if not MIN_FRAME_BYTES <= value <= MAX_FRAME_BYTES:
            raise ValueError(
                f"frame size {value} outside {MIN_FRAME_BYTES}..{MAX_FRAME_BYTES} bytes"
            )
        if value not in values:
            values.append(value)
    if not values:
        raise ValueError("at least one frame size is required")
    return tuple(values)


def query_info(port, timeout: float = 3.0) -> str:
    write_line(port, "INFO")
    return wait_prefix(port, "INFO ", timeout)


def query_toa(port, frame_bytes: int, timeout: float = 3.0) -> int:
    write_line(port, f"TOA {frame_bytes}")
    parsed = parse_toa_line(wait_prefix(port, "TOA ", timeout))
    if parsed["bytes"] != frame_bytes:
        raise RuntimeError(
            f"TOA response size mismatch: requested {frame_bytes}, got {parsed['bytes']}"
        )
    return parsed["toa_us"]


def measure_once(port, sequence: int, frame_bytes: int, timeout_ms: int) -> dict[str, Any]:
    write_line(port, f"MPING {sequence} {frame_bytes} {timeout_ms}")
    # Firmware itself waits up to timeout_ms for the radio PONG.
    line = wait_prefix(port, "MRESULT ", timeout_ms / 1000.0 + 3.0)
    result = parse_measurement_line(line)
    if result["sequence"] != sequence or result["bytes"] != frame_bytes:
        raise RuntimeError("measurement result does not match requested sequence/size")
    return result


def nearest_rank(values: Iterable[float], percentile: float) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


def numeric_stats(values: Iterable[float]) -> dict[str, float | None]:
    vals = list(values)
    if not vals:
        return {"min": None, "mean": None, "p50": None, "p95": None, "max": None}
    return {
        "min": min(vals),
        "mean": statistics.fmean(vals),
        "p50": statistics.median(vals),
        "p95": nearest_rank(vals, 0.95),
        "max": max(vals),
    }


def estimate_minimum_wall_seconds(
    transaction_toa_us: list[int],
    tx_occupancy_cap_percent: float | None,
) -> float | None:
    """Nominal all-success lower-bound wall time for the sequential runner.

    The pacing interval constrains the next transaction *start*. The runner is
    also blocking, so a next start cannot occur before the current nominal
    PING+PONG radio transaction has completed. There is no post-final pacing
    interval; the final transaction contributes only its nominal round-trip
    time-on-air. Firmware turnaround is intentionally excluded from this lower
    bound.
    """
    if tx_occupancy_cap_percent is None:
        return None
    if not 0.0 < tx_occupancy_cap_percent <= 100.0:
        raise ValueError("tx occupancy cap must be in (0, 100]")
    if not transaction_toa_us:
        return 0.0

    fraction = tx_occupancy_cap_percent / 100.0
    total_seconds = 0.0
    for toa_us in transaction_toa_us[:-1]:
        toa_s = toa_us / 1_000_000.0
        pacing_interval_s = toa_s / fraction
        nominal_round_trip_s = toa_s * 2.0
        total_seconds += max(pacing_interval_s, nominal_round_trip_s)

    total_seconds += (transaction_toa_us[-1] * 2.0) / 1_000_000.0
    return total_seconds


def build_plan(
    port,
    sizes: tuple[int, ...],
    count: int,
    tx_occupancy_cap_percent: float | None,
) -> dict[str, Any]:
    if count <= 0:
        raise ValueError("count must be positive")
    info = query_info(port)
    by_size: list[dict[str, Any]] = []
    transaction_toa_us: list[int] = []
    total_airtime_us = 0
    total_radio_bytes = 0
    fraction = None
    if tx_occupancy_cap_percent is not None:
        if not 0.0 < tx_occupancy_cap_percent <= 100.0:
            raise ValueError("tx occupancy cap must be in (0, 100]")
        fraction = tx_occupancy_cap_percent / 100.0

    for frame_bytes in sizes:
        toa_us = query_toa(port, frame_bytes)
        transaction_toa_us.extend([toa_us] * count)
        per_node_airtime_us = toa_us * count
        total_airtime_us += per_node_airtime_us
        total_radio_bytes += frame_bytes * 2 * count
        start_interval_s = None
        if fraction is not None:
            start_interval_s = (toa_us / 1_000_000.0) / fraction
        by_size.append(
            {
                "frame_bytes": frame_bytes,
                "toa_us_per_frame": toa_us,
                "count": count,
                "per_node_planned_tx_airtime_us": per_node_airtime_us,
                "round_trip_radio_bytes_if_successful": frame_bytes * 2,
                "minimum_start_interval_s_for_requested_cap": start_interval_s,
            }
        )

    estimated_wall_seconds = estimate_minimum_wall_seconds(
        transaction_toa_us, tx_occupancy_cap_percent
    )

    return {
        "schema": "pollicino-hw002-plan-v1",
        "info": info,
        "sizes": by_size,
        "count_per_size": count,
        "transactions": len(sizes) * count,
        "planned_per_node_tx_airtime_us": total_airtime_us,
        "planned_two_node_radio_bytes_if_all_successful": total_radio_bytes,
        "tx_occupancy_cap_percent": tx_occupancy_cap_percent,
        "estimated_minimum_wall_seconds_for_requested_cap": estimated_wall_seconds,
        "wall_time_estimate_note": (
            "Nominal all-success lower bound for this sequential runner: pacing between "
            "transaction starts, no post-final pacing interval, and nominal two-frame "
            "time-on-air for the final transaction. Firmware turnaround is excluded."
        ),
        "regulatory_note": (
            "The occupancy cap is an experiment pacing input, not a claim of legal "
            "compliance. Verify the current regional/sub-band rules before RF execution."
        ),
    }


def summarize_samples(samples: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [sample for sample in samples if sample["success"]]
    attempts = len(samples)
    success_count = len(successes)

    initiator_airtime_us = sum(sample["toa_us"] for sample in samples)
    responder_confirmed_airtime_us = sum(sample["toa_us"] for sample in successes)
    initiator_radio_bytes = sum(sample["bytes"] for sample in samples)
    responder_confirmed_radio_bytes = sum(sample["bytes"] for sample in successes)

    return {
        "attempts": attempts,
        "successes": success_count,
        "failures": attempts - success_count,
        "success_rate": success_count / attempts if attempts else None,
        "loss_rate": (attempts - success_count) / attempts if attempts else None,
        "rtt_us": numeric_stats(sample["rtt_us"] for sample in successes),
        "tx_block_us": numeric_stats(sample["tx_block_us"] for sample in samples),
        "remote_rssi_dbm": numeric_stats(
            sample["remote_rssi_dbm"] for sample in successes
        ),
        "remote_snr_db": numeric_stats(sample["remote_snr_db"] for sample in successes),
        "local_rssi_dbm": numeric_stats(
            sample["local_rssi_dbm"] for sample in successes
        ),
        "local_snr_db": numeric_stats(sample["local_snr_db"] for sample in successes),
        "airtime_accounting": {
            "initiator_predicted_tx_airtime_us_exact": initiator_airtime_us,
            "responder_confirmed_tx_airtime_us_lower_bound": responder_confirmed_airtime_us,
            "two_node_confirmed_tx_airtime_us_lower_bound": (
                initiator_airtime_us + responder_confirmed_airtime_us
            ),
            "note": (
                "On a failed transaction the responder may have transmitted a PONG that "
                "was lost, so responder/two-node values are lower bounds."
            ),
        },
        "radio_byte_accounting": {
            "initiator_bytes_exact": initiator_radio_bytes,
            "responder_confirmed_bytes_lower_bound": responder_confirmed_radio_bytes,
            "two_node_confirmed_bytes_lower_bound": (
                initiator_radio_bytes + responder_confirmed_radio_bytes
            ),
        },
    }


def run_benchmark(
    port_name: str,
    sizes: tuple[int, ...],
    count: int,
    timeout_ms: int,
    execute: bool,
    airtime_budget_ms: float | None,
    tx_occupancy_cap_percent: float | None,
    distance_m: float | None,
    environment: str | None,
) -> dict[str, Any]:
    port = open_port(port_name)
    try:
        plan = build_plan(port, sizes, count, tx_occupancy_cap_percent)
        if not execute:
            return {"executed": False, "plan": plan}

        if airtime_budget_ms is None:
            raise ValueError("--airtime-budget-ms is required with --execute")
        if airtime_budget_ms <= 0:
            raise ValueError("airtime budget must be positive")
        if tx_occupancy_cap_percent is None:
            raise ValueError("--tx-occupancy-cap-percent is required with --execute")

        planned_ms = plan["planned_per_node_tx_airtime_us"] / 1000.0
        if planned_ms > airtime_budget_ms:
            raise ValueError(
                f"planned per-node TX airtime {planned_ms:.3f} ms exceeds explicit "
                f"budget {airtime_budget_ms:.3f} ms"
            )

        toa_by_size = {
            item["frame_bytes"]: item["toa_us_per_frame"] for item in plan["sizes"]
        }
        fraction = tx_occupancy_cap_percent / 100.0
        samples: list[dict[str, Any]] = []
        sequence = 1
        previous_start: float | None = None
        previous_min_interval_s = 0.0
        run_started = time.monotonic()

        for frame_bytes in sizes:
            toa_us = toa_by_size[frame_bytes]
            minimum_interval_s = (toa_us / 1_000_000.0) / fraction
            for _ in range(count):
                if previous_start is not None:
                    due = previous_start + previous_min_interval_s
                    remaining = due - time.monotonic()
                    if remaining > 0:
                        time.sleep(remaining)

                previous_start = time.monotonic()
                sample = measure_once(port, sequence, frame_bytes, timeout_ms)
                sample["host_elapsed_s"] = time.monotonic() - run_started
                samples.append(sample)
                previous_min_interval_s = minimum_interval_s
                sequence = 1 if sequence == 65535 else sequence + 1

        elapsed_s = time.monotonic() - run_started
        by_size: dict[str, Any] = {}
        for frame_bytes in sizes:
            subset = [sample for sample in samples if sample["bytes"] == frame_bytes]
            by_size[str(frame_bytes)] = summarize_samples(subset)

        result = {
            "schema": "pollicino-hw002-benchmark-v1",
            "executed": True,
            "port": port_name,
            "distance_m": distance_m,
            "environment": environment,
            "timeout_ms": timeout_ms,
            "elapsed_s": elapsed_s,
            "plan": plan,
            "samples": samples,
            "summary": summarize_samples(samples),
            "summary_by_frame_bytes": by_size,
            "measurement_semantics": {
                "remote": "RSSI/SNR measured by responder for initiator -> responder PING",
                "local": "RSSI/SNR measured by initiator for responder -> initiator PONG",
                "rtt": (
                    "firmware radio transaction RTT: initiator TX + responder processing + "
                    "responder TX + receive completion; USB/Python turnaround is excluded"
                ),
                "toa": "RadioLib getTimeOnAir(frame_bytes), microseconds",
            },
        }
        return result
    finally:
        port.close()


def selftest() -> dict[str, Any]:
    toa = parse_toa_line("TOA bytes=42 us=102912")
    if toa != {"bytes": 42, "toa_us": 102912}:
        raise AssertionError("TOA parser failed")

    success = parse_measurement_line(
        "MRESULT seq=7 bytes=42 success=1 rtt_us=220000 tx_block_us=103000 "
        "toa_us=102912 remote_rssi_dbm=-40.0 remote_snr_db=9.75 "
        "local_rssi_dbm=-37.0 local_snr_db=9.50"
    )
    if not success["success"] or success["sequence"] != 7:
        raise AssertionError("success parser failed")

    failure = parse_measurement_line(
        "MRESULT seq=8 bytes=60 success=0 error=timeout rtt_us=2000000 "
        "tx_block_us=120000 toa_us=118000 state=-6"
    )
    if failure["success"] or failure["error"] != "timeout":
        raise AssertionError("failure parser failed")

    summary = summarize_samples([success, failure])
    if summary["attempts"] != 2 or summary["successes"] != 1:
        raise AssertionError("summary failed")

    paced_estimate = estimate_minimum_wall_seconds([88000] * 10, 1.0)
    if paced_estimate is None or not math.isclose(
        paced_estimate, 79.376, rel_tol=0.0, abs_tol=1e-9
    ):
        raise AssertionError(f"wall-time pacing estimate failed: {paced_estimate}")

    blocking_estimate = estimate_minimum_wall_seconds([88000, 88000], 100.0)
    if blocking_estimate is None or not math.isclose(
        blocking_estimate, 0.352, rel_tol=0.0, abs_tol=1e-9
    ):
        raise AssertionError(f"wall-time blocking estimate failed: {blocking_estimate}")

    return {
        "success": True,
        "toa_parser": True,
        "measurement_parser": True,
        "failure_parser": True,
        "summary": True,
        "wall_time_estimator": True,
    }


def write_json(result: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PollicinoNet HW-002 physical LoRa measurement runner"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("selftest", help="pure host parser/accounting self-test")

    plan = sub.add_parser("plan", help="query time-on-air and build a no-TX experiment plan")
    plan.add_argument("--port", required=True)
    plan.add_argument("--sizes", default=",".join(map(str, DEFAULT_SIZES)))
    plan.add_argument("--count", type=int, default=3)
    plan.add_argument("--tx-occupancy-cap-percent", type=float)
    plan.add_argument("--output", type=Path)

    measure = sub.add_parser("measure", help="run one firmware-level radio ping/pong")
    measure.add_argument("--port", required=True)
    measure.add_argument("--seq", type=int, default=1)
    measure.add_argument("--bytes", type=int, default=42)
    measure.add_argument("--timeout-ms", type=int, default=3000)
    measure.add_argument("--output", type=Path)

    bench = sub.add_parser(
        "benchmark",
        help="plan by default; add --execute plus explicit airtime/occupancy limits to transmit",
    )
    bench.add_argument("--port", required=True)
    bench.add_argument("--sizes", default=",".join(map(str, DEFAULT_SIZES)))
    bench.add_argument("--count", type=int, default=3)
    bench.add_argument("--timeout-ms", type=int, default=3000)
    bench.add_argument("--execute", action="store_true")
    bench.add_argument("--airtime-budget-ms", type=float)
    bench.add_argument("--tx-occupancy-cap-percent", type=float)
    bench.add_argument("--distance-m", type=float)
    bench.add_argument("--environment")
    bench.add_argument("--output", type=Path)

    args = parser.parse_args()

    if args.command == "selftest":
        write_json(selftest(), None)
        return 0

    if args.command == "plan":
        port = open_port(args.port)
        try:
            result = build_plan(
                port,
                parse_sizes(args.sizes),
                args.count,
                args.tx_occupancy_cap_percent,
            )
        finally:
            port.close()
        write_json(result, args.output)
        return 0

    if args.command == "measure":
        if not 0 <= args.seq <= 65535:
            raise SystemExit("--seq must be in 0..65535")
        if not MIN_FRAME_BYTES <= args.bytes <= MAX_FRAME_BYTES:
            raise SystemExit(
                f"--bytes must be in {MIN_FRAME_BYTES}..{MAX_FRAME_BYTES}"
            )
        port = open_port(args.port)
        try:
            result = {
                "schema": "pollicino-hw002-single-v1",
                "info": query_info(port),
                "measurement": measure_once(
                    port, args.seq, args.bytes, args.timeout_ms
                ),
            }
        finally:
            port.close()
        write_json(result, args.output)
        return 0

    if args.command == "benchmark":
        result = run_benchmark(
            args.port,
            parse_sizes(args.sizes),
            args.count,
            args.timeout_ms,
            args.execute,
            args.airtime_budget_ms,
            args.tx_occupancy_cap_percent,
            args.distance_m,
            args.environment,
        )
        write_json(result, args.output)
        return 0

    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())