from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from pollicino.net.endpoint import B2ContactBudget, ScriptedEncodedMessageLink
from pollicino.net.fair_reconciliation import FairIndependentEndpoint, run_fair_contact
from px10_support import query, result
from px11_support import fair_persistent_endpoint, reopen_fair_endpoint


def _run_subprocess(code: str, *arguments: str) -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(Path(__file__).parents[1] / "src")
    subprocess.run(
        [sys.executable, "-c", code, *arguments],
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )


def test_restart_after_every_contact_reaches_all_multipage_state(tmp_path) -> None:
    left_root = tmp_path / "left"
    right_root = tmp_path / "right"
    left = fair_persistent_endpoint(left_root, "left")
    right = fair_persistent_endpoint(right_root, "right")
    left.query_results.add_queries(query(index) for index in range(250))
    contacts = 0
    while right.query_results.query_count < 250:
        report = run_fair_contact(
            left.endpoint,
            right.endpoint,
            bearer=ScriptedEncodedMessageLink(),
            budget=B2ContactBudget(max_bearer_attempts=25),
        )
        assert report.bearer_attempts <= 25
        contacts += 1
        assert contacts <= 20
        left.close()
        right.close()
        left = reopen_fair_endpoint(left_root, "left")
        right = reopen_fair_endpoint(right_root, "right")
    assert right.query_results.canonical_state() == left.query_results.canonical_state()
    assert contacts > 1
    assert not any(
        term in path.name.lower()
        for root in (left_root, right_root)
        for path in root.rglob("*")
        for term in ("peer", "cursor", "offset", "session", "progress")
    )
    left.close()
    right.close()


def test_real_subprocess_multipage_write_contact_restart_and_verify(tmp_path) -> None:
    source_root = tmp_path / "source"
    receiver_root = tmp_path / "receiver"
    populate = """
from pathlib import Path
import sys
from pollicino.net.persistent_catalog import PersistentBoundedReferenceCatalog
from pollicino.net.persistent_query import PersistentQueryResultStore
from pollicino.net.query import QueryRecord, ResultRecord
root = Path(sys.argv[1]); root.mkdir()
catalog = PersistentBoundedReferenceCatalog(root / 'catalog')
store = PersistentQueryResultStore(root / 'query-result')
queries = tuple(QueryRecord(i.to_bytes(4, 'big'), b'q') for i in range(105))
results = tuple(ResultRecord(i.to_bytes(4, 'big'), b'r', (b'k',)) for i in range(105))
store.add_queries(queries); store.add_results(results)
catalog.close(); store.close()
"""
    _run_subprocess(populate, str(source_root))
    receiver = fair_persistent_endpoint(receiver_root, "receiver")
    source = reopen_fair_endpoint(source_root, "source")
    for _ in range(10):
        run_fair_contact(
            source.endpoint,
            receiver.endpoint,
            bearer=ScriptedEncodedMessageLink(),
            budget=B2ContactBudget(max_bearer_attempts=50),
        )
        if receiver.query_results.query_count == receiver.query_results.result_count == 105:
            break
    assert receiver.query_results.query_count == receiver.query_results.result_count == 105
    source.close()
    receiver.close()
    verify = """
from pathlib import Path
import sys
from pollicino.net.persistent_query import PersistentQueryResultStore
store = PersistentQueryResultStore(Path(sys.argv[1]) / 'query-result')
assert store.query_count == 105
assert store.result_count == 105
store.close()
"""
    _run_subprocess(verify, str(receiver_root))
