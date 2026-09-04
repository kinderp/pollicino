from __future__ import annotations

from pathlib import Path

from pollicino.net.bearer import ImpairmentAction, LinkDirection, ScriptedImpairmentPlan
from pollicino.net.catalog import BoundedReference
from pollicino.net.endpoint import (
    B2ContactOutcome,
    B2ContactSelection,
    B2MessageType,
    EncodedBearerAttemptResult,
    ScriptedEncodedMessageLink,
    decode_message,
    message_type,
    run_independent_contact,
)
from px10_support import persistent_endpoint, query, reopen_endpoint, result


class UncertainFirstRecordLink:
    def __init__(self) -> None:
        self.used = False

    def attempt(self, direction: LinkDirection, encoded: bytes) -> EncodedBearerAttemptResult:
        if message_type(decode_message(encoded)) is B2MessageType.RECORD and not self.used:
            self.used = True
            return EncodedBearerAttemptResult(
                ImpairmentAction.DELIVER_UNCERTAIN, (encoded,), False
            )
        return EncodedBearerAttemptResult(ImpairmentAction.DELIVER, (encoded,), True)


class DisconnectFirstSelectionLink:
    def __init__(self) -> None:
        self.used = False

    def attempt(self, direction: LinkDirection, encoded: bytes) -> EncodedBearerAttemptResult:
        if (
            message_type(decode_message(encoded))
            is B2MessageType.REFERENCE_SELECTION
            and not self.used
        ):
            self.used = True
            return EncodedBearerAttemptResult(
                ImpairmentAction.DISCONNECT, (), False, disconnected=True
            )
        return EncodedBearerAttemptResult(ImpairmentAction.DELIVER, (encoded,), True)


def test_b2_lossy_restart_mule_and_explicit_reference_flow(tmp_path: Path) -> None:
    roots = {name: tmp_path / name for name in ("a", "b", "c")}
    a = persistent_endpoint(roots["a"], "A")
    b = persistent_endpoint(roots["b"], "B")
    c = persistent_endpoint(roots["c"], "semantic-blind-C")
    carried_query = query(7, b"opaque-interest")
    a.query_results.add_query(carried_query)

    metadata_lost = run_independent_contact(
        a.endpoint,
        c.endpoint,
        bearer=ScriptedEncodedMessageLink(
            ScriptedImpairmentPlan(left_to_right=(ImpairmentAction.DROP,))
        ),
    )
    assert metadata_lost.outcome is B2ContactOutcome.PARTIAL_NOT_DELIVERED
    assert c.query_results.query_count == 0
    assert run_independent_contact(
        a.endpoint, c.endpoint, bearer=ScriptedEncodedMessageLink()
    ).durable_commits == 1
    c.close()
    c = reopen_endpoint(roots["c"], "semantic-blind-C-query-restart")

    assert run_independent_contact(
        c.endpoint, b.endpoint, bearer=ScriptedEncodedMessageLink()
    ).durable_commits == 1
    assert b.query_results.get_query(carried_query.query_id) == carried_query

    carried_result = result(7, 11, (b"selected-key",))
    b.query_results.add_result(carried_result)
    uncertain = run_independent_contact(
        b.endpoint, c.endpoint, bearer=UncertainFirstRecordLink()
    )
    assert uncertain.outcome is B2ContactOutcome.SENDER_UNCERTAIN
    assert uncertain.durable_commits == 1
    c.close()
    c = reopen_endpoint(roots["c"], "semantic-blind-C-result-restart")
    assert run_independent_contact(
        c.endpoint, a.endpoint, bearer=ScriptedEncodedMessageLink()
    ).durable_commits == 1
    assert a.query_results.get_result(carried_result.identity) == carried_result

    # Result discovery does not select the D2 reference or mutate authority.
    authority_events: list[str] = []
    assert len(a.catalog) == len(c.catalog) == 0
    selected = BoundedReference(b"selected-key", b"opaque-reference")
    b.catalog.add(selected)
    disconnected = run_independent_contact(
        b.endpoint,
        c.endpoint,
        bearer=DisconnectFirstSelectionLink(),
        selection=B2ContactSelection(right_wants_from_left=(selected.logical_key,)),
    )
    assert disconnected.outcome is B2ContactOutcome.DISCONNECTED
    assert len(c.catalog) == 0
    assert run_independent_contact(
        b.endpoint,
        c.endpoint,
        bearer=ScriptedEncodedMessageLink(),
        selection=B2ContactSelection(right_wants_from_left=(selected.logical_key,)),
    ).durable_commits == 1
    c.close()
    c = reopen_endpoint(roots["c"], "semantic-blind-C-reference-restart")
    assert run_independent_contact(
        c.endpoint,
        a.endpoint,
        bearer=ScriptedEncodedMessageLink(),
        selection=B2ContactSelection(right_wants_from_left=(selected.logical_key,)),
    ).durable_commits == 1
    assert a.catalog.get(selected.logical_key) == selected
    assert authority_events == []
    a.close(); b.close(); c.close()
