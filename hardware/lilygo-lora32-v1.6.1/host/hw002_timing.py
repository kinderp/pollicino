#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import time
from typing import Any

import hw002


TIMING_TRACE_VERSION = 1
LOOP_DELAY_VALUES = (0, 1)


def parse_responder_trace(line: str) -> dict[str, Any]:
    fields = hw002.parse_key_value_line(line, "H2RESP")
    required = (
        "seq",
        "bytes",
        "rssi_dbm",
        "snr_db",
        "toa_us",
        "state",
        "timing_v",
        "irq_to_handle_us",
        "handle_to_read_done_us",
        "read_done_to_tx_start_us",
        "irq_to_tx_start_us",
        "tx_block_us",
        "irq_to_tx_done_us",
    )
    missing = [name for name in required if name not in fields]
    if missing:
        raise ValueError(f"missing H2RESP timing fields: {missing}")

    trace: dict[str, Any] = {
        "sequence": int(fields["seq"]),
        "bytes": int(fields["bytes"]),
        "rssi_dbm": float(fields["rssi_dbm"]),
        "snr_db": float(fields["snr_db"]),
        "toa_us": int(fields["toa_us"]),
        "state": int(fields["state"]),
        "timing_version": int(fields["timing_v"]),
        "irq_to_handle_us": int(fields["irq_to_handle_us"]),
        "handle_to_read_done_us": int(fields["handle_to_read_done_us"]),
        "read_done_to_tx_start_us": int(fields["read_done_to_tx_start_us"]),
        "irq_to_tx_start_us": int(fields["irq_to_tx_start_us"]),
        "tx_block_us": int(fields["tx_block_us"]),
        "irq_to_tx_done_us": int(fields["irq_to_tx_done_us"]),
    }
    if trace["timing_version"] != TIMING_TRACE_VERSION:
        raise ValueError(
            f"unsupported timing trace version {trace['timing_version']}"
        )
    if trace["bytes"] < hw002.MIN_FRAME_BYTES or trace["bytes"] > hw002.MAX_FRAME_BYTES:
        raise ValueError("H2RESP frame size outside HW-002 bounds")
    if trace["irq_to_tx_start_us"] != (
        trace["irq_to_handle_us"]
        + trace["handle_to_read_done_us"]
        + trace["read_done_to_tx_start_us"]
    ):
        raise ValueError("H2RESP timing decomposition is internally inconsistent")
    if trace["irq_to_tx_done_us"] != (
        trace["irq_to_tx_start_us"] + trace["tx_block_us"]
    ):
        raise ValueError("H2RESP TX timing decomposition is internally inconsistent")
    return trace


def parse_loop_delay_line(line: str) -> int:
    fields = hw002.parse_key_value_line(line, "LOOPDELAY")
    if "ms" not in fields:
        raise ValueError("LOOPDELAY response missing ms field")
    value = int(fields["ms"])
    if value not in LOOP_DELAY_VALUES:
        raise ValueError(f"unsupported LOOPDELAY value {value}")
    return value


def require_timing_capability(info_line: str, role: str) -> None:
    fields = hw002.parse_key_value_line(info_line, "INFO")
    if fields.get("timing_trace") != "1":
        raise RuntimeError(f"{role} firmware does not advertise timing_trace=1")
    if int(fields.get("timing_trace_version", "0")) != TIMING_TRACE_VERSION:
        raise RuntimeError(
            f"{role} timing trace version is not {TIMING_TRACE_VERSION}: {info_line}"
        )


def current_loop_delay(info_line: str) -> int | None:
    fields = hw002.parse_key_value_line(info_line, "INFO")
    if fields.get("loop_delay_control") != "1":
        return None
    value = int(fields.get("loop_delay_ms", "-1"))
    if value not in LOOP_DELAY_VALUES:
        raise RuntimeError(f"firmware reports unsupported loop_delay_ms={value}")
    return value


def require_loop_delay_control(info_line: str, role: str) -> int:
    value = current_loop_delay(info_line)
    if value is None:
        raise RuntimeError(f"{role} firmware does not advertise loop_delay_control=1")
    return value


def set_loop_delay(port, value: int) -> int:
    if value not in LOOP_DELAY_VALUES:
        raise ValueError(f"loop delay must be one of {LOOP_DELAY_VALUES}")
    hw002.write_line(port, f"LOOPDELAY {value}")
    actual = parse_loop_delay_line(hw002.wait_prefix(port, "LOOPDELAY ", 3.0))
    if actual != value:
        raise RuntimeError(f"requested LOOPDELAY {value}, firmware confirmed {actual}")
    return actual


def apply_responder_loop_policy(
    initiator_info: str,
    responder_info: str,
    responder_port,
    requested_ms: int | None,
) -> tuple[str, dict[str, int | None]]:
    initiator_ms = current_loop_delay(initiator_info)
    responder_initial_ms = current_loop_delay(responder_info)

    if requested_ms is None:
        return responder_info, {
            "requested_ms": None,
            "applied_ms": responder_initial_ms,
            "responder_initial_ms": responder_initial_ms,
            "initiator_ms": initiator_ms,
        }

    require_loop_delay_control(initiator_info, "initiator")
    require_loop_delay_control(responder_info, "responder")
    set_loop_delay(responder_port, requested_ms)
    responder_info_after = hw002.query_info(responder_port)
    responder_applied_ms = require_loop_delay_control(
        responder_info_after, "responder"
    )
    if responder_applied_ms != requested_ms:
        raise RuntimeError(
            f"responder INFO reports loop_delay_ms={responder_applied_ms}, "
            f"expected {requested_ms}"
        )
    return responder_info_after, {
        "requested_ms": requested_ms,
        "applied_ms": responder_applied_ms,
        "responder_initial_ms": responder_initial_ms,
        "initiator_ms": initiator_ms,
    }


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
        trace = parse_responder_trace(line)
        if trace["sequence"] == sequence and trace["bytes"] == frame_bytes:
            return trace, seen
    return None, seen


def derive_timing(
    measurement: dict[str, Any],
    trace: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not measurement.get("success") or trace is None or trace["state"] != 0:
        return None

    initiator_tx_block_us = int(measurement["tx_block_us"])
    rtt_us = int(measurement["rtt_us"])
    responder_irq_to_tx_start_us = int(trace["irq_to_tx_start_us"])
    responder_tx_block_us = int(trace["tx_block_us"])
    known_local_intervals_us = (
        initiator_tx_block_us
        + responder_irq_to_tx_start_us
        + responder_tx_block_us
    )
    residual_us = rtt_us - known_local_intervals_us

    return {
        "initiator_post_tx_to_rx_complete_us": rtt_us - initiator_tx_block_us,
        "known_local_intervals_us": known_local_intervals_us,
        "rtt_residual_us": residual_us,
        "rtt_residual_note": (
            "Residual after subtracting initiator TX blocking, responder RX-IRQ-to-TX-start, "
            "and responder TX blocking. It combines uninstrumented radio/driver boundaries, "
            "clock tolerance and propagation; it is not a one-way propagation-delay estimate."
        ),
    }


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
        "derived_timing": derive_timing(measurement, trace),
    }


def timing_summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    measurements = [sample["measurement"] for sample in samples]
    base = hw002.summarize_samples(measurements)
    traced = [
        sample
        for sample in samples
        if sample["responder_trace"] is not None
    ]
    successful_timed = [
        sample
        for sample in samples
        if sample["derived_timing"] is not None
    ]

    def trace_values(name: str):
        return (
            sample["responder_trace"][name]
            for sample in successful_timed
        )

    def derived_values(name: str):
        return (
            sample["derived_timing"][name]
            for sample in successful_timed
        )

    base["timing_trace"] = {
        "matched_traces": len(traced),
        "successful_timed_transactions": len(successful_timed),
        "irq_to_handle_us": hw002.numeric_stats(trace_values("irq_to_handle_us")),
        "handle_to_read_done_us": hw002.numeric_stats(
            trace_values("handle_to_read_done_us")
        ),
        "read_done_to_tx_start_us": hw002.numeric_stats(
            trace_values("read_done_to_tx_start_us")
        ),
        "irq_to_tx_start_us": hw002.numeric_stats(
            trace_values("irq_to_tx_start_us")
        ),
        "responder_tx_block_us": hw002.numeric_stats(trace_values("tx_block_us")),
        "irq_to_tx_done_us": hw002.numeric_stats(
            trace_values("irq_to_tx_done_us")
        ),
        "initiator_post_tx_to_rx_complete_us": hw002.numeric_stats(
            derived_values("initiator_post_tx_to_rx_complete_us")
        ),
        "rtt_residual_us": hw002.numeric_stats(
            derived_values("rtt_residual_us")
        ),
    }
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
    responder_loop_delay_ms: int | None,
) -> dict[str, Any]:
    initiator, responder = open_pair(initiator_name, responder_name)
    try:
        initiator_info = hw002.query_info(initiator)
        responder_info = hw002.query_info(responder)
        require_timing_capability(initiator_info, "initiator")
        require_timing_capability(responder_info, "responder")
        responder_info, loop_policy = apply_responder_loop_policy(
            initiator_info,
            responder_info,
            responder,
            responder_loop_delay_ms,
        )
        sample = measure_with_trace(
            initiator, responder, sequence, frame_bytes, timeout_ms
        )
        return {
            "schema": "pollicino-hw002t-single-v1",
            "initiator_port": initiator_name,
            "responder_port": responder_name,
            "initiator_info": initiator_info,
            "responder_info": responder_info,
            "loop_policy": loop_policy,
            "sample": sample,
            "timing_semantics": timing_semantics(),
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
    responder_loop_delay_ms: int | None,
) -> dict[str, Any]:
    initiator, responder = open_pair(initiator_name, responder_name)
    try:
        initiator_info = hw002.query_info(initiator)
        responder_info = hw002.query_info(responder)
        require_timing_capability(initiator_info, "initiator")
        require_timing_capability(responder_info, "responder")
        responder_info, loop_policy = apply_responder_loop_policy(
            initiator_info,
            responder_info,
            responder,
            responder_loop_delay_ms,
        )

        plan = hw002.build_plan(
            initiator,
            (frame_bytes,),
            count,
            tx_occupancy_cap_percent,
        )
        if not execute:
            return {
                "schema": "pollicino-hw002t-plan-v1",
                "executed": False,
                "initiator_port": initiator_name,
                "responder_port": responder_name,
                "initiator_info": initiator_info,
                "responder_info": responder_info,
                "loop_policy": loop_policy,
                "plan": plan,
                "timing_semantics": timing_semantics(),
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
            sequence = index + 1
            sample = measure_with_trace(
                initiator, responder, sequence, frame_bytes, timeout_ms
            )
            sample["host_elapsed_s"] = time.monotonic() - run_started
            samples.append(sample)

        return {
            "schema": "pollicino-hw002t-benchmark-v1",
            "executed": True,
            "initiator_port": initiator_name,
            "responder_port": responder_name,
            "initiator_info": initiator_info,
            "responder_info": responder_info,
            "loop_policy": loop_policy,
            "environment": environment,
            "distance_m": distance_m,
            "timeout_ms": timeout_ms,
            "elapsed_s": time.monotonic() - run_started,
            "plan": plan,
            "samples": samples,
            "summary": timing_summary(samples),
            "timing_semantics": timing_semantics(),
        }
    finally:
        responder.close()
        initiator.close()


def timing_semantics() -> dict[str, str]:
    return {
        "irq_to_handle_us": (
            "Responder-local time from SX1276 RX-done DIO0 callback timestamp to entry "
            "of handleReceivedPacket(). This includes firmware loop/scheduling latency."
        ),
        "handle_to_read_done_us": (
            "Responder-local time from handler entry through packet-length handling and "
            "RadioLib readData() completion."
        ),
        "read_done_to_tx_start_us": (
            "Responder-local time from readData() completion through RSSI/SNR reads, H2 "
            "validation, PONG construction and getTimeOnAir(), up to the responder TX call."
        ),
        "tx_block_us": (
            "Responder-local blocking duration of transmitWithoutRxIsr(), including standby/"
            "driver work and the physical PONG transmission."
        ),
        "rtt_residual_us": (
            "Cross-node residual after subtracting measured local intervals. It is diagnostic "
            "only and must not be interpreted as propagation delay."
        ),
        "loop_policy": (
            "For controlled A/B experiments the responder loop delay may be set to 1 ms "
            "(baseline) or 0 ms (yield-only). The initiator remains at its reset/default policy."
        ),
        "clock_note": (
            "Initiator and responder use independent ESP32 clocks. Only durations measured "
            "within one board are directly timestamped; no absolute cross-board clock "
            "synchronization is assumed."
        ),
        "wire_note": (
            "HW-002T does not change the H2 radio frame layout or HW2_VERSION=1. Timing data "
            "travels only over the responder USB serial log."
        ),
    }


def selftest() -> dict[str, Any]:
    trace = parse_responder_trace(
        "H2RESP seq=7 bytes=42 rssi_dbm=-39.0 snr_db=9.75 toa_us=88000 "
        "state=0 timing_v=1 irq_to_handle_us=700 handle_to_read_done_us=100 "
        "read_done_to_tx_start_us=200 irq_to_tx_start_us=1000 tx_block_us=89700 "
        "irq_to_tx_done_us=90700"
    )
    if trace["sequence"] != 7 or trace["irq_to_tx_done_us"] != 90700:
        raise AssertionError("H2RESP timing parser failed")

    if parse_loop_delay_line("LOOPDELAY ms=0") != 0:
        raise AssertionError("LOOPDELAY parser failed for zero")
    if parse_loop_delay_line("LOOPDELAY ms=1") != 1:
        raise AssertionError("LOOPDELAY parser failed for one")

    measurement = hw002.parse_measurement_line(
        "MRESULT seq=7 bytes=42 success=1 rtt_us=182000 tx_block_us=89700 "
        "toa_us=88000 remote_rssi_dbm=-39.0 remote_snr_db=9.75 "
        "local_rssi_dbm=-38.0 local_snr_db=10.0"
    )
    derived = derive_timing(measurement, trace)
    if derived is None or derived["rtt_residual_us"] != 1600:
        raise AssertionError(f"timing derivation failed: {derived}")

    summary = timing_summary(
        [{
            "measurement": measurement,
            "responder_trace": trace,
            "responder_trace_matched": True,
            "responder_serial_tail": [],
            "derived_timing": derived,
        }]
    )
    if summary["timing_trace"]["matched_traces"] != 1:
        raise AssertionError("timing summary failed")

    return {
        "success": True,
        "trace_parser": True,
        "loop_delay_parser": True,
        "timing_derivation": True,
        "timing_summary": True,
    }


def write_json(result: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PollicinoNet HW-002T dual-port timing trace runner"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("selftest", help="pure host timing parser/derivation self-test")

    measure = sub.add_parser(
        "measure", help="run one H2 ping/pong and correlate responder timing trace"
    )
    measure.add_argument("--initiator-port", required=True)
    measure.add_argument("--responder-port", required=True)
    measure.add_argument("--seq", type=int, default=1)
    measure.add_argument("--bytes", type=int, default=42)
    measure.add_argument("--timeout-ms", type=int, default=3000)
    measure.add_argument(
        "--responder-loop-delay-ms",
        type=int,
        choices=LOOP_DELAY_VALUES,
        help="set responder loop policy after serial reset: 1=baseline delay, 0=yield-only",
    )
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
    bench.add_argument(
        "--responder-loop-delay-ms",
        type=int,
        choices=LOOP_DELAY_VALUES,
        help="set responder loop policy after serial reset: 1=baseline delay, 0=yield-only",
    )
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
            args.responder_loop_delay_ms,
        )
        write_json(result, args.output)
        return 0

    if args.command == "benchmark":
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
            args.responder_loop_delay_ms,
        )
        write_json(result, args.output)
        return 0

    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
