from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from pollicino.net.bearer import (
    BearerContactOutcome,
    ImpairmentAction,
    ScriptedImpairmentPlan,
    ScriptedInMemoryLink,
    run_bearer_contact,
)
from px9_support import close_node, full_budget, persistent_node, query, reopen_node, result


def test_sender_uncertainty_after_commit_is_resolved_by_fresh_reconciliation(
    tmp_path: Path,
) -> None:
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left = persistent_node(left_root, "left")
    right = persistent_node(right_root, "right")
    left.query_results.add_query(query(1))
    uncertain = run_bearer_contact(
        left,
        right,
        bearer=ScriptedInMemoryLink(
            ScriptedImpairmentPlan(
                left_to_right=(ImpairmentAction.DELIVER_UNCERTAIN,)
            )
        ),
        contact_budget=full_budget(),
    )
    assert uncertain.outcome is BearerContactOutcome.SENDER_UNCERTAIN
    assert uncertain.sender_uncertainties == uncertain.durable_records_committed == 1
    assert uncertain.remaining_missing_work == 0
    close_node(left)
    close_node(right)

    left = reopen_node(left_root, "left-reopened")
    right = reopen_node(right_root, "right-reopened")
    resumed = run_bearer_contact(
        left,
        right,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
    )
    assert resumed.outcome is BearerContactOutcome.NO_MORE_ELIGIBLE_WORK
    assert resumed.bearer_attempts == resumed.durable_records_committed == 0
    assert right.query_results.get_query(query(1).query_id) == query(1)
    close_node(left)
    close_node(right)


def test_loss_before_commit_survives_restart_as_missing_work(tmp_path: Path) -> None:
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left = persistent_node(left_root, "left")
    right = persistent_node(right_root, "right")
    left.query_results.add_query(query(1))
    lost = run_bearer_contact(
        left,
        right,
        bearer=ScriptedInMemoryLink(
            ScriptedImpairmentPlan(default_left_to_right=ImpairmentAction.DROP)
        ),
        contact_budget=full_budget(),
    )
    assert lost.durable_records_committed == 0
    close_node(left)
    close_node(right)

    left = reopen_node(left_root, "left-reopened")
    right = reopen_node(right_root, "right-reopened")
    assert right.query_results.query_count == 0
    resumed = run_bearer_contact(
        left,
        right,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
    )
    assert resumed.bearer_attempts == resumed.durable_records_committed == 1
    assert right.query_results.get_query(query(1).query_id) == query(1)
    close_node(left)
    close_node(right)


def test_real_subprocess_created_state_is_committed_reopened_and_skipped(
    tmp_path: Path,
) -> None:
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    repository = Path(__file__).parents[1]
    code = """
from pathlib import Path
import sys
from pollicino.net.persistent_catalog import PersistentBoundedReferenceCatalog
from pollicino.net.persistent_query import PersistentQueryResultStore
from pollicino.net.query import QueryRecord
root = Path(sys.argv[1])
root.mkdir()
catalog = PersistentBoundedReferenceCatalog(root / 'catalog')
store = PersistentQueryResultStore(root / 'query-result')
store.add_query(QueryRecord(b'process-query', b'opaque-process-payload'))
catalog.close()
store.close()
"""
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(repository / "src")
    completed = subprocess.run(
        [sys.executable, "-c", code, str(left_root)],
        cwd=repository,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr

    left = reopen_node(left_root, "left-parent")
    right = persistent_node(right_root, "right-parent")
    first = run_bearer_contact(
        left,
        right,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
    )
    assert first.durable_records_committed == 1
    close_node(left)
    close_node(right)

    left = reopen_node(left_root, "left-second-process-boundary")
    right = reopen_node(right_root, "right-second-process-boundary")
    second = run_bearer_contact(
        left,
        right,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
    )
    assert second.bearer_attempts == second.durable_records_committed == 0
    assert (
        right.query_results.get_query(b"process-query").opaque_query
        == b"opaque-process-payload"
    )
    close_node(left)
    close_node(right)


def test_105_queries_and_results_reopen_and_converge_across_bounded_contacts(
    tmp_path: Path,
) -> None:
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left = persistent_node(left_root, "left")
    right = persistent_node(right_root, "right")
    left.query_results.add_queries(query(index) for index in range(105))
    left.query_results.add_results(result(index, index) for index in range(105))

    reports = []
    for contact_index in range(3):
        report = run_bearer_contact(
            left,
            right,
            bearer=ScriptedInMemoryLink(),
            contact_budget=full_budget(),
        )
        reports.append(report)
        close_node(left)
        close_node(right)
        left = reopen_node(left_root, f"left-{contact_index}")
        right = reopen_node(right_root, f"right-{contact_index}")

    assert [report.durable_records_committed for report in reports] == [100, 100, 10]
    assert right.query_results.query_count == 105
    assert right.query_results.result_count == 105
    assert right.query_results.canonical_state() == left.query_results.canonical_state()
    final = run_bearer_contact(
        left,
        right,
        bearer=ScriptedInMemoryLink(),
        contact_budget=full_budget(),
    )
    assert final.bearer_attempts == 0
    close_node(left)
    close_node(right)
