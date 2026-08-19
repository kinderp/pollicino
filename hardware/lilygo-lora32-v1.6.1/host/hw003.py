#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from typing import Any

import hw002
import hw002_timing


SCHEDULER_TRACE_VERSION = 1


def parse_hw003_trace(line: str) -> dict[str, Any]:
    trace = hw002_timing.parse_responder_trace(line)
    fields = hw002.parse_key_value_line(line, "H2RESP")
    required = (
        "sched_v",
        "task_wait_count",
        "task_wake_count",
        "task_spurious_wake_count",
    )
    missing = [name for name in required if name not in fields]
    if missing:
        raise ValueError(f"missing HW-003 scheduler fields: {missing}")

    scheduler_version = int(fields["sched_v"])
    if scheduler_version != SCHEDULER_TRACE_VERSION:
        raise ValueError(
            f"unsupported HW-003 scheduler trace version {scheduler_version}"
        )

    trace.update(
        {
            "scheduler_version": scheduler_version,
            "task_wait_count": int(fields["task_wait_count"]),
            "task_wake_count": int(fields["task_wake_count"]),
            "task_spurious_wake_count": int(fields["task_spurious_wake_count"]),
        }
    )
    return trace


def require_hw003_capability(info_line: str, role: str) -> None:
    hw002_timing.require_timing_capability(info_line, role)
    fields = hw002.parse_key_value_line(info_line, "INFO")
    if fields.get("lab") != "hw-003":
        raise RuntimeError(f"{role} firmware is not HW-003: {info_line}")
    if fields.get("event_driven_rx") != "1":
        raise RuntimeError(f"{role} firmware does not advertise event_driven_rx=1")
    if fields.get("scheduler_trace") != "1":
        raise RuntimeError(f"{role} firmware does not advertise scheduler_trace=1")
    if int(fields.get("scheduler_trace_version", "0")) != SCHEDULER_TRACE_VERSION:
        raise RuntimeError(
            f"{role} scheduler trace version is not {SCHEDULER_TRACE_VERSION}: {info_line}"
        )


def read_matching_trace(
    responder_port,
    sequence: int,
    frame_bytes: int,
    timeout_s: float = 0.75,
) -> tuple[dict[str, Any] | None, list[str]]:
    deadline = time.monotonic() + timeout_s
    seen: list[str] = []
    while time.monotonic() < deadline:
        line = hw002.read_line(responder_port, deadline)
        if line is None:
            break
        seen.append(line)
        if not line.startswith("H2RESP "):
            continue
        trace = parse_hw003_trace(line)
        if trace["sequence"] == sequence and trace["bytes"] == frame_bytes:
            return trace, seen
    return None, seen


def measure_with_trace(
    initiator_port,
    responder_port,
    sequence: int,
    frame_bytes: int,
    timeout_ms: int,
) -> dict[str, Any]:
    responder_port.reset_input_buffer()
    measurement = hw002.measure_once(
        initiator_port, sequence, frame_bytes, timeout_ms
    )
    trace, responder_seen = read_matching_trace(
        responder_port, sequence, frame_bytes
    )
    return {
        "measurement": measurement,
        "responder_trace": trace,
        "responder_trace_matched": trace is not None,
        "responder_serial_tail": responder_seen[-8:],
        "derived_timing": hw002_timing.derive_timing(measurement, trace),
    }


def scheduler_summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    traces = [
        sample["responder_trace"]
        for sample in samples
        if sample.get("responder_trace") is not None
        and sample["responder_trace"].get("scheduler_version") == SCHEDULER_TRACE_VERSION
    ]
    if not traces:
        return {
            "matched_scheduler_traces": 0,
            "counter_sequence_consistent": False,
        }

    wait_counts = [int(trace["task_wait_count"]) for trace in traces]
    wake_counts = [int(trace["task_wake_count"]) for trace in traces]
    spurious_counts = [int(trace["task_spurious_wake_count"]) for trace in traces]

    def increments_by_one(values: list[int]) -> bool:
        return all(b == a + 1 for a, b in zip(values, values[1:]))

    return {
        "matched_scheduler_traces": len(traces),
        "task_wait_count_start": wait_counts[0],
        "task_wait_count_end": wait_counts[-1],
        "task_wait_count_delta": wait_counts[-1] - wait_counts[0],
        "task_wake_count_start": wake_counts[0],
        "task_wake_count_end": wake_counts[-1],
        "task_wake_count_delta": wake_counts[-1] - wake_counts[0],
        "task_spurious_wake_count_start": spurious_counts[0],
        "task_spurious_wake_count_end": spurious_counts[-1],
        "task_spurious_wake_count_delta": spurious_counts[-1] - spurious_counts[0],
        "wait_counter_increments_by_one": increments_by_one(wait_counts),
        "wake_counter_increments_by_one": increments_by_one(wake_counts),
        "spurious_counter_nondecreasing": all(
            b >= a for a, b in zip(spurious_counts, spurious_counts[1:])
        ),
        "counter_sequence_consistent": (
            increments_by_one(wait_counts)
            and increments_by_one(wake_counts)
            and all(b >= a for a, b in zip(spurious_counts, spurious_counts[1:]))
        ),
    }


def hw003_summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    base = hw002_timing.timing_summary(samples)
    base["scheduler_trace"] = scheduler_summary(samples)
    return base


def open_pair(initiator_name: str, responder_name: str):
    if initiator_name == responder_name:
        raise ValueError("initiator and responder ports must be different")
    initiator = hw002.open_port(initiator_name)
    try:
        responder = hw002.open_port(responder_name)
    except Exception:
        initiator.close()
        raise
    return initiator, responder


def run_single(
    initiator_name: str,
    responder_name: str,
    sequence: int,
    frame_bytes: int,
    timeout_ms: int,
) -> dict[str, Any]:
    initiator, responder = open_pair(initiator_name, responder_name)
    try:
        initiator_info = hw002.query_info(initiator)
        responder_info = hw002.query_info(responder)
        require_hw003_capability(initiator_info, "initiator")
        require_hw003_capability(responder_info, "responder")
        sample = measure_with_trace(
            initiator, responder, sequence, frame_bytes, timeout_ms
        )
        return {
            "schema": "pollicino-hw003-single-v1",
            "initiator_port": initiator_name,
            "responder_port": responder_name,
            "initiator_info": initiator_info,
            "responder_info": responder_info,
            "sample": sample,
            "scheduler_summary": scheduler_summary([sample]),
            "semantics": semantics(),
        }
    finally:
        responder.close()
        initiator.close()


def run_benchmark(
    initiator_name: str,
    responder_name: str,
    frame_bytes: int,
    count: int,
    timeout_ms: int,
    execute: bool,
    airtime_budget_ms: float | None,
    tx_occupancy_cap_percent: float | None,
    environment: str | None,
    distance_m: float | None,
) -> dict[str, Any]:
    initiator, responder = open_pair(initiator_name, responder_name)
    try:
        initiator_info = hw002.query_info(initiator)
        responder_info = hw002.query_info(responder)
        require_hw003_capability(initiator_info, "initiator")
        require_hw003_capability(responder_info, "responder")

        plan = hw002.build_plan(
            initiator,
            (frame_bytes,),
            count,
            tx_occupancy_cap_percent,
        )
        if not execute:
            return {
                "schema": "pollicino-hw003-plan-v1",
                "executed": False,
                "initiator_port": initiator_name,
                "responder_port": responder_name,
                "initiator_info": initiator_info,
                "responder_info": responder_info,
                "plan": plan,
                "semantics": semantics(),
            }

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

        toa_us = int(plan["sizes"][0]["toa_us_per_frame"])
        fraction = tx_occupancy_cap_percent / 100.0
        minimum_interval_s = (toa_us / 1_000_000.0) / fraction
        samples: list[dict[str, Any]] = []
        previous_start: float | None = None
        run_started = time.monotonic()

        for index in range(count):
            if previous_start is not None:
                due = previous_start + minimum_interval_s
                remaining = due - time.monotonic()
                if remaining > 0:
                    time.sleep(remaining)
            previous_start = time.monotonic()
            sample = measure_with_trace(
                initiator,
                responder,
                index + 1,
                frame_bytes,
                timeout_ms,
            )
            sample["host_elapsed_s"] = time.monotonic() - run_started
            samples.append(sample)

        return {
            "schema": "pollicino-hw003-benchmark-v1",
            "executed": True,
            "initiator_port": initiator_name,
            "responder_port": responder_name,
            "initiator_info": initiator_info,
            "responder_info": responder_info,
            "environment": environment,
            "distance_m": distance_m,
            "timeout_ms": timeout_ms,
            "elapsed_s": time.monotonic() - run_started,
            "plan": plan,
            "samples": samples,
            "summary": hw003_summary(samples),
            "semantics": semantics(),
        }
    finally:
        responder.close()
        initiator.close()


def semantics() -> dict[str, str]:
    result = dict(hw002_timing.timing_semantics())
    result.update(
        {
            "event_driven_rx": (
                "SX1276 RX-done notifies a dedicated FreeRTOS responder task. The Arduino "
                "loop retains a 1 ms idle delay but does not poll for received radio packets."
            ),
            "task_wait_count": (
                "Cumulative number of times the responder task entered its blocking direct-"
                "notification wait. This is a scheduler proxy, not an energy measurement."
            ),
            "task_wake_count": (
                "Cumulative direct-notification wakeups consumed by the responder task."
            ),
            "task_spurious_wake_count": (
                "Cumulative responder-task wakeups for which no pending packet flag remained."
            ),
            "energy_boundary": (
                "No electrical power/current measurement is performed. Scheduler blocking "
                "must not be converted into watts, joules, current draw or battery life."
            ),
        }
    )
    return result


def selftest() -> dict[str, Any]:
    line = (
        "H2RESP seq=7 bytes=42 rssi_dbm=-39.0 snr_db=9.75 toa_us=88000 "
        "state=0 timing_v=1 irq_to_handle_us=8 handle_to_read_done_us=796 "
        "read_done_to_tx_start_us=485 irq_to_tx_start_us=1289 tx_block_us=90059 "
        "irq_to_tx_done_us=91348 sched_v=1 task_wait_count=11 task_wake_count=11 "
        "task_spurious_wake_count=0"
    )
    trace = parse_hw003_trace(line)
    if trace["sequence"] != 7 or trace["task_wake_count"] != 11:
        raise AssertionError("HW-003 trace parser failed")

    measurement = hw002.parse_measurement_line(
        "MRESULT seq=7 bytes=42 success=1 rtt_us=181100 tx_block_us=89720 "
        "toa_us=88000 remote_rssi_dbm=-39.0 remote_snr_db=9.75 "
        "local_rssi_dbm=-38.0 local_snr_db=10.0"
    )
    derived = hw002_timing.derive_timing(measurement, trace)
    if derived is None:
        raise AssertionError("HW-003 timing derivation failed")

    trace2 = dict(trace)
    trace2["sequence"] = 8
    trace2["task_wait_count"] = 12
    trace2["task_wake_count"] = 12
    summary = scheduler_summary(
        [
            {
                "measurement": measurement,
                "responder_trace": trace,
                "derived_timing": derived,
            },
            {
                "measurement": measurement,
                "responder_trace": trace2,
                "derived_timing": derived,
            },
        ]
    )
    if not summary["counter_sequence_consistent"]:
        raise AssertionError(f"HW-003 scheduler summary failed: {summary}")

    return {
        "success": True,
        "trace_parser": True,
        "timing_derivation": True,
        "scheduler_summary": True,
    }


def write_json(result: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PollicinoNet HW-003 event-driven responder runner"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("selftest", help="pure host HW-003 parser/summary self-test")

    measure = sub.add_parser("measure", help="run one HW-003 H2 ping/pong")
    measure.add_argument("--initiator-port", required=True)
    measure.add_argument("--responder-port", required=True)
    measure.add_argument("--seq", type=int, default=1)
    measure.add_argument("--bytes", type=int, default=42)
    measure.add_argument("--timeout-ms", type=int, default=3000)
    measure.add_argument("--output", type=Path)

    bench = sub.add_parser(
        "benchmark",
        help="dry-run by default; add --execute plus explicit airtime/occupancy limits",
    )
    bench.add_argument("--initiator-port", required=True)
    bench.add_argument("--responder-port", required=True)
    bench.add_argument("--bytes", type=int, default=42)
    bench.add_argument("--count", type=int, default=20)
    bench.add_argument("--timeout-ms", type=int, default=3000)
    bench.add_argument("--execute", action="store_true")
    bench.add_argument("--airtime-budget-ms", type=float)
    bench.add_argument("--tx-occupancy-cap-percent", type=float)
    bench.add_argument("--environment")
    bench.add_argument("--distance-m", type=float)
    bench.add_argument("--output", type=Path)

    args = parser.parse_args()

    if args.command == "selftest":
        write_json(selftest(), None)
        return 0

    if not hw002.MIN_FRAME_BYTES <= args.bytes <= hw002.MAX_FRAME_BYTES:
        raise SystemExit(
            f"--bytes must be in {hw002.MIN_FRAME_BYTES}..{hw002.MAX_FRAME_BYTES}"
        )

    if args.command == "measure":
        if not 0 <= args.seq <= 65535:
            raise SystemExit("--seq must be in 0..65535")
        result = run_single(
            args.initiator_port,
            args.responder_port,
            args.seq,
            args.bytes,
            args.timeout_ms,
        )
        write_json(result, args.output)
        return 0

    if args.count <= 0 or args.count > 65535:
        raise SystemExit("--count must be in 1..65535")
    result = run_benchmark(
        args.initiator_port,
        args.responder_port,
        args.bytes,
        args.count,
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
