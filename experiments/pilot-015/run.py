from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
P14_HERE = ROOT / "experiments/pilot-014"
sys.path.insert(0, str(ROOT / "src"))

from pollicino.compression.admission_routing import (
    AdmissionBudgetState,
    CheapAdmissionDecisionTree,
    DecisionTreeNode,
    RichCheapAdmissionBlockCDFProvider,
    admission_rule_from_dict,
    extract_cheap_admission_features,
    rich_cheap_admission_decision,
    rich_cheap_admission_fingerprint,
)
from pollicino.compression.codec import decode_pol


EXPERIMENT_ID = "pilot-015-longer-cheap-horizon"
PILOT014_FINAL_SHA = "91276bcdf9211a70605e11ee61fb713b16924f2b"
PILOT014_POLICY_DIGEST = "02cb5a4fd9fb2d3695af55a874aff6ad2a4b49599af9d396878ef7cde116aa85"
FROZEN_IMPLEMENTATION_SHA = "e1c392527aaf3535bc2578b43d878291d6e78482"
MODEL_FINGERPRINT = "354daf36f94207a6ff2aa0b9c91b1849c8fe47758fad07cb819bc57edd823117"
CHECKPOINT_SHA256 = "713aebe2b3bac94931060ff4fa09b3174b033d44913d43354f27ec2a568f7ff7"
STREAM_BYTES = 4096
BLOCK_BYTES = 512
P14_PROBE_BYTES = 16
P15_PROBE_BYTES = 32
MAX_ADMITTED_BYTES = 2048
THRESHOLD_CANDIDATES = (20, 22, 24, 26, 28, 30)
RETAINED_GAIN_SUCCESS = 0.50
P14_RULE_THRESHOLD = 12


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_p14():
    return load_module(P14_HERE / "run.py", "pilot014_for_pilot015")


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def current_git_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def csvout(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def threshold_rule(threshold: int) -> CheapAdmissionDecisionTree:
    """Return the only selector family allowed in PILOT-015."""
    if int(threshold) not in THRESHOLD_CANDIDATES:
        raise ValueError("threshold is outside the preregistered PILOT-015 grid")
    return CheapAdmissionDecisionTree(
        (
            DecisionTreeNode(
                feature="unique_count",
                threshold=int(threshold),
                less_equal=1,
                greater=2,
            ),
            DecisionTreeNode(value=1),
            DecisionTreeNode(value=0),
        ),
        threshold=1,
    )


def always_admit_rule() -> CheapAdmissionDecisionTree:
    return CheapAdmissionDecisionTree(
        (
            DecisionTreeNode(
                feature="unique_count", threshold=32, less_equal=1, greater=2
            ),
            DecisionTreeNode(value=1),
            DecisionTreeNode(value=0),
        ),
        threshold=1,
    )


def validate_p14_policy(p14):
    document, rule = p14.load_frozen_policy(P14_HERE / "frozen-policy.json")
    if document["policy_digest"] != PILOT014_POLICY_DIGEST:
        raise RuntimeError("K. INHERITED_PILOT014_CORRECTNESS_BUG: policy digest drift")
    expected_rule = {
        "type": "decision-tree",
        "threshold": 1,
        "nodes": [
            {
                "feature": "unique_count",
                "threshold": P14_RULE_THRESHOLD,
                "less_equal": 1,
                "greater": 2,
            },
            {"value": 1},
            {"value": 0},
        ],
    }
    if rule.to_dict() != expected_rule:
        raise RuntimeError("K. INHERITED_PILOT014_CORRECTNESS_BUG: policy rule drift")
    if document["policy"]["checkpoint"]["canonical_model_fingerprint"] != MODEL_FINGERPRINT:
        raise RuntimeError("K. INHERITED_PILOT014_CORRECTNESS_BUG: model drift")
    if document["policy"]["checkpoint"]["checkpoint_sha256"] != CHECKPOINT_SHA256:
        raise RuntimeError("K. INHERITED_PILOT014_CORRECTNESS_BUG: checkpoint drift")
    return document, rule


def horizon_fingerprint(p14, context, rule, stream_bytes: int, probe_bytes: int) -> bytes:
    return rich_cheap_admission_fingerprint(
        cheap_fingerprint=context.cheap_fp,
        specialist_fingerprint=context.neural_gate_fp,
        stream_bytes=stream_bytes,
        block_bytes=BLOCK_BYTES,
        probe_bytes=probe_bytes,
        rule=rule,
        max_admitted_bytes=min(MAX_ADMITTED_BYTES, stream_bytes),
    )


def run_horizon(p14, context, data: bytes, rule, *, probe_bytes: int, verify: bool) -> dict:
    tracker = p14.TrackingNeuralFactory(context)
    provider = RichCheapAdmissionBlockCDFProvider(
        context.cheap_factory,
        tracker,
        rule,
        stream_bytes=len(data),
        block_bytes=BLOCK_BYTES,
        probe_bytes=probe_bytes,
        max_admitted_bytes=min(MAX_ADMITTED_BYTES, len(data)),
        cheap_name="cheap-gate",
        specialist_name="neural-gate",
    )
    fingerprint = horizon_fingerprint(p14, context, rule, len(data), probe_bytes)
    encoded = p14.encode_only(data, provider, fingerprint)
    result = {
        **{key: value for key, value in encoded.items() if key != "blob"},
        "model_evaluations": tracker.model_evaluations,
        "model_eval_fraction": tracker.model_evaluations / len(data),
        "neural_cache_hits": tracker.cache_hits,
        "admitted_blocks": provider.admitted_blocks,
        "admitted_bytes": provider.admitted_bytes,
        "admitted_byte_fraction": provider.admitted_byte_fraction,
        "specialist_output_calls": provider.specialist_output_calls,
        "block_summary": provider.block_summary(),
    }
    if verify:
        decoder_tracker = p14.TrackingNeuralFactory(context)
        decoder = RichCheapAdmissionBlockCDFProvider(
            context.cheap_factory,
            decoder_tracker,
            rule,
            stream_bytes=len(data),
            block_bytes=BLOCK_BYTES,
            probe_bytes=probe_bytes,
            max_admitted_bytes=min(MAX_ADMITTED_BYTES, len(data)),
            cheap_name="cheap-gate",
            specialist_name="neural-gate",
        )
        restored = decode_pol(
            encoded["blob"],
            shared_provider=decoder,
            expected_model_fingerprint=fingerprint,
        )
        result["roundtrip"] = restored == data
        result["sha256_match"] = sha256(restored) == sha256(data)
        if not result["roundtrip"] or not result["sha256_match"]:
            raise RuntimeError("PILOT-015 exact roundtrip failed")
        if provider.block_summary() != decoder.block_summary():
            raise RuntimeError("D. SEARCH_CODEC_DECISION_DIVERGENCE")
        if tracker.model_evaluations != decoder_tracker.model_evaluations:
            raise RuntimeError("E. NEURAL_COMPUTE_ACCOUNTING_ERROR")
    return result


def simulate_routes(context, streams: dict[str, bytes], rule, *, probe_bytes: int) -> list[dict]:
    rows: list[dict] = []
    for stream_name, data in streams.items():
        spent = 0
        for block_index, start in enumerate(range(0, len(data), BLOCK_BYTES)):
            block = data[start : start + BLOCK_BYTES]
            features = extract_cheap_admission_features(
                context.cheap_factory, block[:probe_bytes]
            )
            decision = rich_cheap_admission_decision(
                features,
                rule,
                AdmissionBudgetState(spent, min(MAX_ADMITTED_BYTES, len(data))),
                len(block),
            )
            if decision.admitted:
                spent += len(block)
            rows.append(
                {
                    "stream": stream_name,
                    "block_index": block_index,
                    "unique_count": features.unique_count,
                    "score": decision.score,
                    "rule_match": decision.rule_match,
                    "budget_allows": decision.budget_allows,
                    "admitted": decision.admitted,
                }
            )
    return rows


def compare_routes(simulated: list[dict], actual: dict[str, dict]) -> int:
    expected = {
        (row["stream"], int(row["block_index"])): bool(row["admitted"])
        for row in simulated
    }
    mismatches = 0
    for stream_name, result in actual.items():
        for row in result["block_summary"]:
            mismatches += bool(row["admitted"]) != expected[
                (stream_name, int(row["block_index"]))
            ]
    return mismatches


def reproduce_predecessors(p14, context, streams: dict[str, bytes], p14_rule) -> dict:
    names = p14.VALIDATION_STREAMS
    p13 = {name: p14.run_p13(context, streams[name], verify=True) for name in names}
    p14_actual = {
        name: p14.run_rich(context, streams[name], p14_rule, verify=True)
        for name in names
    }
    p13_mean_bpb = mean(row["payload_bpb"] for row in p13.values())
    p13_mean_eval = mean(row["model_eval_fraction"] for row in p13.values())
    p14_mean_bpb = mean(row["payload_bpb"] for row in p14_actual.values())
    p14_mean_eval = mean(row["model_eval_fraction"] for row in p14_actual.values())
    frozen = json.loads((P14_HERE / "frozen-policy.json").read_text())["development"]
    expected = {
        "p13_mean_bpb": float(frozen["p13_validation_actual_mean_payload_bpb"]),
        "p13_mean_eval": float(frozen["p13_validation_actual_mean_model_eval_fraction"]),
        "p14_mean_bpb": float(frozen["reproduction"]["validation_actual_mean_payload_bpb"]),
        "p14_mean_eval": float(
            frozen["reproduction"]["validation_actual_mean_model_eval_fraction"]
        ),
    }
    observed = {
        "p13_mean_bpb": p13_mean_bpb,
        "p13_mean_eval": p13_mean_eval,
        "p14_mean_bpb": p14_mean_bpb,
        "p14_mean_eval": p14_mean_eval,
    }
    if observed != expected:
        raise RuntimeError(
            "K. INHERITED_PILOT014_CORRECTNESS_BUG: development reproduction drift "
            f"expected={expected!r} observed={observed!r}"
        )
    return {
        "streams": list(names),
        "p13_rule": "88 <= ceil(probe codelength bits) <= 128",
        "p14_rule": "unique_count_16 <= 12",
        "p14_policy_digest": PILOT014_POLICY_DIGEST,
        **observed,
    }


def evaluate_thresholds(p14, context, streams: dict[str, bytes]) -> tuple[list[dict], dict, dict]:
    candidates: list[dict] = []
    actual_by_threshold: dict[int, dict[str, dict]] = {}
    for threshold in THRESHOLD_CANDIDATES:
        rule = threshold_rule(threshold)
        actual = {
            name: run_horizon(
                p14, context, data, rule, probe_bytes=P15_PROBE_BYTES, verify=True
            )
            for name, data in streams.items()
        }
        actual_by_threshold[threshold] = actual
        simulated = simulate_routes(
            context, streams, rule, probe_bytes=P15_PROBE_BYTES
        )
        mismatches = compare_routes(simulated, actual)
        max_eval = max(row["model_eval_fraction"] for row in actual.values())
        budget_violations = sum(
            row["model_eval_fraction"] > 0.5 + 1e-12 for row in actual.values()
        )
        candidate = {
            "threshold": threshold,
            "mean_payload_bpb": mean(row["payload_bpb"] for row in actual.values()),
            "mean_model_eval_fraction": mean(
                row["model_eval_fraction"] for row in actual.values()
            ),
            "max_model_eval_fraction": max_eval,
            "mean_admitted_byte_fraction": mean(
                row["admitted_byte_fraction"] for row in actual.values()
            ),
            "admitted_blocks": sum(row["admitted_blocks"] for row in actual.values()),
            "budget_violations": budget_violations,
            "search_codec_decision_mismatches": mismatches,
        }
        candidates.append(candidate)
        print("DEVELOPMENT_CANDIDATE", json.dumps(candidate, sort_keys=True), flush=True)
    eligible = [
        row
        for row in candidates
        if row["budget_violations"] == 0
        and row["search_codec_decision_mismatches"] == 0
    ]
    if not eligible:
        raise RuntimeError("F. BUDGET_VIOLATION: no preregistered threshold is feasible")
    selected = min(
        eligible,
        key=lambda row: (
            row["mean_payload_bpb"],
            row["mean_model_eval_fraction"],
            row["threshold"],
        ),
    )
    return candidates, selected, actual_by_threshold[int(selected["threshold"])]


def measure_activation(p14, context, rule, *, probe_bytes: int) -> dict:
    data = bytes((index * 29 + 7) % 251 for index in range(BLOCK_BYTES))
    tracker = p14.TrackingNeuralFactory(context)
    provider = RichCheapAdmissionBlockCDFProvider(
        context.cheap_factory,
        tracker,
        rule,
        stream_bytes=len(data),
        block_bytes=BLOCK_BYTES,
        probe_bytes=probe_bytes,
        max_admitted_bytes=BLOCK_BYTES,
    )
    prefix: list[int] = []
    for index in range(probe_bytes):
        provider(index, prefix)
        prefix.append(data[index])
    before = tracker.model_evaluations
    provider(probe_bytes, prefix)
    after_first = tracker.model_evaluations
    summary = provider.block_summary()[0]
    if not summary["admitted"]:
        raise RuntimeError("activation accounting probe unexpectedly rejected")
    return {
        "probe_bytes": probe_bytes,
        "first_neural_coded_byte_zero_based": probe_bytes,
        "first_neural_coded_byte_ordinal": probe_bytes + 1,
        "cheap_coded_bytes_before_activation": probe_bytes,
        "remaining_neural_coded_bytes_full_block": BLOCK_BYTES - probe_bytes,
        "model_evaluations_before_admission": before,
        "model_evaluations_after_first_specialist_output": after_first,
        "post_decision_catchup_evaluations_before_current_output": max(
            0, after_first - before - 1
        ),
    }


def precompute_diagnostic_blocks(p14, context, streams: dict[str, bytes]) -> list[dict]:
    rows: list[dict] = []
    forced16_rule = p14.ALWAYS_ADMIT_RULE
    forced32_rule = always_admit_rule()
    for stream_name, data in streams.items():
        for block_index, start in enumerate(range(0, len(data), BLOCK_BYTES)):
            block = data[start : start + BLOCK_BYTES]
            features16 = extract_cheap_admission_features(
                context.cheap_factory, block[:P14_PROBE_BYTES]
            )
            features32 = extract_cheap_admission_features(
                context.cheap_factory, block[:P15_PROBE_BYTES]
            )
            cheap = p14.encode_only(block, context.cheap_factory(), context.cheap_fp)
            forced16 = p14.run_rich(
                context, block, forced16_rule, verify=False
            )
            forced32 = run_horizon(
                p14,
                context,
                block,
                forced32_rule,
                probe_bytes=P15_PROBE_BYTES,
                verify=False,
            )
            rows.append(
                {
                    "stream": stream_name,
                    "block_index": block_index,
                    "start": start,
                    "bytes": len(block),
                    "unique_count_16": features16.unique_count,
                    "unique_count_32": features32.unique_count,
                    "cheap_payload_bits": cheap["payload_bits"],
                    "hybrid16_payload_bits": forced16["payload_bits"],
                    "hybrid16_model_evaluations": forced16["model_evaluations"],
                    "hybrid16_saving_bits": cheap["payload_bits"] - forced16["payload_bits"],
                    "hybrid32_payload_bits": forced32["payload_bits"],
                    "hybrid32_model_evaluations": forced32["model_evaluations"],
                    "hybrid32_saving_bits": cheap["payload_bits"] - forced32["payload_bits"],
                    "forced_horizon32_minus_horizon16_bits": (
                        forced32["payload_bits"] - forced16["payload_bits"]
                    ),
                }
            )
        print("DEVELOPMENT_DIAGNOSTIC", stream_name, flush=True)
    return rows


def oracle_selection(rows: list[dict], saving_field: str) -> set[int]:
    ranked = sorted(
        rows,
        key=lambda row: (int(row[saving_field]), -int(row["block_index"])),
        reverse=True,
    )
    return {
        int(row["block_index"])
        for row in ranked[: MAX_ADMITTED_BYTES // BLOCK_BYTES]
        if int(row[saving_field]) > 0
    }


def route_diagnostics(
    rows: list[dict], summaries: list[dict], *, horizon: int
) -> dict:
    saving_field = f"hybrid{horizon}_saving_bits"
    selected = {int(row["block_index"]): bool(row["admitted"]) for row in summaries}
    oracle = oracle_selection(rows, saving_field)
    output = {
        "true_neural": 0,
        "false_neural": 0,
        "true_cheap": 0,
        "missed_beneficial_neural": 0,
        "false_neural_lost_bits": 0,
        "missed_beneficial_lost_bits": 0,
        "fixed_budget_route_correct": 0,
    }
    for row in rows:
        index = int(row["block_index"])
        admitted = selected[index]
        saving = int(row[saving_field])
        beneficial = saving > 0
        if admitted and beneficial:
            output["true_neural"] += 1
        elif admitted:
            output["false_neural"] += 1
            output["false_neural_lost_bits"] += max(0, -saving)
        elif beneficial:
            output["missed_beneficial_neural"] += 1
            output["missed_beneficial_lost_bits"] += saving
        else:
            output["true_cheap"] += 1
        output["fixed_budget_route_correct"] += admitted == (index in oracle)
    output["fixed_budget_route_accuracy"] = (
        output["fixed_budget_route_correct"] / len(rows)
    )
    blocksum = sum(
        int(row[f"hybrid{horizon}_payload_bits"])
        if selected[int(row["block_index"])]
        else int(row["cheap_payload_bits"])
        for row in rows
    )
    oracle_bits = sum(
        int(row[f"hybrid{horizon}_payload_bits"])
        if int(row["block_index"]) in oracle
        else int(row["cheap_payload_bits"])
        for row in rows
    )
    output["blocksum_bits"] = blocksum
    output["oracle_bits"] = oracle_bits
    output["oracle_regret_bits"] = blocksum - oracle_bits
    output["oracle_admitted_blocks"] = len(oracle)
    return output


def development_reproduction_record(summary: dict) -> dict:
    return {
        "predecessor_reproduction": summary["predecessor_reproduction"],
        "development_streams": summary["development_streams"],
        "development_block_count": summary["development_block_count"],
        "candidate_rows_digest": summary["candidate_rows_digest"],
        "selected_threshold": summary["selected_threshold"],
        "selected_metrics": summary["selected_metrics"],
        "search_codec_decision_mismatches": summary[
            "search_codec_decision_mismatches"
        ],
        "activation_accounting": summary["activation_accounting"],
    }


def run_development(*, write_outputs: bool = True) -> dict:
    p14 = load_p14()
    p14_document, p14_rule = validate_p14_policy(p14)
    context = p14.load_context()
    if context.checkpoint["canonical_model_fingerprint"] != MODEL_FINGERPRINT:
        raise RuntimeError("K. INHERITED_PILOT014_CORRECTNESS_BUG: loaded model drift")
    if context.checkpoint["checkpoint_sha256"] != CHECKPOINT_SHA256:
        raise RuntimeError("K. INHERITED_PILOT014_CORRECTNESS_BUG: loaded checkpoint drift")
    streams, source_manifest = p14.make_development_streams(context)
    predecessor = reproduce_predecessors(p14, context, streams, p14_rule)
    print("PREDECESSORS_REPRODUCED", json.dumps(predecessor, sort_keys=True), flush=True)
    candidates, selected, selected_actual = evaluate_thresholds(
        p14, context, streams
    )
    selected_rule = threshold_rule(int(selected["threshold"]))
    p14_all = {
        name: p14.run_rich(context, data, p14_rule, verify=True)
        for name, data in streams.items()
    }
    block_rows = precompute_diagnostic_blocks(p14, context, streams)
    p14_diag = []
    p15_diag = []
    for stream_name in streams:
        stream_rows = [row for row in block_rows if row["stream"] == stream_name]
        p14_diag.append(
            route_diagnostics(
                stream_rows, p14_all[stream_name]["block_summary"], horizon=16
            )
        )
        p15_diag.append(
            route_diagnostics(
                stream_rows,
                selected_actual[stream_name]["block_summary"],
                horizon=32,
            )
        )
    simulated = simulate_routes(
        context, streams, selected_rule, probe_bytes=P15_PROBE_BYTES
    )
    mismatches = compare_routes(simulated, selected_actual)
    activation = {
        "pilot014": measure_activation(
            p14, context, p14.ALWAYS_ADMIT_RULE, probe_bytes=P14_PROBE_BYTES
        ),
        "pilot015": measure_activation(
            p14, context, always_admit_rule(), probe_bytes=P15_PROBE_BYTES
        ),
    }
    candidate_digest = sha256(canonical_json(candidates))
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "new_holdout_sources_opened": False,
        "development_source": "already-consumed PILOT-012/PILOT-013 mixed streams",
        "development_streams": list(streams),
        "development_block_count": len(block_rows),
        "source_manifest": source_manifest,
        "threshold_candidates": list(THRESHOLD_CANDIDATES),
        "selection_objective": [
            "lower mean real range-coded payload bpb",
            "lower mean actual neural evaluation fraction",
            "lower threshold",
        ],
        "candidate_rows_digest": candidate_digest,
        "selected_threshold": int(selected["threshold"]),
        "selected_metrics": selected,
        "predecessor_reproduction": predecessor,
        "search_codec_decision_mismatches": mismatches,
        "activation_accounting": activation,
        "p14_all_stream_mean_payload_bpb": mean(
            row["payload_bpb"] for row in p14_all.values()
        ),
        "p14_all_stream_mean_model_eval_fraction": mean(
            row["model_eval_fraction"] for row in p14_all.values()
        ),
        "p14_mean_fixed_budget_route_accuracy": mean(
            row["fixed_budget_route_accuracy"] for row in p14_diag
        ),
        "p15_mean_fixed_budget_route_accuracy": mean(
            row["fixed_budget_route_accuracy"] for row in p15_diag
        ),
        "p14_mean_oracle_regret_bits": mean(
            row["oracle_regret_bits"] for row in p14_diag
        ),
        "p15_mean_oracle_regret_bits": mean(
            row["oracle_regret_bits"] for row in p15_diag
        ),
        "mean_forced_horizon32_minus_horizon16_bits_per_block": mean(
            row["forced_horizon32_minus_horizon16_bits"] for row in block_rows
        ),
    }
    reproduction = development_reproduction_record(summary)
    reproduction_digest = sha256(canonical_json(reproduction))
    summary["development_reproduction_digest"] = reproduction_digest
    recommended_policy = {
        "pilot_version": "PILOT-015",
        "experiment_id": EXPERIMENT_ID,
        "predecessor_sha": PILOT014_FINAL_SHA,
        "source_commit": FROZEN_IMPLEMENTATION_SHA,
        "policy": {
            "block_bytes": BLOCK_BYTES,
            "probe_bytes": P15_PROBE_BYTES,
            "max_admitted_bytes": MAX_ADMITTED_BYTES,
            "max_actual_neural_eval_fraction": 0.5,
            "feature_name": "unique_count_32",
            "feature_definition": (
                "number of distinct byte values among the first 32 "
                "already-consumed bytes of the current 512-byte block"
            ),
            "selector": selected_rule.to_dict(),
            "selector_side_bits": 0,
            "neural_evaluations_before_admission": 0,
            "cheap_provider_fingerprint": context.cheap_fp.hex(),
            "neural_gate_fingerprint": context.neural_gate_fp.hex(),
            "model_fingerprint": MODEL_FINGERPRINT,
            "checkpoint_sha256": CHECKPOINT_SHA256,
            "codec_identity": "POL1 shared-provider range coder, unchanged",
        },
        "development": {
            "threshold_candidates": list(THRESHOLD_CANDIDATES),
            "selection_objective": summary["selection_objective"],
            "selected_metrics": selected,
            "reproduction": reproduction,
            "reproduction_digest": reproduction_digest,
        },
        "freeze": {
            "fresh_holdout_bytes_opened_before_freeze": False,
            "policy_may_not_be_retuned_after_this_record": True,
        },
    }
    recommended_policy["policy_digest"] = policy_digest(recommended_policy)
    if write_outputs:
        csvout(HERE / "development-candidates.csv", candidates)
        csvout(HERE / "development-blocks.csv", block_rows)
        (HERE / "development-summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n"
        )
        (HERE / "recommended-policy.json").write_text(
            json.dumps(recommended_policy, indent=2, sort_keys=True) + "\n"
        )
    print("DEVELOPMENT_SELECTED", json.dumps(selected, sort_keys=True), flush=True)
    print("POLICY_DIGEST", recommended_policy["policy_digest"], flush=True)
    return {
        "summary": summary,
        "recommended_policy": recommended_policy,
        "candidates": candidates,
    }


def policy_digest(document: dict) -> str:
    payload = {key: value for key, value in document.items() if key != "policy_digest"}
    return sha256(canonical_json(payload))


def load_frozen_policy(path: Path) -> tuple[dict, object]:
    document = json.loads(path.read_text())
    observed = policy_digest(document)
    if document.get("policy_digest") != observed:
        raise RuntimeError(
            f"frozen policy digest mismatch: {observed} != {document.get('policy_digest')}"
        )
    if document.get("pilot_version") != "PILOT-015":
        raise RuntimeError("wrong frozen policy version")
    if document.get("predecessor_sha") != PILOT014_FINAL_SHA:
        raise RuntimeError("frozen predecessor mismatch")
    policy = document["policy"]
    if int(policy["block_bytes"]) != BLOCK_BYTES:
        raise RuntimeError("frozen block size changed")
    if int(policy["probe_bytes"]) != P15_PROBE_BYTES:
        raise RuntimeError("frozen observation horizon changed")
    if int(policy["max_admitted_bytes"]) != MAX_ADMITTED_BYTES:
        raise RuntimeError("frozen budget changed")
    if policy["model_fingerprint"] != MODEL_FINGERPRINT:
        raise RuntimeError("frozen model fingerprint changed")
    if policy["checkpoint_sha256"] != CHECKPOINT_SHA256:
        raise RuntimeError("frozen checkpoint digest changed")
    rule = admission_rule_from_dict(policy["selector"])
    if rule != threshold_rule(int(rule.nodes[0].threshold)):
        raise RuntimeError("frozen selector is not the preregistered one-split rule")
    return document, rule


def make_holdout_streams(p14, context, preregistration: dict):
    specs = {item["name"]: item for item in preregistration["sources"]}
    sources, source_manifest = p14.download_verified_sources(
        specs, user_agent="POLLICINO-PILOT-015-HOLDOUT/1.0"
    )
    p12 = context.p12
    generated = preregistration["generated_components"]
    components = {
        alias: sources[source_name]
        for alias, source_name in preregistration["source_aliases"].items()
    }
    components.update(
        {
            "json": p12.json_bytes(STREAM_BYTES, int(generated["json_seed"])),
            "dna": p12.dna_bytes(STREAM_BYTES, int(generated["dna_seed"])),
            "random64": p12.random_bytes(
                STREAM_BYTES, int(generated["random64_seed"]), 64
            ),
            "random256": p12.random_bytes(
                STREAM_BYTES, int(generated["random256_seed"]), 256
            ),
            "repeat": p12.cycle(str(generated["repeat_ascii"]).encode(), STREAM_BYTES),
            "compressed": p12.compressed_bytes(
                STREAM_BYTES, int(generated["compressed_seed"])
            ),
            "english": p12.english_bytes(STREAM_BYTES),
        }
    )
    streams: dict[str, bytes] = {}
    stream_manifest: list[dict] = []
    for name, raw_recipe in preregistration["recipes"].items():
        recipe = [(str(component), int(length)) for component, length in raw_recipe]
        data, segments = p12.compose(components, recipe)
        if len(data) != STREAM_BYTES:
            raise RuntimeError(f"holdout stream {name} is not 4096 bytes")
        streams[name] = data
        stream_manifest.append(
            {
                "stream": name,
                "bytes": len(data),
                "sha256": sha256(data),
                "segments": segments,
            }
        )
    return streams, source_manifest, stream_manifest


def holdout_stream_metrics(
    p14,
    context,
    stream_name: str,
    data: bytes,
    block_rows: list[dict],
    p14_rule,
    p15_rule,
) -> tuple[dict, list[dict]]:
    cheap = p14.reset_roundtrip(context, data, neural=False)
    neural = p14.reset_roundtrip(context, data, neural=True)
    p12_result = p14.p12_max_roundtrip(context, data)
    p13 = p14.run_p13(context, data, verify=True)
    p14_result = p14.run_rich(context, data, p14_rule, verify=True)
    p15_result = run_horizon(
        p14,
        context,
        data,
        p15_rule,
        probe_bytes=P15_PROBE_BYTES,
        verify=True,
    )
    classical = p14.classical_baselines(data)
    p14_diag = route_diagnostics(
        block_rows, p14_result["block_summary"], horizon=16
    )
    p15_diag = route_diagnostics(
        block_rows, p15_result["block_summary"], horizon=32
    )
    p14_summaries = {
        int(row["block_index"]): row for row in p14_result["block_summary"]
    }
    p15_summaries = {
        int(row["block_index"]): row for row in p15_result["block_summary"]
    }
    available_gain = cheap["payload_bpb"] - neural["payload_bpb"]
    p14_retained = (
        (cheap["payload_bpb"] - p14_result["payload_bpb"]) / available_gain
        if available_gain > 0
        else 0.0
    )
    p15_retained = (
        (cheap["payload_bpb"] - p15_result["payload_bpb"]) / available_gain
        if available_gain > 0
        else 0.0
    )
    p15_selected_delay_bits = sum(
        int(block["forced_horizon32_minus_horizon16_bits"])
        for block in block_rows
        if bool(p15_summaries[int(block["block_index"])]["admitted"])
    )
    simulated = simulate_routes(
        context, {stream_name: data}, p15_rule, probe_bytes=P15_PROBE_BYTES
    )
    mismatches = compare_routes(simulated, {stream_name: p15_result})
    diagnostics = []
    oracle16 = oracle_selection(block_rows, "hybrid16_saving_bits")
    oracle32 = oracle_selection(block_rows, "hybrid32_saving_bits")
    for block in block_rows:
        index = int(block["block_index"])
        diagnostics.append(
            {
                **block,
                "p14_admitted": bool(p14_summaries[index]["admitted"]),
                "p15_admitted": bool(p15_summaries[index]["admitted"]),
                "p14_rule_match": bool(p14_summaries[index]["rule_match"]),
                "p15_rule_match": bool(p15_summaries[index]["rule_match"]),
                "p14_budget_limited": bool(p14_summaries[index]["budget_limited"]),
                "p15_budget_limited": bool(p15_summaries[index]["budget_limited"]),
                "oracle16_admitted": index in oracle16,
                "oracle32_admitted": index in oracle32,
            }
        )
    row = {
        "stream": stream_name,
        "sample_bytes": len(data),
        "source_sha256": sha256(data),
        "cheap_reset_bpb": cheap["payload_bpb"],
        "neural_reset_bpb": neural["payload_bpb"],
        "neural_reset_model_eval_fraction": neural["model_eval_fraction"],
        "p12_max_bpb": p12_result["payload_bpb"],
        "p12_max_model_eval_fraction": p12_result["model_eval_fraction"],
        "p13_bpb": p13["payload_bpb"],
        "p13_model_eval_fraction": p13["model_eval_fraction"],
        "p14_bpb": p14_result["payload_bpb"],
        "p14_model_eval_fraction": p14_result["model_eval_fraction"],
        "p14_admitted_blocks": p14_result["admitted_blocks"],
        "p14_retained_gain_fraction": p14_retained,
        "p15_bpb": p15_result["payload_bpb"],
        "p15_model_eval_fraction": p15_result["model_eval_fraction"],
        "p15_admitted_blocks": p15_result["admitted_blocks"],
        "p15_rejected_blocks": len(block_rows) - p15_result["admitted_blocks"],
        "p15_admitted_byte_fraction": p15_result["admitted_byte_fraction"],
        "p15_retained_gain_fraction": p15_retained,
        "p14_minus_p15_bpb": p14_result["payload_bpb"] - p15_result["payload_bpb"],
        "retained_gain_improvement_vs_p14": p15_retained - p14_retained,
        "oracle16_blocksum_bpb": p14_diag["oracle_bits"] / len(data),
        "oracle32_blocksum_bpb": p15_diag["oracle_bits"] / len(data),
        "p14_blocksum_bpb": p14_diag["blocksum_bits"] / len(data),
        "p15_blocksum_bpb": p15_diag["blocksum_bits"] / len(data),
        "p14_oracle_regret_bits": p14_diag["oracle_regret_bits"],
        "p15_oracle_regret_bits": p15_diag["oracle_regret_bits"],
        "p14_route_accuracy": p14_diag["fixed_budget_route_accuracy"],
        "p15_route_accuracy": p15_diag["fixed_budget_route_accuracy"],
        "p14_false_neural": p14_diag["false_neural"],
        "p15_false_neural": p15_diag["false_neural"],
        "p14_missed_beneficial_neural": p14_diag["missed_beneficial_neural"],
        "p15_missed_beneficial_neural": p15_diag["missed_beneficial_neural"],
        "p14_false_neural_lost_bits": p14_diag["false_neural_lost_bits"],
        "p15_false_neural_lost_bits": p15_diag["false_neural_lost_bits"],
        "p14_missed_beneficial_lost_bits": p14_diag[
            "missed_beneficial_lost_bits"
        ],
        "p15_missed_beneficial_lost_bits": p15_diag[
            "missed_beneficial_lost_bits"
        ],
        "p15_selected_blocks_horizon_delay_bits": p15_selected_delay_bits,
        "search_codec_decision_mismatches": mismatches,
        "roundtrip": bool(p15_result["roundtrip"] and p14_result["roundtrip"]),
        "sha256_match": bool(
            p15_result["sha256_match"] and p14_result["sha256_match"]
        ),
        **classical,
    }
    return row, diagnostics


def aggregate_holdout(rows: list[dict]) -> dict:
    aggregate = {
        "mean_cheap_reset_bpb": mean(row["cheap_reset_bpb"] for row in rows),
        "mean_neural_reset_bpb": mean(row["neural_reset_bpb"] for row in rows),
        "mean_p12_max_bpb": mean(row["p12_max_bpb"] for row in rows),
        "mean_p13_bpb": mean(row["p13_bpb"] for row in rows),
        "mean_p14_bpb": mean(row["p14_bpb"] for row in rows),
        "mean_p15_bpb": mean(row["p15_bpb"] for row in rows),
        "mean_oracle16_blocksum_bpb": mean(
            row["oracle16_blocksum_bpb"] for row in rows
        ),
        "mean_oracle32_blocksum_bpb": mean(
            row["oracle32_blocksum_bpb"] for row in rows
        ),
        "mean_zlib_bpb": mean(row["zlib_bpb"] for row in rows),
        "mean_zstd19_bpb": mean(row["zstd19_bpb"] for row in rows),
        "mean_p15_model_eval_fraction": mean(
            row["p15_model_eval_fraction"] for row in rows
        ),
        "max_p15_model_eval_fraction": max(
            row["p15_model_eval_fraction"] for row in rows
        ),
        "min_p15_model_eval_fraction": min(
            row["p15_model_eval_fraction"] for row in rows
        ),
        "mean_p15_admitted_byte_fraction": mean(
            row["p15_admitted_byte_fraction"] for row in rows
        ),
        "mean_p14_retained_gain_fraction": mean(
            row["p14_retained_gain_fraction"] for row in rows
        ),
        "mean_p15_retained_gain_fraction": mean(
            row["p15_retained_gain_fraction"] for row in rows
        ),
        "mean_retained_gain_improvement_vs_p14": mean(
            row["retained_gain_improvement_vs_p14"] for row in rows
        ),
        "mean_horizon32_gain_vs16_bpb": mean(
            row["p14_minus_p15_bpb"] for row in rows
        ),
        "p15_beats_p14_streams": sum(row["p15_bpb"] < row["p14_bpb"] for row in rows),
        "p15_loses_to_p14_streams": sum(row["p15_bpb"] > row["p14_bpb"] for row in rows),
        "p15_ties_p14_streams": sum(row["p15_bpb"] == row["p14_bpb"] for row in rows),
        "mean_p14_route_accuracy": mean(row["p14_route_accuracy"] for row in rows),
        "mean_p15_route_accuracy": mean(row["p15_route_accuracy"] for row in rows),
        "mean_p14_oracle_regret_bits": mean(
            row["p14_oracle_regret_bits"] for row in rows
        ),
        "mean_p15_oracle_regret_bits": mean(
            row["p15_oracle_regret_bits"] for row in rows
        ),
        "mean_p14_to_oracle16_gap_bpb": mean(
            row["p14_blocksum_bpb"] - row["oracle16_blocksum_bpb"] for row in rows
        ),
        "mean_p15_to_oracle32_gap_bpb": mean(
            row["p15_blocksum_bpb"] - row["oracle32_blocksum_bpb"] for row in rows
        ),
        "total_p15_false_neural": sum(row["p15_false_neural"] for row in rows),
        "total_p15_missed_beneficial_neural": sum(
            row["p15_missed_beneficial_neural"] for row in rows
        ),
        "total_p15_false_neural_lost_bits": sum(
            row["p15_false_neural_lost_bits"] for row in rows
        ),
        "total_p15_missed_beneficial_lost_bits": sum(
            row["p15_missed_beneficial_lost_bits"] for row in rows
        ),
        "total_p15_selected_blocks_horizon_delay_bits": sum(
            row["p15_selected_blocks_horizon_delay_bits"] for row in rows
        ),
        "budget_violations": sum(
            row["p15_model_eval_fraction"] > 0.5 + 1e-12 for row in rows
        ),
        "search_codec_decision_mismatches": sum(
            row["search_codec_decision_mismatches"] for row in rows
        ),
        "exact_roundtrip_failures": sum(not row["roundtrip"] for row in rows),
        "sha256_mismatches": sum(not row["sha256_match"] for row in rows),
    }
    aggregate["retained_gain_threshold_passed"] = bool(
        aggregate["mean_p15_retained_gain_fraction"] >= RETAINED_GAIN_SUCCESS
    )
    aggregate["mean_payload_beats_p14"] = bool(
        aggregate["mean_p15_bpb"] < aggregate["mean_p14_bpb"]
    )
    aggregate["secondary_four_of_six_passed"] = bool(
        aggregate["p15_beats_p14_streams"] >= 4
    )
    aggregate["primary_success"] = bool(
        aggregate["retained_gain_threshold_passed"]
        and aggregate["mean_payload_beats_p14"]
        and aggregate["budget_violations"] == 0
        and aggregate["search_codec_decision_mismatches"] == 0
        and aggregate["exact_roundtrip_failures"] == 0
        and aggregate["sha256_mismatches"] == 0
    )
    signal_improved = (
        aggregate["mean_p15_route_accuracy"] > aggregate["mean_p14_route_accuracy"]
        or aggregate["mean_p15_oracle_regret_bits"]
        < aggregate["mean_p14_oracle_regret_bits"]
    )
    if aggregate["primary_success"] and aggregate["secondary_four_of_six_passed"]:
        classification = "PILOT015_LONGER_HORIZON_SUCCESS"
    elif aggregate["primary_success"]:
        classification = "PILOT015_LONGER_HORIZON_SUCCESS_WITH_LIMITS"
    elif aggregate["mean_payload_beats_p14"]:
        classification = "PILOT015_LONGER_HORIZON_IMPROVED_BUT_THRESHOLD_NOT_MET"
    elif signal_improved:
        classification = "PILOT015_ADMISSION_DELAY_NEGATES_SIGNAL_GAIN"
    else:
        classification = "PILOT015_LONGER_HORIZON_NO_BENEFIT"
    aggregate["scientific_classification"] = classification
    return aggregate


def bundle_digest(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.name):
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def run_holdout(
    policy_document: dict,
    rule,
    preregistration: dict,
    preregistration_digest: str,
) -> dict:
    if os.environ.get("PILOT015_FROZEN_FIREWALL") != "verified":
        raise RuntimeError("fresh holdout may only run through run_frozen.py")
    p14 = load_p14()
    _, p14_rule = validate_p14_policy(p14)
    context = p14.load_context()
    streams, sources, stream_manifest = make_holdout_streams(
        p14, context, preregistration
    )
    block_rows = precompute_diagnostic_blocks(p14, context, streams)
    rows: list[dict] = []
    diagnostic_rows: list[dict] = []
    for stream_name, data in streams.items():
        relevant = [row for row in block_rows if row["stream"] == stream_name]
        row, diagnostics = holdout_stream_metrics(
            p14, context, stream_name, data, relevant, p14_rule, rule
        )
        rows.append(row)
        diagnostic_rows.extend(diagnostics)
        print("HOLDOUT", json.dumps(row, sort_keys=True), flush=True)
    aggregate = aggregate_holdout(rows)
    activation = {
        "pilot014": measure_activation(
            p14, context, p14.ALWAYS_ADMIT_RULE, probe_bytes=P14_PROBE_BYTES
        ),
        "pilot015": measure_activation(
            p14, context, always_admit_rule(), probe_bytes=P15_PROBE_BYTES
        ),
    }
    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "preregistration_digest": preregistration_digest,
        "selection_basis": preregistration["selection_basis"],
        "sources": sources,
        "streams": stream_manifest,
    }
    results = {
        "experiment_id": EXPERIMENT_ID,
        "question": "Does exactly 32 cheap-only bytes improve same-budget admission over the frozen 16-byte selector?",
        "predecessor": {
            "pilot014_final_sha": PILOT014_FINAL_SHA,
            "pilot014_policy_digest": PILOT014_POLICY_DIGEST,
            "pilot013_remains_valid": True,
            "pilot014_remains_valid": True,
        },
        "run_source_commit": current_git_sha(),
        "frozen_policy_digest": policy_document["policy_digest"],
        "holdout_preregistration_digest": preregistration_digest,
        "policy": policy_document["policy"],
        "development": policy_document["development"],
        "holdout": {
            "name": preregistration["name"],
            "streams": list(streams),
            "sources": sources,
            "aggregate": aggregate,
        },
        "activation_accounting": activation,
        "feature_cost": {
            "histogram_updates_per_block": 32,
            "histogram_entries_max": 32,
            "unique_count_extractions": 1,
            "integer_split_comparisons": 1,
            "integer_budget_comparisons": 1,
            "additional_bytes_transmitted": 0,
            "neural_calls_during_feature_extraction": 0,
            "extra_histogram_updates_vs_pilot014_per_block": 16,
            "relative_cost": "bounded O(32) integer/container work versus 511 counted neural forwards per admitted full block",
        },
        "protocol": {
            "block_bytes": BLOCK_BYTES,
            "pilot014_probe_bytes": P14_PROBE_BYTES,
            "pilot015_probe_bytes": P15_PROBE_BYTES,
            "hard_max_admitted_bytes": MAX_ADMITTED_BYTES,
            "hard_max_actual_neural_eval_fraction": 0.5,
            "selector_side_bits": 0,
            "future_byte_reads_before_admission": 0,
            "neural_evaluations_before_admission": 0,
            "primary_compute_metric": "actual uncached PyTorch model forward evaluations / source bytes",
            "search_and_codec_helper": "rich_cheap_admission_decision",
            "holdout_policy_retuning": 0,
            "policy_modifications_after_holdout_access": 0,
            "neural_model_changed": False,
            "cheap_model_changed": False,
            "range_coder_changed": False,
            "block_size_changed": False,
            "selector_complexity_changed_vs_pilot014": False,
        },
        "failure_taxonomy": {
            "repaired_before_scientific_run": [],
            "scientific_run_failures": [],
        },
        "limitations": [
            "Six deterministic mixed streams form a mechanism holdout, not a population sample.",
            "The horizon-matched fixed-budget oracles are non-causal and use independently coded block payloads.",
            "The shared neural checkpoint cost is separate from payload bpb and is not free.",
            "Python container overhead is implementation-dependent although logical feature state is bounded.",
        ],
    }
    results_path = HERE / "results.json"
    rows_path = HERE / "holdout.csv"
    blocks_path = HERE / "holdout-blocks.csv"
    manifest_path = HERE / "holdout-manifest.json"
    results_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    csvout(rows_path, rows)
    csvout(blocks_path, diagnostic_rows)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    artifact_sha = bundle_digest(
        [results_path, rows_path, blocks_path, manifest_path]
    )
    metadata = {
        "experiment_id": EXPERIMENT_ID,
        "execution_kind": "local-scientific-run",
        "workflow_run_id": None,
        "git_sha": current_git_sha(),
        "artifact": {
            "id": f"local-{current_git_sha()[:12]}-{policy_document['policy_digest'][:12]}",
            "name": "pilot-015-results",
            "digest": f"sha256:{artifact_sha}",
        },
        "frozen_policy_digest": policy_document["policy_digest"],
        "holdout_manifest_digest": sha256(manifest_path.read_bytes()),
        "holdout_preregistration_digest": preregistration_digest,
        "python": sys.version,
        "platform": platform.platform(),
        "torch": p14.torch.__version__,
        "numpy": p14.np.__version__,
        "zstandard": p14.zstd.__version__,
        "device": "cpu",
        "torch_num_threads": p14.torch.get_num_threads(),
        "torch_deterministic_algorithms": p14.torch.are_deterministic_algorithms_enabled(),
        "random_seeds": preregistration["generated_components"],
        "checkpoint": context.checkpoint,
        "exact_command": "GITHUB_TOKEN=\"$(gh auth token)\" /Users/antoniocaristia/dev/pollicino-pilot014/.venv/bin/python experiments/pilot-015/run_frozen.py",
        "tests": "recorded after final validation",
    }
    (HERE / "run-metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    )
    print("AGGREGATE", json.dumps(aggregate, sort_keys=True), flush=True)
    print("ARTIFACT_SHA256", artifact_sha, flush=True)
    return {"results": results, "metadata": metadata, "manifest": manifest}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("development", "holdout"))
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--preregistration", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.phase == "development":
        run_development()
        return
    if args.policy is None or args.preregistration is None:
        raise RuntimeError("holdout requires --policy and --preregistration")
    policy_document, rule = load_frozen_policy(args.policy)
    preregistration_bytes = args.preregistration.read_bytes()
    run_holdout(
        policy_document,
        rule,
        json.loads(preregistration_bytes),
        sha256(preregistration_bytes),
    )


if __name__ == "__main__":
    main()
