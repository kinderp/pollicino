#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any


FAILURE_CLASSES = (
    "timeout",
    "crc_mismatch",
    "tx",
    "bad_pong",
    "rx_other",
    "other",
)


def classify_failure(sample: dict[str, Any]) -> str | None:
    if sample.get("success") is True:
        return None

    error = str(sample.get("error", "unknown"))
    state = int(sample.get("state", 0))

    if error == "timeout" or state == -6:
        return "timeout"
    if error == "rx" and state == -7:
        return "crc_mismatch"
    if error == "tx":
        return "tx"
    if error == "bad-pong":
        return "bad_pong"
    if error == "rx":
        return "rx_other"
    return "other"


def summarize_documents(documents: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    events: list[dict[str, Any]] = []
    attempts = 0
    successes = 0

    for source, document in documents:
        samples = document.get("samples")
        if not isinstance(samples, list):
            raise ValueError(f"{source}: expected top-level samples list")

        for sample in samples:
            if not isinstance(sample, dict):
                raise ValueError(f"{source}: sample is not an object")
            attempts += 1
            if sample.get("success") is True:
                successes += 1
                continue

            failure_class = classify_failure(sample)
            assert failure_class is not None
            counts[failure_class] += 1
            events.append(
                {
                    "source": source,
                    "sequence": sample.get("sequence"),
                    "bytes": sample.get("bytes"),
                    "error": sample.get("error"),
                    "state": sample.get("state"),
                    "failure_class": failure_class,
                    "rtt_us": sample.get("rtt_us"),
                    "tx_block_us": sample.get("tx_block_us"),
                    "toa_us": sample.get("toa_us"),
                }
            )

    failures = attempts - successes
    return {
        "schema": "pollicino-hw002-failure-summary-v1",
        "attempts": attempts,
        "successes": successes,
        "failures": failures,
        "success_rate": successes / attempts if attempts else None,
        "failure_rate": failures / attempts if attempts else None,
        "failure_classes": {name: counts[name] for name in FAILURE_CLASSES},
        "events": events,
        "interpretation_note": (
            "Failure classes describe initiator-observed outcomes only. A timeout cannot "
            "distinguish a lost PING from a lost PONG or another receive-path event. A "
            "CRC mismatch proves that a CRC-invalid LoRa frame was detected during the "
            "receive window, but not by itself that it was the expected H2 PONG."
        ),
    }


def selftest() -> dict[str, Any]:
    document = {
        "samples": [
            {"success": True, "sequence": 1, "bytes": 42},
            {
                "success": False,
                "sequence": 2,
                "bytes": 42,
                "error": "timeout",
                "state": -6,
            },
            {
                "success": False,
                "sequence": 3,
                "bytes": 42,
                "error": "rx",
                "state": -7,
            },
            {
                "success": False,
                "sequence": 4,
                "bytes": 42,
                "error": "bad-pong",
                "state": 0,
            },
        ]
    }
    result = summarize_documents([("selftest", document)])
    expected = {
        "timeout": 1,
        "crc_mismatch": 1,
        "tx": 0,
        "bad_pong": 1,
        "rx_other": 0,
        "other": 0,
    }
    if result["failure_classes"] != expected:
        raise AssertionError(result)
    if result["attempts"] != 4 or result["successes"] != 1:
        raise AssertionError(result)
    return {"success": True, "failure_classes": True, "aggregation": True}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classify failure outcomes in frozen HW-002 benchmark JSON files"
    )
    parser.add_argument("inputs", nargs="*", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        print(json.dumps(selftest(), indent=2, sort_keys=True))
        return 0
    if not args.inputs:
        parser.error("provide at least one benchmark JSON or use --selftest")

    documents: list[tuple[str, dict[str, Any]]] = []
    for path in args.inputs:
        documents.append((str(path), json.loads(path.read_text(encoding="utf-8"))))

    result = summarize_documents(documents)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
