from __future__ import annotations

import pytest

from pollicino.net.endpoint import (
    B2ContactBudget,
    B2ContactOutcome,
    B2ContactSelection,
    IndependentEndpoint,
    ScriptedEncodedMessageLink,
    run_independent_contact,
)
from pollicino.net.fair_reconciliation import (
    FairContactSelection,
    FairIndependentEndpoint,
    run_fair_contact,
)
from px10_support import query, reference, result
from px11_support import fair_memory_endpoint


def _fresh_endpoint(fixture, label: str) -> FairIndependentEndpoint:
    return FairIndependentEndpoint(fixture.catalog, fixture.query_results, label)


def _converge_queries(sender, receiver, *, horizon: int, attempts: int = 100):
    reports = []
    while receiver.query_results.query_count < sender.query_results.query_count:
        assert len(reports) < horizon
        reports.append(
            run_fair_contact(
                _fresh_endpoint(sender, "sender"),
                _fresh_endpoint(receiver, "receiver"),
                bearer=ScriptedEncodedMessageLink(),
                budget=B2ContactBudget(max_bearer_attempts=attempts),
            )
        )
    return reports


def test_px10_prefix_replay_starves_single_final_identity_negative_control() -> None:
    sender = fair_memory_endpoint("sender")
    receiver = fair_memory_endpoint("receiver")
    records = tuple(query(index) for index in range(10_000))
    sender.query_results.add_queries(records)
    receiver.query_results.add_queries(records[:-1])
    for _ in range(3):
        report = run_independent_contact(
            IndependentEndpoint(sender.catalog, sender.query_results),
            IndependentEndpoint(receiver.catalog, receiver.query_results),
            bearer=ScriptedEncodedMessageLink(),
        )
        assert report.outcome is B2ContactOutcome.BUDGET_EXHAUSTED
        assert report.durable_commits == 0
    assert receiver.query_results.query_count == 9_999


def test_single_lexicographically_final_identity_is_not_starved_at_10k() -> None:
    sender = fair_memory_endpoint("sender")
    receiver = fair_memory_endpoint("receiver")
    records = tuple(query(index) for index in range(10_000))
    sender.query_results.add_queries(records)
    receiver.query_results.add_queries(records[:-1])
    report = run_fair_contact(
        _fresh_endpoint(sender, "sender"),
        _fresh_endpoint(receiver, "receiver"),
        bearer=ScriptedEncodedMessageLink(),
    )
    assert report.outcome is B2ContactOutcome.NO_MORE_PLANNED_WORK
    assert report.durable_commits == 1
    assert report.pages_reached == 200
    assert report.pages_repeated == 199
    assert receiver.query_results.get_query(records[-1].query_id) == records[-1]


def test_maximum_state_late_item_needs_bounded_eight_attempt_chain() -> None:
    sender = fair_memory_endpoint("sender")
    receiver = fair_memory_endpoint("receiver")
    records = tuple(query(index) for index in range(10_000))
    sender.query_results.add_queries(records)
    receiver.query_results.add_queries(records[:-1])
    too_small = run_fair_contact(
        _fresh_endpoint(sender, "sender"),
        _fresh_endpoint(receiver, "receiver"),
        bearer=ScriptedEncodedMessageLink(),
        budget=B2ContactBudget(max_bearer_attempts=7),
    )
    assert too_small.durable_commits == 0
    assert too_small.outcome is B2ContactOutcome.BUDGET_EXHAUSTED
    enough = run_fair_contact(
        _fresh_endpoint(sender, "sender"),
        _fresh_endpoint(receiver, "receiver"),
        bearer=ScriptedEncodedMessageLink(),
        budget=B2ContactBudget(max_bearer_attempts=8),
    )
    assert enough.durable_commits == 1
    assert receiver.query_results.query_count == 10_000


def test_late_missing_suffix_at_catalog_maximum_eventually_converges() -> None:
    sender = fair_memory_endpoint("sender")
    receiver = fair_memory_endpoint("receiver")
    records = tuple(query(index) for index in range(10_000))
    sender.query_results.add_queries(records)
    receiver.query_results.add_queries(records[:9_000])
    reports = _converge_queries(sender, receiver, horizon=20)
    assert receiver.query_results.canonical_state() == sender.query_results.canonical_state()
    assert sum(report.durable_commits for report in reports) == 1_000
    assert len(reports) > 1


@pytest.mark.parametrize("size", (100, 101, 1_000))
def test_static_query_sets_converge_across_fresh_contacts(size: int) -> None:
    sender = fair_memory_endpoint("sender")
    receiver = fair_memory_endpoint("receiver")
    sender.query_results.add_queries(query(index) for index in range(size))
    reports = _converge_queries(sender, receiver, horizon=60, attempts=25)
    assert receiver.query_results.canonical_state() == sender.query_results.canonical_state()
    assert sum(report.durable_commits for report in reports) == size
    assert all(report.bearer_attempts <= 25 for report in reports)


def test_alternating_and_sparse_missing_identities_do_not_starve() -> None:
    records = tuple(query(index) for index in range(1_000))
    for known in (
        tuple(record for index, record in enumerate(records) if index % 2 == 0),
        tuple(record for index, record in enumerate(records) if index % 1000 != 999),
    ):
        sender = fair_memory_endpoint("sender")
        receiver = fair_memory_endpoint("receiver")
        sender.query_results.add_queries(records)
        receiver.query_results.add_queries(known)
        _converge_queries(sender, receiver, horizon=60, attempts=25)
        assert receiver.query_results.canonical_state() == sender.query_results.canonical_state()


def test_large_two_way_state_progresses_in_both_directions() -> None:
    left = fair_memory_endpoint("left")
    right = fair_memory_endpoint("right")
    left.query_results.add_queries(query(index) for index in range(300))
    right.query_results.add_queries(query(10_000 + index) for index in range(300))
    per_contact = []
    for _ in range(80):
        report = run_fair_contact(
            _fresh_endpoint(left, "left"),
            _fresh_endpoint(right, "right"),
            bearer=ScriptedEncodedMessageLink(),
            budget=B2ContactBudget(max_bearer_attempts=20),
        )
        per_contact.append((report.progress_left_to_right, report.progress_right_to_left))
        if left.query_results.query_count == right.query_results.query_count == 600:
            break
    assert left.query_results.canonical_state() == right.query_results.canonical_state()
    assert any(ltr for ltr, _ in per_contact)
    assert any(rtl for _, rtl in per_contact)
    assert not any((ltr > 0) ^ (rtl > 0) for ltr, rtl in per_contact[:2])


def test_cross_category_lanes_all_progress_under_shared_small_budget() -> None:
    left = fair_memory_endpoint("left")
    right = fair_memory_endpoint("right")
    left.query_results.add_queries(query(index) for index in range(100))
    left.query_results.add_results(result(index, 0) for index in range(20))
    references = tuple(reference(index) for index in range(20))
    left.catalog.add_many(references)
    selected = tuple(value.logical_key for value in references)
    report = run_fair_contact(
        _fresh_endpoint(left, "left"),
        _fresh_endpoint(right, "right"),
        bearer=ScriptedEncodedMessageLink(),
        budget=B2ContactBudget(max_bearer_attempts=30),
        selection=FairContactSelection(right_wants_from_left=selected),
    )
    assert right.query_results.query_count > 0
    assert right.query_results.result_count > 0
    assert len(right.catalog) > 0
    assert report.progress_left_to_right > 0
    contacts = 1
    while (
        right.query_results.query_count != 100
        or right.query_results.result_count != 20
        or len(right.catalog) != 20
    ):
        assert contacts < 20
        run_fair_contact(
            _fresh_endpoint(left, "left"),
            _fresh_endpoint(right, "right"),
            bearer=ScriptedEncodedMessageLink(),
            budget=B2ContactBudget(max_bearer_attempts=30),
            selection=FairContactSelection(right_wants_from_left=selected),
        )
        contacts += 1
    assert right.query_results.canonical_state() == left.query_results.canonical_state()
    assert right.catalog.canonical_state() == left.catalog.canonical_state()


def test_reference_paging_is_explicit_and_can_cover_more_than_one_native_page() -> None:
    source = fair_memory_endpoint("source")
    requester = fair_memory_endpoint("requester")
    references = tuple(reference(index) for index in range(250))
    source.catalog.add_many(references)
    selected = tuple(value.logical_key for value in references)
    for _ in range(60):
        run_fair_contact(
            _fresh_endpoint(requester, "requester"),
            _fresh_endpoint(source, "source"),
            bearer=ScriptedEncodedMessageLink(),
            budget=B2ContactBudget(max_bearer_attempts=25),
            selection=FairContactSelection(left_wants_from_right=selected),
        )
        if len(requester.catalog) == len(source.catalog):
            break
    assert requester.catalog.canonical_state() == source.catalog.canonical_state()

    unselected = fair_memory_endpoint("unselected")
    report = run_fair_contact(
        _fresh_endpoint(unselected, "unselected"),
        _fresh_endpoint(source, "source"),
        bearer=ScriptedEncodedMessageLink(),
    )
    assert report.durable_commits == 0
    assert len(unselected.catalog) == 0


def test_final_selected_reference_is_reachable_at_catalog_maximum() -> None:
    source = fair_memory_endpoint("source")
    requester = fair_memory_endpoint("requester")
    references = tuple(reference(index) for index in range(10_000))
    source.catalog.add_many(references)
    requester.catalog.add_many(references[:-1])
    selected = tuple(value.logical_key for value in references)
    report = run_fair_contact(
        _fresh_endpoint(requester, "requester"),
        _fresh_endpoint(source, "source"),
        bearer=ScriptedEncodedMessageLink(),
        selection=FairContactSelection(left_wants_from_right=selected),
    )
    assert report.durable_commits == 1
    assert requester.catalog.canonical_state() == source.catalog.canonical_state()


def test_result_paging_uses_candidate_keys_only_and_does_not_pull_references() -> None:
    source = fair_memory_endpoint("source")
    receiver = fair_memory_endpoint("receiver")
    records = tuple(result(index, 0) for index in range(1_000))
    source.query_results.add_results(records)
    for _ in range(60):
        run_fair_contact(
            _fresh_endpoint(source, "source"),
            _fresh_endpoint(receiver, "receiver"),
            bearer=ScriptedEncodedMessageLink(),
            budget=B2ContactBudget(max_bearer_attempts=25),
        )
        if receiver.query_results.result_count == 1_000:
            break
    assert receiver.query_results.canonical_state() == source.query_results.canonical_state()
    assert len(receiver.catalog) == 0


def test_one_lane_needs_five_attempts_for_first_commit() -> None:
    source = fair_memory_endpoint("source")
    receiver = fair_memory_endpoint("receiver")
    source.query_results.add_query(query(1))
    too_small = run_fair_contact(
        _fresh_endpoint(source, "source"),
        _fresh_endpoint(receiver, "receiver"),
        bearer=ScriptedEncodedMessageLink(),
        budget=B2ContactBudget(max_bearer_attempts=4),
    )
    assert too_small.durable_commits == 0
    assert too_small.outcome is B2ContactOutcome.BUDGET_EXHAUSTED
    enough = run_fair_contact(
        _fresh_endpoint(source, "source"),
        _fresh_endpoint(receiver, "receiver"),
        bearer=ScriptedEncodedMessageLink(),
        budget=B2ContactBudget(max_bearer_attempts=5),
    )
    assert enough.durable_commits == 1
