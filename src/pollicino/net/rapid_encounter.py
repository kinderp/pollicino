from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .bundle import CustodyLedger
from .contact_windows import SyntheticContactWindow
from .rapid_inference import RapidDeadlineInferenceReport, infer_rapid_deadline_replication
from .rapid_meeting_control import (
    RapidMeetingControlState,
    RapidMeetingMetadataExchangeReport,
    exchange_rapid_meeting_metadata,
)
from .rapid_queue_inference import (
    RapidQueueEntry,
    RapidTransferOpportunityEstimator,
    estimate_queue_service_from_history,
)
from .rapid_replica_control import (
    RapidReplicaControlState,
    RapidReplicaMetadataExchangeReport,
    exchange_rapid_replica_metadata,
)
from .rapid_selection import RapidDeadlineSelectionDecision, select_rapid_deadline_candidate
from .scheduling import ScheduledBundle
from .store_forward import ForwardPeer


def _require_id(name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _require_bundle_id(value: bytes) -> None:
    if not isinstance(value, bytes) or len(value) != 32:
        raise ValueError("bundle_id must be exactly 32 bytes")


def _complete_replica(item: ScheduledBundle, peer: ForwardPeer) -> bool:
    return all(peer.store.has(ref.sha256_digest) for ref in item.manifest.chunks)


def _replication_source_bytes(
    item: ScheduledBundle,
    *,
    source: ForwardPeer,
    target: ForwardPeer,
) -> int:
    return sum(
        ref.length
        for ref in item.manifest.chunks
        if source.store.has(ref.sha256_digest)
        and not target.store.has(ref.sha256_digest)
    )


@dataclass(frozen=True, slots=True)
class RapidEncounterDecisionReport:
    encounter_id: str
    source_id: str
    target_id: str
    now_s: int
    direct_delivery: bool
    direct_bundle_ids: tuple[bytes, ...]
    inferences: tuple[RapidDeadlineInferenceReport, ...]
    selection: RapidDeadlineSelectionDecision | None
    meeting_exchange: RapidMeetingMetadataExchangeReport
    replica_exchange: RapidReplicaMetadataExchangeReport
    candidate_queue_quote_count: int

    @property
    def selected_bundle_id(self) -> bytes | None:
        return None if self.selection is None else self.selection.selected_bundle_id

    @property
    def control_entry_count_lower_bound(self) -> int:
        """Count modeled control entries, deliberately not bytes.

        Candidate queue quotes are counted as one logical control item each.
        No serialization/header/authentication size is inferred.
        """

        return (
            self.meeting_exchange.total_sent_entry_count
            + self.replica_exchange.total_sent_entry_count
            + self.candidate_queue_quote_count
        )


@dataclass(slots=True)
class RapidEncounterPrototypeState:
    """Mutable per-node research state for one RAPID encounter experiment."""

    _meeting: dict[str, RapidMeetingControlState] = field(
        default_factory=dict, init=False, repr=False
    )
    _replica: dict[str, RapidReplicaControlState] = field(
        default_factory=dict, init=False, repr=False
    )
    _opportunity: dict[str, RapidTransferOpportunityEstimator] = field(
        default_factory=dict, init=False, repr=False
    )

    def meeting_state(self, peer_id: str) -> RapidMeetingControlState:
        _require_id("peer_id", peer_id)
        return self._meeting.setdefault(peer_id, RapidMeetingControlState(peer_id))

    def replica_state(self, peer_id: str) -> RapidReplicaControlState:
        _require_id("peer_id", peer_id)
        return self._replica.setdefault(peer_id, RapidReplicaControlState(peer_id))

    def opportunity_estimator(self, peer_id: str) -> RapidTransferOpportunityEstimator:
        _require_id("peer_id", peer_id)
        return self._opportunity.setdefault(
            peer_id, RapidTransferOpportunityEstimator(peer_id)
        )

    def observe_prior_meeting(
        self,
        node_a: str,
        node_b: str,
        *,
        now_s: int,
        opportunity_bytes_a_to_b: int | None = None,
        opportunity_bytes_b_to_a: int | None = None,
    ) -> None:
        """Seed genuine prior-history observations before a routing experiment.

        This is explicit historical input, not future knowledge. Meeting history
        is observed symmetrically; directional transfer-opportunity samples are
        added only when explicitly supplied.
        """

        left = self.meeting_state(node_a)
        right = self.meeting_state(node_b)
        left.observe_direct_encounter(node_b, now_s=now_s)
        right.observe_direct_encounter(node_a, now_s=now_s)
        if opportunity_bytes_a_to_b is not None:
            self.opportunity_estimator(node_a).observe(
                node_b,
                opportunity_bytes=opportunity_bytes_a_to_b,
                observed_at_s=now_s,
            )
        if opportunity_bytes_b_to_a is not None:
            self.opportunity_estimator(node_b).observe(
                node_a,
                opportunity_bytes=opportunity_bytes_b_to_a,
                observed_at_s=now_s,
            )


def _sync_local_replica_facts(
    state: RapidEncounterPrototypeState,
    bundles: Sequence[ScheduledBundle],
    *,
    peer: ForwardPeer,
    now_s: int,
) -> None:
    replica_state = state.replica_state(peer.peer_id)
    for item in bundles:
        complete = _complete_replica(item, peer)
        previous = replica_state.replica_state(item.bundle.bundle_id, peer.peer_id)
        if complete:
            replica_state.advertise_local_replica(
                item.bundle.bundle_id,
                present=True,
                now_s=now_s,
            )
        elif previous is not None and previous.present:
            replica_state.advertise_local_replica(
                item.bundle.bundle_id,
                present=False,
                now_s=now_s,
            )


def _isolated_service_meetings(
    state: RapidEncounterPrototypeState,
    item: ScheduledBundle,
    *,
    peer_id: str,
    destination_id: str,
) -> int | None:
    """Initial prototype quote: selected object alone in destination queue.

    This deliberately avoids inventing a multi-bundle queue ordering before a
    RAPID-integrated scheduling policy exists. It still captures objects that
    need several destination opportunities to complete.
    """

    entry = RapidQueueEntry(
        bundle_id=item.bundle.bundle_id,
        transfer_bytes=item.manifest.object_size,
    )
    estimate = estimate_queue_service_from_history(
        (entry,),
        bundle_id=item.bundle.bundle_id,
        destination_id=destination_id,
        opportunity_estimator=state.opportunity_estimator(peer_id),
    )
    return None if estimate is None else estimate.meetings_needed


def evaluate_rapid_encounter(
    state: RapidEncounterPrototypeState,
    bundles: Sequence[ScheduledBundle],
    *,
    source: ForwardPeer,
    target: ForwardPeer,
    ledger: CustodyLedger,
    window: SyntheticContactWindow,
    destination_ids: tuple[str, ...],
    application_deadlines: Mapping[bytes, int],
) -> RapidEncounterDecisionReport:
    """Evaluate one encounter without performing any Pollicino transfer.

    Direct delivery remains first priority. For a non-destination peer, the
    function builds conservative local RAPID inferences and runs the one-item
    selection kernel. Current-contact control state is updated, but no bundle,
    custody or store state is mutated.
    """

    if not isinstance(state, RapidEncounterPrototypeState):
        raise TypeError("state must be RapidEncounterPrototypeState")
    if not isinstance(ledger, CustodyLedger):
        raise TypeError("ledger must be CustodyLedger")
    if not isinstance(window, SyntheticContactWindow):
        raise TypeError("window must be SyntheticContactWindow")
    if source.peer_id != window.source_id or target.peer_id != window.target_id:
        raise ValueError("source/target peers must match the synthetic contact window")
    if not destination_ids or any(not isinstance(item, str) or not item for item in destination_ids):
        raise ValueError("destination_ids must contain at least one non-empty ID")
    if len(destination_ids) != len(set(destination_ids)):
        raise ValueError("destination_ids must be unique")
    if not isinstance(application_deadlines, Mapping):
        raise TypeError("application_deadlines must be a mapping")
    for bundle_id, deadline_s in application_deadlines.items():
        _require_bundle_id(bundle_id)
        if isinstance(deadline_s, bool) or not isinstance(deadline_s, int) or deadline_s < 0:
            raise ValueError("application deadlines must be non-negative integers")
    if not all(isinstance(item, ScheduledBundle) for item in bundles):
        raise TypeError("bundles must contain ScheduledBundle values")

    now_s = window.start_s
    source_meeting = state.meeting_state(source.peer_id)
    target_meeting = state.meeting_state(target.peer_id)
    source_replica = state.replica_state(source.peer_id)
    target_replica = state.replica_state(target.peer_id)

    _sync_local_replica_facts(state, bundles, peer=source, now_s=now_s)
    _sync_local_replica_facts(state, bundles, peer=target, now_s=now_s)

    source_meeting.observe_direct_encounter(target.peer_id, now_s=now_s)
    target_meeting.observe_direct_encounter(source.peer_id, now_s=now_s)
    if window.logical_source_byte_budget > 0:
        state.opportunity_estimator(source.peer_id).observe(
            target.peer_id,
            opportunity_bytes=window.logical_source_byte_budget,
            observed_at_s=now_s,
        )

    meeting_exchange = exchange_rapid_meeting_metadata(
        source_meeting,
        target_meeting,
    )
    replica_exchange = exchange_rapid_replica_metadata(
        source_replica,
        target_replica,
    )

    transferable = tuple(
        item
        for item in bundles
        if ledger.get(item.bundle.bundle_id, source.peer_id) is not None
        and _complete_replica(item, source)
        and not _complete_replica(item, target)
        and _replication_source_bytes(item, source=source, target=target) > 0
    )

    if target.peer_id in destination_ids:
        return RapidEncounterDecisionReport(
            encounter_id=window.encounter_id,
            source_id=source.peer_id,
            target_id=target.peer_id,
            now_s=now_s,
            direct_delivery=True,
            direct_bundle_ids=tuple(item.bundle.bundle_id for item in transferable),
            inferences=(),
            selection=None,
            meeting_exchange=meeting_exchange,
            replica_exchange=replica_exchange,
            candidate_queue_quote_count=0,
        )

    inferences: list[RapidDeadlineInferenceReport] = []
    quote_count = 0
    for item in transferable:
        deadline_s = application_deadlines.get(item.bundle.bundle_id)
        if deadline_s is None:
            continue
        replication_bytes = _replication_source_bytes(
            item,
            source=source,
            target=target,
        )
        source_meetings = _isolated_service_meetings(
            state,
            item,
            peer_id=source.peer_id,
            destination_id=destination_ids[0],
        )
        target_meetings = _isolated_service_meetings(
            state,
            item,
            peer_id=target.peer_id,
            destination_id=destination_ids[0],
        )
        meetings_needed: dict[str, int] = {}
        if source_meetings is not None:
            meetings_needed[source.peer_id] = source_meetings
        if target_meetings is not None:
            meetings_needed[target.peer_id] = target_meetings
            quote_count += 1

        inference = infer_rapid_deadline_replication(
            bundle_id=item.bundle.bundle_id,
            destination_id=destination_ids[0],
            candidate_id=target.peer_id,
            now_s=now_s,
            application_deadline_s=deadline_s,
            transfer_bytes=replication_bytes,
            meeting_state=source_meeting,
            replica_state=source_replica,
            meetings_needed_by_carrier=meetings_needed,
        )
        inferences.append(inference)

    selection = (
        None
        if not inferences
        else select_rapid_deadline_candidate(tuple(inferences))
    )
    return RapidEncounterDecisionReport(
        encounter_id=window.encounter_id,
        source_id=source.peer_id,
        target_id=target.peer_id,
        now_s=now_s,
        direct_delivery=False,
        direct_bundle_ids=(),
        inferences=tuple(inferences),
        selection=selection,
        meeting_exchange=meeting_exchange,
        replica_exchange=replica_exchange,
        candidate_queue_quote_count=quote_count,
    )
