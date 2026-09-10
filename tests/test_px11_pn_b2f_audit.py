from __future__ import annotations

import inspect
from pathlib import Path

from pollicino.net.fair_reconciliation import run_fair_contact


def test_driver_has_no_direct_remote_store_reads_or_persistent_progress() -> None:
    source = inspect.getsource(run_fair_contact).lower()
    forbidden_store_reads = (
        ".catalog",
        ".query_results",
        ".state_digest",
        ".receiver_known_ids",
        ".sorted_query_ids",
        ".sorted_result_ids",
        "__catalog",
        "__query_results",
    )
    assert not any(term in source for term in forbidden_store_reads)
    forbidden_progress_authority = (
        "peer_cursor",
        "peer_offset",
        "peer_page",
        "last_advertised_identity",
        "continuation_token",
        "ack_ledger",
        "custody_log",
        "session_journal",
    )
    assert not any(term in source for term in forbidden_progress_authority)


def test_b2f_core_is_application_neutral_and_has_no_future_transport() -> None:
    module = Path(inspect.getfile(run_fair_contact)).read_text().lower()
    application_terms = (
        "faro",
        "dna",
        "delivery",
        "content",
        "topic",
        "publisher",
        "recommendation",
    )
    assert not any(term in module for term in application_terms)
    deferred = (
        "pnf1",
        "fragment_payload",
        "transmit_exact",
        "from .link import",
        "socket",
        "tcp",
        "udp",
        "bluetooth",
        "wi-fi",
        "lora",
        "freakwan",
        "serial",
    )
    assert not any(term in module for term in deferred)


def test_d4_remains_free_of_concrete_bearer_branches() -> None:
    d4 = Path(__file__).parents[1] / "src/pollicino/net/contact.py"
    source = d4.read_text().lower()
    concrete = (
        "lora",
        "freakwan",
        "bluetooth",
        "wi-fi",
        "tcp",
        "udp",
        "socket",
        "radio",
    )
    assert not any(term in source for term in concrete)
