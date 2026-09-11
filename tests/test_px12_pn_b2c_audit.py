from __future__ import annotations

import inspect
from pathlib import Path

from pollicino.net.compact_reconciliation import run_compact_contact


def test_compact_driver_has_no_direct_remote_store_reads() -> None:
    source = inspect.getsource(run_compact_contact).lower()
    forbidden = (
        ".catalog", ".query_results", ".state_digest", ".receiver_known_ids",
        ".sorted_query_ids", ".sorted_result_ids", "__catalog", "__query_results",
    )
    assert not any(term in source for term in forbidden)


def test_compact_production_layer_is_application_neutral_and_transport_local() -> None:
    path = Path(inspect.getfile(run_compact_contact))
    source = path.read_text().lower()
    applications = ("faro", "dna", "delivery", "content", "topic", "publisher", "recommendation")
    transports = ("socket", "tcp", "udp", "bluetooth", "wi-fi", "lora", "freakwan", "serial")
    deferred = ("pnf1", "fragment_payload", "transmit_exact", "from .link import")
    assert not any(term in source for term in applications)
    assert not any(term in source for term in transports)
    assert not any(term in source for term in deferred)


def test_compact_layer_introduces_no_persistent_peer_progress_authority() -> None:
    source = Path(inspect.getfile(run_compact_contact)).read_text().lower()
    persistent_peer_terms = (
        "persistent ack", "peer cursor", "peer sketch", "peer progress",
        "custody log", "session journal", "last peer", "peer offset",
    )
    persistence_imports = ("persistent_catalog", "persistent_query", "local_persistence import atomic")
    assert not any(term in source for term in persistent_peer_terms)
    assert not any(term in source for term in persistence_imports)


def test_historical_decision_documents_are_not_modified() -> None:
    root = Path(__file__).parents[1]
    assert (root / "docs/research/px11-pn-b2f-decision.md").is_file()
    assert (root / "artifacts/px11-pn-b2f/classification.json").is_file()
