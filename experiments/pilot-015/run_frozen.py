from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN = HERE / "run.py"
POLICY = HERE / "frozen-policy.json"
HOLDOUT_PREREGISTRATION = HERE / "holdout-preregistration.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("pilot015_frozen_runner", RUN)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def require_clean_tracked_worktree() -> None:
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=ROOT,
        text=True,
    )
    if status:
        raise RuntimeError(
            "fresh evaluation refuses tracked worktree changes; commit frozen state first"
        )


def main() -> None:
    p15 = load_runner()
    policy_document, rule = p15.load_frozen_policy(POLICY)
    source_commit = policy_document["source_commit"]
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", source_commit, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        raise RuntimeError("frozen implementation commit is not an ancestor of run HEAD")
    require_clean_tracked_worktree()

    development = p15.run_development(write_outputs=False)
    observed = p15.development_reproduction_record(development["summary"])
    expected = policy_document["development"]["reproduction"]
    if observed != expected:
        raise RuntimeError(
            "frozen development reproduction drifted: "
            f"expected={expected!r} observed={observed!r}"
        )
    observed_digest = p15.sha256(p15.canonical_json(observed))
    if observed_digest != policy_document["development"]["reproduction_digest"]:
        raise RuntimeError("frozen development reproduction digest mismatch")
    if (
        development["recommended_policy"]["policy"]["selector"]
        != policy_document["policy"]["selector"]
    ):
        raise RuntimeError("development no longer selects the frozen threshold")
    if development["recommended_policy"]["policy_digest"] != policy_document["policy_digest"]:
        raise RuntimeError("regenerated policy digest differs from frozen policy digest")
    print(
        "POLICY_FROZEN_VERIFIED",
        json.dumps(
            {
                "policy_digest": policy_document["policy_digest"],
                "development_reproduction_digest": observed_digest,
            },
            sort_keys=True,
        ),
        flush=True,
    )

    preregistration_bytes = HOLDOUT_PREREGISTRATION.read_bytes()
    preregistration = json.loads(preregistration_bytes)
    if preregistration["frozen_policy_digest"] != policy_document["policy_digest"]:
        raise RuntimeError("holdout preregistration targets another frozen policy")
    preregistration_digest = p15.sha256(preregistration_bytes)
    print("HOLDOUT_PREREGISTRATION_VERIFIED", preregistration_digest, flush=True)
    os.environ["PILOT015_FROZEN_FIREWALL"] = "verified"
    p15.run_holdout(
        policy_document,
        rule,
        preregistration,
        preregistration_digest,
    )


if __name__ == "__main__":
    main()
