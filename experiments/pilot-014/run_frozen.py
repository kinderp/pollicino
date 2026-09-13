from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN = HERE / "run.py"
POLICY = HERE / "frozen-policy.json"
PREREGISTRATION = HERE / "holdout-preregistration.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("pilot014_frozen_runner", RUN)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
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
            "fresh evaluation refuses tracked worktree changes; commit the frozen state first"
        )


def main() -> None:
    p14 = load_runner()
    policy_document, rule = p14.load_frozen_policy(POLICY)
    source_commit = policy_document["source_commit"]
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", source_commit, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        raise RuntimeError("frozen implementation commit is not an ancestor of the run head")
    require_clean_tracked_worktree()

    context = p14.load_context()
    development = p14.run_development(context, write_outputs=True)
    observed = p14.development_reproduction_record(development["summary"])
    expected = policy_document["development"]["reproduction"]
    if observed != expected:
        raise RuntimeError(
            "frozen development reproduction drifted: "
            f"expected={expected!r} observed={observed!r}"
        )
    observed_digest = p14.sha256(p14.canonical_json(observed))
    if observed_digest != policy_document["development"]["reproduction_digest"]:
        raise RuntimeError("frozen development reproduction digest mismatch")
    if development["recommended_policy"]["selector"] != policy_document["policy"]["selector"]:
        raise RuntimeError("development selection no longer produces the frozen selector")
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

    preregistration_bytes = PREREGISTRATION.read_bytes()
    preregistration = json.loads(preregistration_bytes)
    if preregistration["frozen_policy_digest"] != policy_document["policy_digest"]:
        raise RuntimeError("holdout preregistration targets a different frozen policy")
    preregistration_digest = p14.sha256(preregistration_bytes)
    print(
        "HOLDOUT_PREREGISTRATION_VERIFIED",
        preregistration_digest,
        flush=True,
    )
    p14.run_holdout(
        context,
        policy_document,
        rule,
        preregistration,
        preregistration_digest,
    )


if __name__ == "__main__":
    main()
