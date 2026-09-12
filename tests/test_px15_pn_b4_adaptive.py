from __future__ import annotations

from pathlib import Path

import pytest

from pollicino.net.endpoint import RecordKind
from px10_support import persistent_endpoint, query
from px15_support import run_fragment_worker


def _seed(root: Path, count: int) -> None:
    endpoint = persistent_endpoint(root, "seed")
    endpoint.query_results.add_queries(query(index) for index in range(count))
    endpoint.close()


@pytest.mark.parametrize(
    ("difference", "expected"),
    ((0, "EQUAL"), (1, "DECODED"), (10, "DECODED"),
     (100, "CAPACITY_EXCEEDED"), (1_000, "CAPACITY_EXCEEDED")),
)
def test_oracle_blind_capacity_10_policy_crosses_fragment_boundary(
    tmp_path: Path, difference: int, expected: str
) -> None:
    source_root, receiver_root = tmp_path / "source", tmp_path / "receiver"
    _seed(source_root, 1_000)
    _seed(receiver_root, 1_000 - difference)
    start = run_fragment_worker(
        source_root, "adaptive-start", mtu=128, kind=RecordKind.QUERY
    )
    assert start.returncode == 0
    assert start.diagnostics["decision"] == "COMPACT_10"
    assert len(start.frame_groups) == 1 and len(start.frame_groups[0]) == 11
    response = run_fragment_worker(
        receiver_root,
        "consume",
        mtu=128,
        frame_groups=start.frame_groups,
        role="RESPONDER",
        read_size=1,
    )
    assert response.returncode == 0
    assert response.diagnostics["compact_statuses"] == [expected]
    if expected == "CAPACITY_EXCEEDED":
        fallback = run_fragment_worker(
            source_root,
            "consume",
            mtu=128,
            frame_groups=response.frame_groups,
            role="INITIATOR",
        )
        assert fallback.returncode == 0
        assert fallback.frame_groups

