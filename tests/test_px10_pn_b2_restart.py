from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from pollicino.net.bearer import ImpairmentAction, ScriptedImpairmentPlan
from pollicino.net.endpoint import (
    B2ContactOutcome,
    ScriptedEncodedMessageLink,
    run_independent_contact,
)
from px10_support import persistent_endpoint, query, reopen_endpoint, result


def test_sender_uncertainty_commit_restarts_and_is_not_retransferred(
    tmp_path: Path,
) -> None:
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left = persistent_endpoint(left_root, "left")
    right = persistent_endpoint(right_root, "right")
    left.query_results.add_query(query(1))
    uncertain = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(
                left_to_right=(
                    ImpairmentAction.DELIVER,
                    ImpairmentAction.DELIVER_UNCERTAIN,
                )
            )
        ),
    )
    assert uncertain.outcome is B2ContactOutcome.SENDER_UNCERTAIN
    assert uncertain.durable_commits == uncertain.sender_uncertainties == 1
    left.close()
    right.close()

    left = reopen_endpoint(left_root, "left-reopened")
    right = reopen_endpoint(right_root, "right-reopened")
    resumed = run_independent_contact(
        left.endpoint, right.endpoint, bearer=ScriptedEncodedMessageLink()
    )
    assert resumed.outcome is B2ContactOutcome.NO_MORE_PLANNED_WORK
    assert resumed.record_messages_sent == resumed.durable_commits == 0
    assert resumed.already_known_records_skipped >= 1
    assert right.query_results.get_query(query(1).query_id) == query(1)
    left.close()
    right.close()


def test_loss_before_commit_restarts_as_missing(tmp_path: Path) -> None:
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left = persistent_endpoint(left_root, "left")
    right = persistent_endpoint(right_root, "right")
    left.query_results.add_query(query(1))
    lost = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(
                left_to_right=(ImpairmentAction.DELIVER, ImpairmentAction.DROP)
            )
        ),
    )
    assert lost.durable_commits == 0
    left.close()
    right.close()

    left = reopen_endpoint(left_root, "left-reopened")
    right = reopen_endpoint(right_root, "right-reopened")
    assert right.query_results.query_count == 0
    resumed = run_independent_contact(
        left.endpoint, right.endpoint, bearer=ScriptedEncodedMessageLink()
    )
    assert resumed.durable_commits == 1
    left.close()
    right.close()


def test_real_subprocess_state_crosses_encoded_endpoint_boundary(tmp_path: Path) -> None:
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    repository = Path(__file__).parents[1]
    code = """
from pathlib import Path
import sys
from pollicino.net.persistent_catalog import PersistentBoundedReferenceCatalog
from pollicino.net.persistent_query import PersistentQueryResultStore
from pollicino.net.query import QueryRecord
root = Path(sys.argv[1]); root.mkdir()
catalog = PersistentBoundedReferenceCatalog(root / 'catalog')
store = PersistentQueryResultStore(root / 'query-result')
store.add_query(QueryRecord(b'process-query', b'process-opaque'))
catalog.close(); store.close()
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
    left = reopen_endpoint(left_root, "left-parent")
    right = persistent_endpoint(right_root, "right-parent")
    first = run_independent_contact(
        left.endpoint, right.endpoint, bearer=ScriptedEncodedMessageLink()
    )
    assert first.durable_commits == 1
    left.close(); right.close()
    left = reopen_endpoint(left_root, "left-again")
    right = reopen_endpoint(right_root, "right-again")
    second = run_independent_contact(
        left.endpoint, right.endpoint, bearer=ScriptedEncodedMessageLink()
    )
    assert second.record_messages_sent == 0
    assert right.query_results.get_query(b"process-query").opaque_query == b"process-opaque"
    left.close(); right.close()


def test_105_queries_and_results_reconcile_in_pages_with_restart(
    tmp_path: Path,
) -> None:
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left = persistent_endpoint(left_root, "left")
    right = persistent_endpoint(right_root, "right")
    left.query_results.add_queries(query(index) for index in range(105))
    left.query_results.add_results(result(index, index) for index in range(105))

    commits: list[int] = []
    for contact_index in range(6):
        report = run_independent_contact(
            left.endpoint, right.endpoint, bearer=ScriptedEncodedMessageLink()
        )
        commits.append(report.durable_commits)
        left.close(); right.close()
        left = reopen_endpoint(left_root, f"left-{contact_index}")
        right = reopen_endpoint(right_root, f"right-{contact_index}")
        if (
            right.query_results.query_count == 105
            and right.query_results.result_count == 105
        ):
            break

    assert sum(commits) == 210
    assert len(commits) <= 4
    assert right.query_results.query_count == 105
    assert right.query_results.result_count == 105
    assert right.query_results.canonical_state() == left.query_results.canonical_state()
    final = run_independent_contact(
        left.endpoint, right.endpoint, bearer=ScriptedEncodedMessageLink()
    )
    assert final.record_messages_sent == final.durable_commits == 0
    left.close(); right.close()
