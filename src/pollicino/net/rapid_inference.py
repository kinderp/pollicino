from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .rapid_deadline_utility import (
    RapidDeadlineUtility,
    RapidReplicaEstimate,
    rapid_deadline_marginal_utility,
)
from .rapid_meeting_control import RapidMeetingControlState
from .rapid_replica_control import RapidReplicaControlState


def _require_id(name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _require_bundle_id(value: bytes) -> None:
    if not isinstance(value, bytes) or len(value) != 32:
        raise ValueError("bundle_id must be exactly 32 bytes")


def _require_non_negative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _require_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class RapidDeadlineInferenceReport:
    bundle_id: bytes
    destination_id: str
    candidate_id: str
    now_s: int
    application_deadline_s: int
    transfer_bytes: int
    known_replica_carriers: tuple[str, ...]
    existing_replica_estimates: tuple[RapidReplicaEstimate, ...]
    candidate_replica_estimate: RapidReplicaEstimate | None
    missing_meeting_carriers: tuple[str, ...]
    missing_queue_carriers: tuple[str, ...]
    delivered_already: bool
    candidate_already_has_replica: bool
    deadline_passed: bool
    utility: RapidDeadlineUtility | None

    @property
    def knowledge_complete(self) -> bool:
        return not self.missing_meeting_carriers and not self.missing_queue_carriers

    @property
    def usable_for_replication_ranking(self) -> bool:
        return (
            self.utility is not None
            and self.knowledge_complete
            and not self.delivered_already
            and not self.candidate_already_has_replica
            and not self.deadline_passed
        )


def infer_rapid_deadline_replication(
    *,
    bundle_id: bytes,
    destination_id: str,
    candidate_id: str,
    now_s: int,
    application_deadline_s: int,
    transfer_bytes: int,
    meeting_state: RapidMeetingControlState,
    replica_state: RapidReplicaControlState,
    meetings_needed_by_carrier: Mapping[str, int],
    max_meeting_path_hops: int = 3,
) -> RapidDeadlineInferenceReport:
    """Combine current local RAPID knowledge without mutating control state.

    The function deliberately fails incomplete rather than ignoring a known
    replica whose meeting/queue estimate is missing; otherwise marginal utility
    would be biased upward by pretending that useful existing replicas do not
    exist.

    ``meetings_needed_by_carrier`` is explicit queue knowledge supplied by the
    caller. This facade does not invent remote queue state.
    """

    _require_bundle_id(bundle_id)
    _require_id("destination_id", destination_id)
    _require_id("candidate_id", candidate_id)
    _require_non_negative_int("now_s", now_s)
    _require_non_negative_int("application_deadline_s", application_deadline_s)
    _require_positive_int("transfer_bytes", transfer_bytes)
    _require_positive_int("max_meeting_path_hops", max_meeting_path_hops)
    if not isinstance(meeting_state, RapidMeetingControlState):
        raise TypeError("meeting_state must be RapidMeetingControlState")
    if not isinstance(replica_state, RapidReplicaControlState):
        raise TypeError("replica_state must be RapidReplicaControlState")
    if not isinstance(meetings_needed_by_carrier, Mapping):
        raise TypeError("meetings_needed_by_carrier must be a mapping")
    for carrier_id, meetings_needed in meetings_needed_by_carrier.items():
        _require_id("carrier_id", carrier_id)
        _require_positive_int("meetings_needed", meetings_needed)

    known_carriers = replica_state.known_replica_carriers(bundle_id)
    delivered_already = (
        replica_state.delivery_ack(bundle_id, destination_id) is not None
    )
    candidate_already = candidate_id in known_carriers
    deadline_passed = now_s >= application_deadline_s
    remaining = max(0, application_deadline_s - now_s)

    if delivered_already:
        utility = RapidDeadlineUtility(
            remaining_useful_seconds=float(remaining),
            transfer_bytes=transfer_bytes,
            probability_before=1.0,
            probability_after=1.0,
        )
        return RapidDeadlineInferenceReport(
            bundle_id=bundle_id,
            destination_id=destination_id,
            candidate_id=candidate_id,
            now_s=now_s,
            application_deadline_s=application_deadline_s,
            transfer_bytes=transfer_bytes,
            known_replica_carriers=known_carriers,
            existing_replica_estimates=(),
            candidate_replica_estimate=None,
            missing_meeting_carriers=(),
            missing_queue_carriers=(),
            delivered_already=True,
            candidate_already_has_replica=candidate_already,
            deadline_passed=deadline_passed,
            utility=utility,
        )

    if deadline_passed:
        utility = RapidDeadlineUtility(
            remaining_useful_seconds=0.0,
            transfer_bytes=transfer_bytes,
            probability_before=0.0,
            probability_after=0.0,
        )
        return RapidDeadlineInferenceReport(
            bundle_id=bundle_id,
            destination_id=destination_id,
            candidate_id=candidate_id,
            now_s=now_s,
            application_deadline_s=application_deadline_s,
            transfer_bytes=transfer_bytes,
            known_replica_carriers=known_carriers,
            existing_replica_estimates=(),
            candidate_replica_estimate=None,
            missing_meeting_carriers=(),
            missing_queue_carriers=(),
            delivered_already=False,
            candidate_already_has_replica=candidate_already,
            deadline_passed=True,
            utility=utility,
        )

    missing_meeting: set[str] = set()
    missing_queue: set[str] = set()
    existing_estimates: list[RapidReplicaEstimate] = []

    for carrier_id in known_carriers:
        if carrier_id == destination_id:
            # A final-destination replica without its delivery acknowledgement
            # is inconsistent control state. Do not turn it into a zero-second
            # exponential estimate; require the final ACK instead.
            missing_meeting.add(carrier_id)
            continue
        meeting_seconds = meeting_state.expected_meeting_seconds(
            carrier_id,
            destination_id,
            max_hops=max_meeting_path_hops,
        )
        meetings_needed = meetings_needed_by_carrier.get(carrier_id)
        if meeting_seconds is None or meeting_seconds <= 0:
            missing_meeting.add(carrier_id)
        if meetings_needed is None:
            missing_queue.add(carrier_id)
        if (
            meeting_seconds is not None
            and meeting_seconds > 0
            and meetings_needed is not None
        ):
            existing_estimates.append(
                RapidReplicaEstimate(
                    carrier_id=carrier_id,
                    mean_direct_meeting_seconds=float(meeting_seconds),
                    meetings_needed=meetings_needed,
                )
            )

    candidate_estimate: RapidReplicaEstimate | None = None
    if not candidate_already:
        candidate_meeting = meeting_state.expected_meeting_seconds(
            candidate_id,
            destination_id,
            max_hops=max_meeting_path_hops,
        )
        candidate_meetings_needed = meetings_needed_by_carrier.get(candidate_id)
        if candidate_meeting is None or candidate_meeting <= 0:
            missing_meeting.add(candidate_id)
        if candidate_meetings_needed is None:
            missing_queue.add(candidate_id)
        if (
            candidate_meeting is not None
            and candidate_meeting > 0
            and candidate_meetings_needed is not None
        ):
            candidate_estimate = RapidReplicaEstimate(
                carrier_id=candidate_id,
                mean_direct_meeting_seconds=float(candidate_meeting),
                meetings_needed=candidate_meetings_needed,
            )

    utility: RapidDeadlineUtility | None = None
    if (
        not missing_meeting
        and not missing_queue
        and not candidate_already
        and candidate_estimate is not None
    ):
        utility = rapid_deadline_marginal_utility(
            remaining_useful_seconds=float(remaining),
            existing_replicas=tuple(existing_estimates),
            candidate_replica=candidate_estimate,
            transfer_bytes=transfer_bytes,
        )

    return RapidDeadlineInferenceReport(
        bundle_id=bundle_id,
        destination_id=destination_id,
        candidate_id=candidate_id,
        now_s=now_s,
        application_deadline_s=application_deadline_s,
        transfer_bytes=transfer_bytes,
        known_replica_carriers=known_carriers,
        existing_replica_estimates=tuple(existing_estimates),
        candidate_replica_estimate=candidate_estimate,
        missing_meeting_carriers=tuple(sorted(missing_meeting)),
        missing_queue_carriers=tuple(sorted(missing_queue)),
        delivered_already=False,
        candidate_already_has_replica=candidate_already,
        deadline_passed=False,
        utility=utility,
    )
