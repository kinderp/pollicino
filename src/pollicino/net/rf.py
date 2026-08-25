from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class RFEvidence:
    """Normalized summary of one physical RF evidence record.

    Evidence records are intentionally file-scoped. ``catalog_rf_paths`` does
    not add attempts across records because historical summaries can overlap
    with raw runs or with other derived summaries.
    """

    source: str
    lab: str
    schema: str
    environment: str | None
    checkpoint: str | None
    direction: str | None
    frame_bytes: int | None
    tx_power_dbm: float | None
    attempts: int
    successes: int
    failures: int
    crc_events: int | None = None
    local_rssi_dbm_mean: float | None = None
    remote_rssi_dbm_mean: float | None = None
    local_snr_db_mean: float | None = None
    remote_snr_db_mean: float | None = None
    rtt_us_mean: float | None = None
    irq_to_handle_us_mean: float | None = None
    derived_from: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.attempts < 0 or self.successes < 0 or self.failures < 0:
            raise ValueError("attempt counts must be non-negative")
        if self.successes + self.failures != self.attempts:
            raise ValueError("successes + failures must equal attempts")
        if self.crc_events is not None and self.crc_events < 0:
            raise ValueError("crc_events must be non-negative")

    @property
    def success_rate(self) -> float | None:
        if self.attempts == 0:
            return None
        return self.successes / self.attempts

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["success_rate"] = self.success_rate
        return result


@dataclass(frozen=True, slots=True)
class RFTraceSample:
    """One ordered physical radio transaction suitable for deterministic replay."""

    sequence: int
    success: bool
    failure_class: str | None
    frame_bytes: int | None = None
    local_rssi_dbm: float | None = None
    remote_rssi_dbm: float | None = None
    local_snr_db: float | None = None
    remote_snr_db: float | None = None
    rtt_us: float | None = None
    toa_us: int | None = None

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("sequence must be >= 1")
        if self.success and self.failure_class not in {None, "success"}:
            raise ValueError("successful samples cannot carry a failure class")


@dataclass(frozen=True, slots=True)
class RFReplayTrace:
    source: str
    lab: str
    schema: str
    checkpoint: str | None
    environment: str | None
    samples: tuple[RFTraceSample, ...]

    @property
    def successes(self) -> int:
        return sum(sample.success for sample in self.samples)

    @property
    def failures(self) -> int:
        return len(self.samples) - self.successes

    @property
    def failure_classes(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for sample in self.samples:
            if sample.success:
                continue
            key = sample.failure_class or "other_failure"
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))

    def replay(self, count: int | None = None, *, repeat: bool = False) -> tuple[RFTraceSample, ...]:
        """Return a deterministic replay sequence without inventing observations.

        By default replay cannot consume more samples than were physically
        recorded. ``repeat=True`` is explicit synthetic reuse and is therefore
        opt-in.
        """

        if count is None:
            count = len(self.samples)
        if count < 0:
            raise ValueError("count must be non-negative")
        if count == 0:
            return ()
        if not self.samples:
            raise ValueError("cannot replay an empty physical trace")
        if not repeat and count > len(self.samples):
            raise ValueError(
                f"requested {count} samples but trace contains only {len(self.samples)}; "
                "use repeat=True only for explicit synthetic reuse"
            )
        if not repeat:
            return self.samples[:count]
        return tuple(self.samples[index % len(self.samples)] for index in range(count))

    def to_dict(self, *, include_samples: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {
            "source": self.source,
            "lab": self.lab,
            "schema": self.schema,
            "checkpoint": self.checkpoint,
            "environment": self.environment,
            "sample_count": len(self.samples),
            "successes": self.successes,
            "failures": self.failures,
            "failure_classes": self.failure_classes,
        }
        if include_samples:
            result["samples"] = [asdict(sample) for sample in self.samples]
        return result


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _metric_mean(container: Any, key: str) -> float | None:
    value = _mapping(container).get(key)
    if isinstance(value, Mapping):
        value = value.get("mean")
    return _float(value)


def _lab(record: Mapping[str, Any], schema: str) -> str:
    explicit = record.get("lab")
    if explicit:
        return str(explicit).upper()
    lowered = schema.lower()
    labels = {
        "hw006": "HW-006",
        "hw005": "HW-005",
        "hw004": "HW-004",
        "hw003": "HW-003",
        "hw002t": "HW-002T",
        "hw002": "HW-002",
        "hw001": "HW-001",
    }
    for token, label in labels.items():
        if token in lowered:
            return label
    return "UNKNOWN"


def _power(record: Mapping[str, Any]) -> float | None:
    for container_name in ("phy", "radio_profile"):
        container = _mapping(record.get(container_name))
        for key in ("tx_power_dbm", "power_dbm"):
            if container.get(key) is not None:
                return float(container[key])
    measurement_info = record.get("local_measurement_info")
    if isinstance(measurement_info, str):
        for token in measurement_info.split():
            if token.startswith("power_dbm="):
                return float(token.split("=", 1)[1])
    return None


def _frame_bytes(record: Mapping[str, Any]) -> int | None:
    if record.get("frame_bytes") is not None:
        return int(record["frame_bytes"])
    radio = _mapping(record.get("radio_profile"))
    if radio.get("frame_bytes_each_direction") is not None:
        return int(radio["frame_bytes_each_direction"])
    return None


def _derived_from(record: Mapping[str, Any]) -> tuple[str, ...]:
    values: list[str] = []
    for key in ("raw_source_artifact", "source_record"):
        value = record.get(key)
        if isinstance(value, str):
            values.append(value)
    directions = record.get("directions")
    if isinstance(directions, Sequence) and not isinstance(directions, (str, bytes)):
        for direction in directions:
            value = _mapping(direction).get("source_record")
            if isinstance(value, str):
                values.append(value)
    return tuple(dict.fromkeys(values))


def normalize_rf_evidence(record: Mapping[str, Any], *, source: str = "<memory>") -> RFEvidence | None:
    """Normalize one supported physical evidence record.

    Unsupported JSON is ignored rather than guessed. This is important because
    the physical-validation directory intentionally contains raw captures,
    analysis notes and derived summaries with overlapping provenance.
    """

    schema = str(record.get("schema", ""))
    lab = _lab(record, schema)

    if schema == "pollicino-hw006-preflight-v1":
        return None

    if schema == "pollicino-hw006-checkpoint-v1":
        if not record.get("executed"):
            return None
        summary = _mapping(record.get("summary"))
        attempts = int(summary.get("attempts", 0))
        successes = int(summary.get("successes", 0))
        failures = attempts - successes
        return RFEvidence(
            source=source,
            lab="HW-006",
            schema=schema,
            environment=record.get("environment"),
            checkpoint=record.get("checkpoint"),
            direction=None,
            frame_bytes=_frame_bytes(record),
            tx_power_dbm=_power(record) or 2.0,
            attempts=attempts,
            successes=successes,
            failures=failures,
            local_rssi_dbm_mean=_float(summary.get("local_rssi_dbm_mean")),
            remote_rssi_dbm_mean=_float(summary.get("remote_rssi_dbm_mean")),
            local_snr_db_mean=_float(summary.get("local_snr_db_mean")),
            remote_snr_db_mean=_float(summary.get("remote_snr_db_mean")),
            rtt_us_mean=_float(summary.get("rtt_us_mean")),
        )

    if schema == "pollicino-hw002-benchmark-v1":
        summary = _mapping(record.get("summary"))
        attempts = int(summary.get("attempts", len(record.get("samples", ()))))
        successes = int(summary.get("successes", 0))
        failures = int(summary.get("failures", attempts - successes))
        return RFEvidence(
            source=source,
            lab="HW-002",
            schema=schema,
            environment=record.get("environment"),
            checkpoint=None,
            direction=str(record.get("port")) if record.get("port") else None,
            frame_bytes=_frame_bytes(record)
            or (
                int(record["samples"][0]["bytes"])
                if isinstance(record.get("samples"), list) and record["samples"]
                else None
            ),
            tx_power_dbm=_power(record) or 10.0,
            attempts=attempts,
            successes=successes,
            failures=failures,
            local_rssi_dbm_mean=_metric_mean(summary, "local_rssi_dbm"),
            remote_rssi_dbm_mean=_metric_mean(summary, "remote_rssi_dbm"),
            local_snr_db_mean=_metric_mean(summary, "local_snr_db"),
            remote_snr_db_mean=_metric_mean(summary, "remote_snr_db"),
            rtt_us_mean=_metric_mean(summary, "rtt_us"),
        )

    if schema == "pollicino-hw002-bidirectional-summary-v1":
        runs = record.get("runs")
        if not isinstance(runs, list):
            return None
        attempts = len(runs)
        successes = sum(bool(_mapping(run).get("success")) for run in runs)
        derived = _mapping(record.get("derived"))
        return RFEvidence(
            source=source,
            lab="HW-002",
            schema=schema,
            environment="same-bench-indoor",
            checkpoint=None,
            direction="bidirectional",
            frame_bytes=_frame_bytes(record),
            tx_power_dbm=_power(record),
            attempts=attempts,
            successes=successes,
            failures=attempts - successes,
            local_rssi_dbm_mean=_float(derived.get("b_to_a_rssi_mean_dbm")),
            remote_rssi_dbm_mean=_float(derived.get("a_to_b_rssi_mean_dbm")),
            local_snr_db_mean=_float(derived.get("b_to_a_snr_mean_db")),
            remote_snr_db_mean=_float(derived.get("a_to_b_snr_mean_db")),
            rtt_us_mean=_float(derived.get("rtt_mean_us")),
        )

    if schema == "pollicino-hw003-physical-summary-v1":
        result = _mapping(record.get("result"))
        attempts = int(result.get("attempts", record.get("count", 0)))
        successes = int(result.get("successes", 0))
        return RFEvidence(
            source=source,
            lab="HW-003",
            schema=schema,
            environment=record.get("environment"),
            checkpoint=None,
            direction=record.get("direction"),
            frame_bytes=_frame_bytes(record),
            tx_power_dbm=_power(record),
            attempts=attempts,
            successes=successes,
            failures=attempts - successes,
            local_rssi_dbm_mean=_metric_mean(result, "local_rssi_dbm"),
            remote_rssi_dbm_mean=_metric_mean(result, "remote_rssi_dbm"),
            local_snr_db_mean=_metric_mean(result, "local_snr_db"),
            remote_snr_db_mean=_metric_mean(result, "remote_snr_db"),
            rtt_us_mean=_metric_mean(result, "rtt_us"),
            irq_to_handle_us_mean=_metric_mean(result, "irq_to_handle_us"),
            derived_from=_derived_from(record),
        )

    if schema == "pollicino-hw004-physical-summary-v1":
        overall = _mapping(record.get("overall"))
        attempts = int(overall.get("attempts", 0))
        successes = int(overall.get("successes", 0))
        return RFEvidence(
            source=source,
            lab="HW-004",
            schema=schema,
            environment=record.get("environment"),
            checkpoint=None,
            direction="bidirectional",
            frame_bytes=None,
            tx_power_dbm=_power(record),
            attempts=attempts,
            successes=successes,
            failures=int(overall.get("failures", attempts - successes)),
            crc_events=_int(overall.get("crc_events")),
            irq_to_handle_us_mean=_metric_mean(overall, "irq_to_handle_us"),
        )

    if schema == "pollicino-hw005-physical-summary-v1":
        attempts = int(record.get("attempts", 0))
        successes = int(record.get("successes", 0))
        return RFEvidence(
            source=source,
            lab="HW-005",
            schema=schema,
            environment=record.get("environment"),
            checkpoint=None,
            direction="bidirectional",
            frame_bytes=_frame_bytes(record),
            tx_power_dbm=None,
            attempts=attempts,
            successes=successes,
            failures=int(record.get("failures", attempts - successes)),
            irq_to_handle_us_mean=_metric_mean(record, "irq_to_handle_us"),
        )

    if lab == "HW-001" and record.get("status") == "PASS":
        directions = record.get("directions")
        if not isinstance(directions, list):
            return None
        attempts = 0
        successes = 0
        rssi: list[float] = []
        snr: list[float] = []
        for direction in directions:
            item = _mapping(direction)
            for payload_name in ("pnd1", "pnf1"):
                payload = _mapping(item.get(payload_name))
                if not payload:
                    continue
                attempts += 1
                successes += bool(payload.get("exact"))
                if payload.get("rssi_dbm") is not None:
                    rssi.append(float(payload["rssi_dbm"]))
                if payload.get("snr_db") is not None:
                    snr.append(float(payload["snr_db"]))
        return RFEvidence(
            source=source,
            lab="HW-001",
            schema=schema or "pollicino-hw001-bidirectional-summary-v1",
            environment="same-bench-indoor",
            checkpoint=None,
            direction="bidirectional",
            frame_bytes=None,
            tx_power_dbm=_power(record),
            attempts=attempts,
            successes=successes,
            failures=attempts - successes,
            remote_rssi_dbm_mean=(sum(rssi) / len(rssi)) if rssi else None,
            remote_snr_db_mean=(sum(snr) / len(snr)) if snr else None,
            derived_from=_derived_from(record),
        )

    return None


def extract_rf_trace(record: Mapping[str, Any], *, source: str = "<memory>") -> RFReplayTrace | None:
    """Extract ordered per-attempt observations when the source really has them."""

    schema = str(record.get("schema", ""))

    if schema == "pollicino-hw002-benchmark-v1":
        raw_samples = record.get("samples")
        if not isinstance(raw_samples, list):
            return None
        samples = tuple(
            RFTraceSample(
                sequence=int(sample.get("sequence", index + 1)),
                success=bool(sample.get("success")),
                failure_class=None if sample.get("success") else str(sample.get("error", "other_failure")),
                frame_bytes=_int(sample.get("bytes")),
                local_rssi_dbm=_float(sample.get("local_rssi_dbm")),
                remote_rssi_dbm=_float(sample.get("remote_rssi_dbm")),
                local_snr_db=_float(sample.get("local_snr_db")),
                remote_snr_db=_float(sample.get("remote_snr_db")),
                rtt_us=_float(sample.get("rtt_us")),
                toa_us=_int(sample.get("toa_us")),
            )
            for index, sample_value in enumerate(raw_samples)
            for sample in (_mapping(sample_value),)
        )
        return RFReplayTrace(
            source=source,
            lab="HW-002",
            schema=schema,
            checkpoint=None,
            environment=record.get("environment"),
            samples=samples,
        )

    if schema == "pollicino-hw006-checkpoint-v1" and record.get("executed"):
        raw_attempts = record.get("attempts")
        if not isinstance(raw_attempts, list):
            return None
        samples_list: list[RFTraceSample] = []
        for index, attempt_value in enumerate(raw_attempts):
            attempt = _mapping(attempt_value)
            measurement = _mapping(attempt.get("measurement"))
            success = bool(measurement.get("success"))
            failure_class = None if success else str(
                attempt.get("failure_class") or measurement.get("error") or "other_failure"
            )
            samples_list.append(
                RFTraceSample(
                    sequence=int(attempt.get("sequence", index + 1)),
                    success=success,
                    failure_class=failure_class,
                    frame_bytes=_int(measurement.get("bytes") or record.get("frame_bytes")),
                    local_rssi_dbm=_float(measurement.get("local_rssi_dbm")),
                    remote_rssi_dbm=_float(measurement.get("remote_rssi_dbm")),
                    local_snr_db=_float(measurement.get("local_snr_db")),
                    remote_snr_db=_float(measurement.get("remote_snr_db")),
                    rtt_us=_float(measurement.get("rtt_us")),
                    toa_us=_int(measurement.get("toa_us") or _mapping(record.get("plan")).get("toa_us_per_frame")),
                )
            )
        return RFReplayTrace(
            source=source,
            lab="HW-006",
            schema=schema,
            checkpoint=record.get("checkpoint"),
            environment=record.get("environment"),
            samples=tuple(samples_list),
        )

    return None


def iter_json_paths(paths: Iterable[str | Path]) -> tuple[Path, ...]:
    files: list[Path] = []
    for value in paths:
        path = Path(value)
        if path.is_dir():
            files.extend(candidate for candidate in path.rglob("*.json") if candidate.is_file())
        elif path.is_file() and path.suffix.lower() == ".json":
            files.append(path)
    return tuple(sorted(dict.fromkeys(files)))


def catalog_rf_paths(paths: Iterable[str | Path]) -> dict[str, Any]:
    """Catalog RF evidence and replay traces without unsafe cross-file summing."""

    evidence: list[RFEvidence] = []
    traces: list[RFReplayTrace] = []
    ignored: list[str] = []
    invalid: list[dict[str, str]] = []
    observed_frame_sizes: set[int] = set()
    observed_power_levels: set[float] = set()
    files = iter_json_paths(paths)

    for path in files:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(record, Mapping):
                raise ValueError("top-level JSON value is not an object")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            invalid.append({"source": str(path), "error": str(exc)})
            continue

        normalized = normalize_rf_evidence(record, source=str(path))
        trace = extract_rf_trace(record, source=str(path))

        direct_frame = _frame_bytes(record)
        if direct_frame is not None:
            observed_frame_sizes.add(direct_frame)
        design = _mapping(record.get("design"))
        for value in design.get("sizes_bytes", ()) if isinstance(design.get("sizes_bytes"), list) else ():
            observed_frame_sizes.add(int(value))
        plan = _mapping(record.get("plan"))
        sizes = plan.get("sizes")
        if isinstance(sizes, list):
            for item in sizes:
                value = _mapping(item).get("frame_bytes")
                if value is not None:
                    observed_frame_sizes.add(int(value))

        direct_power = _power(record)
        if direct_power is not None:
            observed_power_levels.add(direct_power)
        powers = record.get("powers_dbm")
        if isinstance(powers, list):
            observed_power_levels.update(float(value) for value in powers)

        if normalized is not None:
            evidence.append(normalized)
        if trace is not None:
            traces.append(trace)
        if normalized is None and trace is None:
            ignored.append(str(path))

    labs = sorted({item.lab for item in evidence} | {trace.lab for trace in traces})
    schemas = sorted({item.schema for item in evidence} | {trace.schema for trace in traces})
    frame_sizes = sorted(
        observed_frame_sizes
        | {
            size
            for item in evidence
            for size in (item.frame_bytes,)
            if size is not None
        }
        | {
            sample.frame_bytes
            for trace in traces
            for sample in trace.samples
            if sample.frame_bytes is not None
        }
    )
    power_levels = sorted(
        observed_power_levels
        | {item.tx_power_dbm for item in evidence if item.tx_power_dbm is not None}
    )
    checkpoints = sorted(
        {
            checkpoint
            for checkpoint in (
                *(item.checkpoint for item in evidence),
                *(trace.checkpoint for trace in traces),
            )
            if checkpoint
        }
    )

    return {
        "schema": "pollicino-rf-evidence-catalog-v1",
        "files_seen": len(files),
        "evidence_records": len(evidence),
        "replay_traces": len(traces),
        "ignored_files": ignored,
        "invalid_files": invalid,
        "coverage": {
            "labs": labs,
            "schemas": schemas,
            "frame_bytes": frame_sizes,
            "tx_power_dbm": power_levels,
            "checkpoints": checkpoints,
        },
        "scientific_boundary": (
            "Attempts are not summed across catalog records because historical raw runs and "
            "derived summaries can overlap. Select explicitly disjoint evidence before computing "
            "an aggregate packet-loss estimate."
        ),
        "evidence": [item.to_dict() for item in evidence],
        "traces": [trace.to_dict() for trace in traces],
    }


def _write_json(payload: Mapping[str, Any], output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    print(text)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Catalog Pollicino physical RF evidence and deterministic replay traces"
    )
    parser.add_argument("paths", nargs="+", help="JSON file or directory to scan recursively")
    parser.add_argument("--output", help="optional JSON catalog output path")
    args = parser.parse_args(argv)

    result = catalog_rf_paths(args.paths)
    _write_json(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
