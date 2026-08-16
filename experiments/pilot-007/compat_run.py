from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
P6_RESULTS = ROOT / "experiments/pilot-006/results.json"
RUN = HERE / "run.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("pilot007_runner", RUN)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    original = P6_RESULTS.read_text()
    data = json.loads(original)
    for row in data.get("calgary", []):
        # PILOT-006 persisted bpb/choices but not per-file timings. Temporary
        # placeholders only keep the generic aggregator running; they are
        # replaced with null/blank immediately after the experiment.
        row.setdefault("gate_encode_seconds", 0.0)
        row.setdefault("gate_decode_seconds", 0.0)
    P6_RESULTS.write_text(json.dumps(data, indent=2) + "\n")
    try:
        load_runner().main()
    finally:
        P6_RESULTS.write_text(original)

    results_path = HERE / "output/results.json"
    results = json.loads(results_path.read_text())
    cal = results["calgary_replication"]["aggregate"]
    cal["mean_neural_encode_seconds"] = None
    cal["mean_neural_decode_seconds"] = None
    cal["neural_timing_source"] = "not persisted by PILOT-006; same-run timing comparison is reported on Silesia"
    results_path.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n")

    csv_path = HERE / "output/calgary.csv"
    with csv_path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
        fields = handle.seek(0) or None
    if rows:
        fieldnames = list(rows[0].keys())
        for row in rows:
            row["neural_gate_encode_seconds"] = ""
            row["neural_gate_decode_seconds"] = ""
        with csv_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()
