from __future__ import annotations

import hashlib

import pytest

from pollicino.net.bearer import ImpairmentAction, LinkDirection
from pollicino.net.catalog import BoundedReference
from pollicino.net.endpoint import (
    AdvertisementMessage,
    AdvertisedIdentity,
    B2ContactOutcome,
    B2ContactSelection,
    B2DecodeError,
    EncodedBearerAttemptResult,
    RecordKind,
    RequestMessage,
    ScriptedEncodedMessageLink,
    decode_message,
    encode_message,
    message_type,
    run_independent_contact,
)
from pollicino.net.query import QueryConflictError, QueryRecord, ResultRecord
from px10_support import memory_endpoint, query, reference


class CorruptingBearer:
    def attempt(self, direction: LinkDirection, encoded: bytes) -> EncodedBearerAttemptResult:
        changed = bytearray(encoded)
        changed[-1] ^= 0x01
        return EncodedBearerAttemptResult(
            ImpairmentAction.DELIVER, (bytes(changed),), True
        )


class TruncatingBearer:
    def attempt(self, direction: LinkDirection, encoded: bytes) -> EncodedBearerAttemptResult:
        return EncodedBearerAttemptResult(
            ImpairmentAction.DELIVER, (encoded[:-1],), True
        )


class CorruptFirstRecordBearer:
    def attempt(self, direction: LinkDirection, encoded: bytes) -> EncodedBearerAttemptResult:
        if message_type(decode_message(encoded)).name == "RECORD":
            changed = bytearray(encoded)
            changed[-1] ^= 0x01
            return EncodedBearerAttemptResult(
                ImpairmentAction.DELIVER, (bytes(changed),), True
            )
        return EncodedBearerAttemptResult(ImpairmentAction.DELIVER, (encoded,), True)


class DuplicateFirstRecordBearer:
    def __init__(self) -> None:
        self.used = False

    def attempt(self, direction: LinkDirection, encoded: bytes) -> EncodedBearerAttemptResult:
        if message_type(decode_message(encoded)).name == "RECORD" and not self.used:
            self.used = True
            return EncodedBearerAttemptResult(
                ImpairmentAction.DUPLICATE, (encoded, encoded), True
            )
        return EncodedBearerAttemptResult(ImpairmentAction.DELIVER, (encoded,), True)


@pytest.mark.parametrize("bearer", (CorruptingBearer(), TruncatingBearer()))
def test_corrupt_or_truncated_message_fails_closed_without_mutation(bearer) -> None:
    left = memory_endpoint("left")
    right = memory_endpoint("right")
    left.query_results.add_query(query(1))
    before = right.query_results.canonical_state()
    report = run_independent_contact(left.endpoint, right.endpoint, bearer=bearer)
    assert report.outcome is B2ContactOutcome.ERROR
    assert report.error_code == "B2_DECODE_ERROR"
    assert report.decode_failures == 1
    assert right.query_results.canonical_state() == before


def test_corrupt_complete_record_fails_before_native_apply() -> None:
    left = memory_endpoint("left")
    right = memory_endpoint("right")
    left.query_results.add_query(query(1))
    report = run_independent_contact(
        left.endpoint, right.endpoint, bearer=CorruptFirstRecordBearer()
    )
    assert report.outcome is B2ContactOutcome.ERROR
    assert report.decode_failures == 1
    assert report.native_apply_failures == 0
    assert right.query_results.query_count == 0


@pytest.mark.parametrize("kind", (RecordKind.QUERY, RecordKind.RESULT, RecordKind.REFERENCE))
def test_duplicate_encoded_records_are_native_idempotent_for_every_kind(
    kind: RecordKind,
) -> None:
    left = memory_endpoint("left")
    right = memory_endpoint("right")
    selection = B2ContactSelection()
    if kind is RecordKind.QUERY:
        left.query_results.add_query(query(1))
    elif kind is RecordKind.RESULT:
        left.query_results.add_result(ResultRecord(b"q", b"r", (b"key",)))
    else:
        selected = reference(1)
        left.catalog.add(selected)
        selection = B2ContactSelection(
            right_wants_from_left=(selected.logical_key,)
        )
    report = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=DuplicateFirstRecordBearer(),
        selection=selection,
    )
    assert report.outcome is B2ContactOutcome.NO_MORE_PLANNED_WORK
    assert report.duplicate_presentations == 1
    assert report.durable_commits == 1
    assert report.already_known_records_skipped >= 1


@pytest.mark.parametrize("kind", (RecordKind.QUERY, RecordKind.RESULT, RecordKind.REFERENCE))
def test_conflicting_known_identity_fails_closed_from_digest_metadata(kind: RecordKind) -> None:
    left = memory_endpoint("left")
    right = memory_endpoint("right")
    selection = B2ContactSelection()
    if kind is RecordKind.QUERY:
        left.query_results.add_query(QueryRecord(b"same", b"left"))
        right.query_results.add_query(QueryRecord(b"same", b"right"))
        before = right.query_results.canonical_state()
        expected = "QUERY_CONFLICT"
    elif kind is RecordKind.RESULT:
        left.query_results.add_result(ResultRecord(b"q", b"same", (b"left",)))
        right.query_results.add_result(ResultRecord(b"q", b"same", (b"right",)))
        before = right.query_results.canonical_state()
        expected = "RESULT_CONFLICT"
    else:
        left.catalog.add(BoundedReference(b"same", b"left"))
        right.catalog.add(BoundedReference(b"same", b"right"))
        before = right.catalog.canonical_state()
        expected = "REFERENCE_CONFLICT"
        selection = B2ContactSelection(right_wants_from_left=(b"same",))
    report = run_independent_contact(
        left.endpoint,
        right.endpoint,
        bearer=ScriptedEncodedMessageLink(),
        selection=selection,
    )
    assert report.outcome is B2ContactOutcome.ERROR
    assert report.error_code == expected
    assert report.native_validation_failures == 1
    after = (
        right.catalog.canonical_state()
        if kind is RecordKind.REFERENCE
        else right.query_results.canonical_state()
    )
    assert after == before


def _deliver(link, direction, receiver, encoded):
    attempt = link.attempt(direction, encoded)
    assert len(attempt.presentations) == 1
    return receiver.receive_message(attempt.presentations[0])


def test_stale_advertisement_is_safe_and_later_fresh_contact_recovers() -> None:
    left = memory_endpoint("left")
    right = memory_endpoint("right")
    left.query_results.add_query(query(1))
    stale = next(left.endpoint.advertisement_messages(RecordKind.QUERY))
    left.query_results.add_query(query(2))

    link = ScriptedEncodedMessageLink()
    request_result = _deliver(
        link, LinkDirection.LEFT_TO_RIGHT, right.endpoint, stale
    )
    assert len(request_result.outbound_messages) == 1
    records = _deliver(
        link,
        LinkDirection.RIGHT_TO_LEFT,
        left.endpoint,
        request_result.outbound_messages[0],
    )
    assert len(records.outbound_messages) == 1
    applied = _deliver(
        link,
        LinkDirection.LEFT_TO_RIGHT,
        right.endpoint,
        records.outbound_messages[0],
    )
    assert applied.durable_commits == 1
    assert right.query_results.query_count == 1

    fresh = run_independent_contact(
        left.endpoint, right.endpoint, bearer=ScriptedEncodedMessageLink()
    )
    assert fresh.durable_commits == 1
    assert right.query_results.canonical_state() == left.query_results.canonical_state()


def test_request_and_record_can_arrive_before_advertisement_without_session_state() -> None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_query(query(1))
    request = encode_message(RequestMessage(RecordKind.QUERY, (query(1).query_id,)))
    link = ScriptedEncodedMessageLink()
    records = _deliver(link, LinkDirection.RIGHT_TO_LEFT, source.endpoint, request)
    assert len(records.outbound_messages) == 1
    applied = _deliver(
        link,
        LinkDirection.LEFT_TO_RIGHT,
        receiver.endpoint,
        records.outbound_messages[0],
    )
    assert applied.durable_commits == 1

    advertisement = next(source.endpoint.advertisement_messages(RecordKind.QUERY))
    known = _deliver(
        link, LinkDirection.LEFT_TO_RIGHT, receiver.endpoint, advertisement
    )
    assert known.outbound_messages == ()
    assert known.already_known == 1


def test_structurally_valid_false_digest_cannot_mutate_known_state() -> None:
    receiver = memory_endpoint("receiver")
    receiver.query_results.add_query(query(1))
    false = AdvertisementMessage(
        RecordKind.QUERY,
        (AdvertisedIdentity(query(1).query_id, hashlib.sha256(b"false").digest()),),
    )
    before = receiver.query_results.canonical_state()
    with pytest.raises(QueryConflictError, match="different bytes"):
        receiver.endpoint.receive_message(encode_message(false))
    assert receiver.query_results.canonical_state() == before


def test_receiver_quota_failure_keeps_prior_record_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pollicino.net.query as query_module

    left = memory_endpoint("left")
    right = memory_endpoint("right")
    left.query_results.add_queries((query(1), query(2)))
    monkeypatch.setattr(query_module, "MAX_STORED_QUERIES", 1)
    report = run_independent_contact(
        left.endpoint, right.endpoint, bearer=ScriptedEncodedMessageLink()
    )
    assert report.outcome is B2ContactOutcome.ERROR
    assert report.error_code == "QUERY_RESULT_BOUNDS_ERROR"
    assert report.native_apply_failures == 1
    assert report.durable_commits == 1
    assert right.query_results.query_count == 1
    assert right.query_results.get_query(query(1).query_id) == query(1)


def test_decode_rejects_oversize_input_before_allocation_or_interpretation() -> None:
    from pollicino.net.endpoint import MAX_B2_MESSAGE_BYTES

    with pytest.raises(B2DecodeError, match="maximum"):
        decode_message(b"x" * (MAX_B2_MESSAGE_BYTES + 1))
