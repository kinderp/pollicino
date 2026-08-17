from __future__ import annotations

import builtins
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "run.py"
FROZEN = json.loads((HERE / "frozen-policy.json").read_text())
EXPECTED_POLICY = FROZEN["policy"]

CORRECTED_SOURCES = {
    "go-http-server": {
        "url": "https://raw.githubusercontent.com/golang/go/go1.22.12/src/net/http/server.go",
        "git_blob_sha1": "23a603a83dd7135077fa1363ceb8255ff345ac06",
    },
    "node-cjs-loader": {
        "url": "https://raw.githubusercontent.com/nodejs/node/v20.19.1/lib/internal/modules/cjs/loader.js",
        "git_blob_sha1": "ebccdb28256314e7cd8ac8d7e3dec670286022d2",
    },
}


def load_original():
    spec = importlib.util.spec_from_file_location("pilot013_original", RUN)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    p13 = load_original()
    # Correct source provenance only. The development search space and all codec
    # parameters remain exactly those of the first scientific run.
    p13.FRESH_SOURCES = CORRECTED_SOURCES

    state = {"policy_frozen_seen": False, "observed_policy": None}
    original_print = builtins.print
    original_download = p13.download_sources

    def guarded_print(*args, **kwargs):
        if args and args[0] == "POLICY_FROZEN":
            if len(args) < 2:
                raise RuntimeError("PILOT-013 emitted an unreadable frozen-policy record")
            observed = json.loads(str(args[1]))
            state["observed_policy"] = observed
            if observed != EXPECTED_POLICY:
                raise RuntimeError(
                    "PILOT-013 development policy drifted after the first freeze: "
                    f"expected={EXPECTED_POLICY!r} observed={observed!r}"
                )
            state["policy_frozen_seen"] = True
        return original_print(*args, **kwargs)

    def guarded_download_sources():
        if not state["policy_frozen_seen"]:
            raise RuntimeError("fresh holdout requested before the frozen policy was re-verified")
        return original_download()

    builtins.print = guarded_print
    p13.download_sources = guarded_download_sources
    try:
        p13.main()
    finally:
        builtins.print = original_print

    results_path = HERE / "output" / "results.json"
    results = json.loads(results_path.read_text())
    selected = results["development"]["selected_policy"]
    if selected != EXPECTED_POLICY:
        raise RuntimeError(
            "written result does not preserve the first-run frozen policy: "
            f"expected={EXPECTED_POLICY!r} selected={selected!r}"
        )
    results["provenance_correction"] = {
        "first_run_id": FROZEN["frozen_in_github_actions_run_id"],
        "first_run_scientific_head_sha": FROZEN["scientific_head_sha"],
        "first_run_policy_frozen_before_holdout": True,
        "first_run_holdout_metrics_produced": False,
        "reason_for_rerun": "correct preregistered Git-blob identifiers for Go and Node sources",
        "policy_retuned": False,
        "corrected_source_git_blobs": {
            name: meta["git_blob_sha1"] for name, meta in CORRECTED_SOURCES.items()
        },
    }
    results_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
