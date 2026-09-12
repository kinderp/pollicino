from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True, slots=True)
class RapidReplicaEstimate:
    """One replica's direct-delivery estimate for RAPID utility math.

    ``meetings_needed`` represents how many destination meetings are expected
    before this packet can be served from the carrier's destination queue. The
    simplest uncongested case is 1.
    """

    carrier_id: str
    mean_direct_meeting_seconds: float
    meetings_needed: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.carrier_id, str) or not self.carrier_id:
            raise ValueError("carrier_id must be a non-empty string")
        if (
            isinstance(self.mean_direct_meeting_seconds, bool)
            or not isinstance(self.mean_direct_meeting_seconds, (int, float))
            or not math.isfinite(float(self.mean_direct_meeting_seconds))
            or self.mean_direct_meeting_seconds <= 0
        ):
            raise ValueError("mean_direct_meeting_seconds must be finite and positive")
        if (
            isinstance(self.meetings_needed, bool)
            or not isinstance(self.meetings_needed, int)
            or self.meetings_needed <= 0
        ):
            raise ValueError("meetings_needed must be a positive integer")

    @property
    def effective_hazard_per_second(self) -> float:
        return 1.0 / (
            float(self.mean_direct_meeting_seconds) * self.meetings_needed
        )


@dataclass(frozen=True, slots=True)
class RapidDeadlineUtility:
    remaining_useful_seconds: float
    transfer_bytes: int
    probability_before: float
    probability_after: float

    @property
    def marginal_utility(self) -> float:
        return self.probability_after - self.probability_before

    @property
    def marginal_utility_per_byte(self) -> float:
        return self.marginal_utility / self.transfer_bytes


def deadline_delivery_probability(
    remaining_useful_seconds: float,
    replicas: Sequence[RapidReplicaEstimate],
) -> float:
    """Probability of delivery before deadline under exponential meetings.

    This is the tractable independent-exponential case used as a RAPID
    inference building block. It is not a claim that real Pollicino contacts
    follow an exponential distribution.
    """

    if (
        isinstance(remaining_useful_seconds, bool)
        or not isinstance(remaining_useful_seconds, (int, float))
        or not math.isfinite(float(remaining_useful_seconds))
    ):
        raise ValueError("remaining_useful_seconds must be finite")
    if not all(isinstance(item, RapidReplicaEstimate) for item in replicas):
        raise TypeError("replicas must contain RapidReplicaEstimate values")
    if remaining_useful_seconds <= 0 or not replicas:
        return 0.0

    carrier_ids = [item.carrier_id for item in replicas]
    if len(carrier_ids) != len(set(carrier_ids)):
        raise ValueError("replica carrier IDs must be unique")

    total_hazard = sum(item.effective_hazard_per_second for item in replicas)
    probability = 1.0 - math.exp(-float(remaining_useful_seconds) * total_hazard)
    return min(1.0, max(0.0, probability))


def rapid_deadline_marginal_utility(
    *,
    remaining_useful_seconds: float,
    existing_replicas: Sequence[RapidReplicaEstimate],
    candidate_replica: RapidReplicaEstimate,
    transfer_bytes: int,
) -> RapidDeadlineUtility:
    """Evaluate RAPID deadline marginal utility for one candidate replication."""

    if not isinstance(candidate_replica, RapidReplicaEstimate):
        raise TypeError("candidate_replica must be RapidReplicaEstimate")
    if isinstance(transfer_bytes, bool) or not isinstance(transfer_bytes, int) or transfer_bytes <= 0:
        raise ValueError("transfer_bytes must be a positive integer")
    if not all(isinstance(item, RapidReplicaEstimate) for item in existing_replicas):
        raise TypeError("existing_replicas must contain RapidReplicaEstimate values")
    if any(item.carrier_id == candidate_replica.carrier_id for item in existing_replicas):
        raise ValueError("candidate carrier already holds a replica")

    before = deadline_delivery_probability(
        remaining_useful_seconds,
        existing_replicas,
    )
    after = deadline_delivery_probability(
        remaining_useful_seconds,
        (*existing_replicas, candidate_replica),
    )
    return RapidDeadlineUtility(
        remaining_useful_seconds=float(remaining_useful_seconds),
        transfer_bytes=transfer_bytes,
        probability_before=before,
        probability_after=after,
    )
