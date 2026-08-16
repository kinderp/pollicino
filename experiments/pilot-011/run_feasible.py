from __future__ import annotations

import importlib.util
import io
import json
import socket
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
HERE = Path(__file__).resolve().parent

# Infrastructure-only robustness for slow historical corpus mirrors. Read every
# response fully inside the retry boundary so connection and mid-stream read
# failures are both retried. Callers receive a normal in-memory file object.
socket.setdefaulttimeout(900)
_original_urlopen = urllib.request.urlopen


def _retrying_urlopen(url, *args, **kwargs):
    timeout = kwargs.get("timeout")
    if timeout is None or timeout < 900:
        kwargs["timeout"] = 900
    last_error = None
    for attempt in range(4):
        try:
            with _original_urlopen(url, *args, **kwargs) as response:
                data = response.read()
            return io.BytesIO(data)
        except Exception as exc:
            last_error = exc
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))
    raise last_error


urllib.request.urlopen = _retrying_urlopen

spec = importlib.util.spec_from_file_location("pilot011_core", HERE / "run.py")
core = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(core)

# Development-only feasibility check in the previous run established that no member
# of the frozen 735-policy grid satisfies the predeclared <=20% specialist-call
# budget. Do not relax that budget post hoc and do not open the fresh holdout for
# it: keep the budget fixed, record it as infeasible, and evaluate only feasible
# P11 modes. Cheap-only remains the explicit zero-neural endpoint in all tables.
requested_budgets = dict(core.MODE_BUDGETS)
core.MODE_BUDGETS = {"max": requested_budgets["max"], "balanced": requested_budgets["balanced"]}
core.main()

results_path = HERE / "output" / "results.json"
results = json.loads(results_path.read_text())
results["development"]["requested_mode_budgets"] = requested_budgets
results["development"]["infeasible_modes"] = {
    "fast": {
        "budget": requested_budgets["fast"],
        "reason": "No policy in the frozen 735-policy grid has mean specialist-call fraction <= 0.20 on the 20 development streams.",
        "holdout_evaluated": False,
    }
}
results["protocol"]["infeasible_budget_rule"] = (
    "A predeclared hard budget with no eligible development policy is reported as infeasible and is not relaxed after development."
)
results_path.write_text(json.dumps(results, indent=2) + "\n")
