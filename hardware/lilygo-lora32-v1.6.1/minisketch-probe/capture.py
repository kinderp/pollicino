from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
import time

import serial


def _parse_kv(line: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for token in line.split()[1:]:
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        result[key] = value
    return result


def _as_number(value: str):
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def capture(port: str, *, baud: int, timeout_s: float) -> dict[str, object]:
    started = time.time()
    ready: dict[str, object] | None = None
    boot_heap: dict[str, object] | None = None
    results: list[dict[str, object]] = []
    cleanups: list[dict[str, object]] = []
    failures: list[str] = []
    raw_lines: list[str] = []

    with serial.Serial(port, baudrate=baud, timeout=1.0) as ser:
        ser.reset_input_buffer()
        # Most ESP32 USB serial adapters reset on DTR; wait for the fresh boot.
        ser.dtr = False
        time.sleep(0.1)
        ser.dtr = True

        while time.time() - started < timeout_s:
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            print(line)
            raw_lines.append(line)

            if line.startswith("MSP_READY "):
                ready = {key: _as_number(value) for key, value in _parse_kv(line).items()}
            elif line.startswith("MSP_BOOT_HEAP "):
                boot_heap = {key: _as_number(value) for key, value in _parse_kv(line).items()}
            elif line.startswith("MSP_RESULT "):
                results.append({key: _as_number(value) for key, value in _parse_kv(line).items()})
            elif line.startswith("MSP_CLEANUP "):
                cleanups.append({key: _as_number(value) for key, value in _parse_kv(line).items()})
            elif line.startswith("MSP_FAIL ") or line.startswith("MSP_FATAL "):
                failures.append(line)
            elif line == "MSP_DONE":
                break
        else:
            failures.append("capture timeout before MSP_DONE")

    by_capacity: dict[int, list[dict[str, object]]] = defaultdict(list)
    for item in results:
        by_capacity[int(item["capacity"])].append(item)

    summaries = []
    timing_fields = (
        "receiver_create_us",
        "receiver_build_us",
        "serialize_us",
        "source_create_us",
        "source_build_us",
        "merge_us",
        "decode_us",
    )
    for capacity, items in sorted(by_capacity.items()):
        summary: dict[str, object] = {
            "capacity": capacity,
            "trials": len(items),
            "exact_trials": sum(int(item.get("exact", 0)) == 1 for item in items),
            "decoded_counts": sorted({int(item["decoded"]) for item in items}),
            "serialized_bytes": sorted({int(item["serialized"]) for item in items}),
            "minimum_reported_free_heap": min(int(item["min_free"]) for item in items),
            "minimum_largest_free_block_after_decode": min(
                int(item["largest_after_decode"]) for item in items
            ),
        }
        for field in timing_fields:
            values = [int(item[field]) for item in items]
            summary[f"{field}_median"] = statistics.median(values)
            summary[f"{field}_min"] = min(values)
            summary[f"{field}_max"] = max(values)
        summaries.append(summary)

    cleanup_deltas = [int(item.get("delta", 0)) for item in cleanups]
    success = (
        not failures
        and ready is not None
        and boot_heap is not None
        and len(results) == 15
        and len(cleanups) == 15
        and all(int(item.get("exact", 0)) == 1 for item in results)
        and set(by_capacity) == {20, 21, 32}
        and all(len(items) == 5 for items in by_capacity.values())
        and all(abs(value) <= 32 for value in cleanup_deltas)
    )
    return {
        "schema": "pollicino-minisketch-esp32-runtime-probe-v1",
        "success": success,
        "captured_at_unix_s": int(time.time()),
        "port": port,
        "baud": baud,
        "ready": ready,
        "boot_heap": boot_heap,
        "capacity_summaries": summaries,
        "cleanup_delta_bytes": cleanup_deltas,
        "failures": failures,
        "raw_lines": raw_lines,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = capture(args.port, baud=args.baud, timeout_s=args.timeout)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
        print(f"wrote {args.output}")
    print(encoded, end="")
    raise SystemExit(0 if report["success"] else 2)


if __name__ == "__main__":
    main()
