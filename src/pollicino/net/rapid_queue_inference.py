from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Sequence


def _require_id(name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _require_bundle_id(value: bytes) -> None:
    if not isinstance(value, bytes) or len(value) != 32:
        raise ValueError("bundle_id must be exactly 32 bytes")


def _require_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class RapidQueueEntry:
    """One complete-object transfer waiting in a destination-facing queue."""

    bundle_id: bytes
    transfer_bytes: int

    def __post_init__(self) -> None:
        _require_bundle_id(self.bundle_id)
        _require_positive_int("transfer_bytes", self.transfer_bytes)


@dataclass(frozen=True, slots=True)
class RapidQueueServiceEstimate:
    bundle_id: bytes
    bytes_ahead: int
    transfer_bytes: int
    cumulative_bytes_through_bundle: int
    expected_transfer_bytes_per_meeting: float
    meetings_needed: int

    def __post_init__(self) -> None:
        _require_bundle_id(self.bundle_id)
        if isinstance(self.bytes_ahead, bool) or not isinstance(self.bytes_ahead, int) or self.bytes_ahead < 0:
            raise ValueError("bytes_ahead must be a non-negative integer")
        _require_positive_int("transfer_bytes", self.transfer_bytes)
        _require_positive_int(
            "cumulative_bytes_through_bundle", self.cumulative_bytes_through_bundle
        )
        if (
            isinstance(self.expected_transfer_bytes_per_meeting, bool)
            or not isinstance(self.expected_transfer_bytes_per_meeting, (int, float))
            or not math.isfinite(float(self.expected_transfer_bytes_per_meeting))
            or self.expected_transfer_bytes_per_meeting <= 0
        ):
            raise ValueError(
                "expected_transfer_bytes_per_meeting must be finite and positive"
            )
        _require_positive_int("meetings_needed", self.meetings_needed)


@dataclass(frozen=True, slots=True)
class RapidTransferOpportunityEstimate:
    peer_id: str
    sample_count: int
    mean_opportunity_bytes: float
    last_observed_at_s: int

    def __post_init__(self) -> None:
        _require_id("peer_id", self.peer_id)
        _require_positive_int("sample_count", self.sample_count)
        if (
            isinstance(self.mean_opportunity_bytes, bool)
            or not isinstance(self.mean_opportunity_bytes, (int, float))
            or not math.isfinite(float(self.mean_opportunity_bytes))
            or self.mean_opportunity_bytes <= 0
        ):
            raise ValueError("mean_opportunity_bytes must be finite and positive")
        if (
            isinstance(self.last_observed_at_s, bool)
            or not isinstance(self.last_observed_at_s, int)
            or self.last_observed_at_s < 0
        ):
            raise ValueError("last_observed_at_s must be a non-negative integer")


@dataclass(slots=True)
class RapidTransferOpportunityEstimator:
    """Local historical mean of explicit transfer opportunities per peer.

    ``opportunity_bytes`` must come from an experiment or measured adapter that
    explicitly defines the opportunity. This class never derives capacity from
    contact duration, bitrate labels or bearer kind.
    """

    node_id: str
    _sample_count: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    _mean_bytes: dict[str, float] = field(default_factory=dict, init=False, repr=False)
    _last_observed_at_s: dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        _require_id("node_id", self.node_id)

    def observe(
        self,
        peer_id: str,
        *,
        opportunity_bytes: int,
        observed_at_s: int,
    ) -> RapidTransferOpportunityEstimate:
        _require_id("peer_id", peer_id)
        if peer_id == self.node_id:
            raise ValueError("a node cannot observe a transfer opportunity with itself")
        _require_positive_int("opportunity_bytes", opportunity_bytes)
        if (
            isinstance(observed_at_s, bool)
            or not isinstance(observed_at_s, int)
            or observed_at_s < 0
        ):
            raise ValueError("observed_at_s must be a non-negative integer")
        previous_time = self._last_observed_at_s.get(peer_id)
        if previous_time is not None and observed_at_s <= previous_time:
            raise ValueError("transfer opportunity observation times must increase")

        previous_count = self._sample_count.get(peer_id, 0)
        previous_mean = self._mean_bytes.get(peer_id, 0.0)
        count = previous_count + 1
        mean = (
            float(opportunity_bytes)
            if previous_count == 0
            else previous_mean + (opportunity_bytes - previous_mean) / count
        )
        self._sample_count[peer_id] = count
        self._mean_bytes[peer_id] = mean
        self._last_observed_at_s[peer_id] = observed_at_s
        return RapidTransferOpportunityEstimate(
            peer_id=peer_id,
            sample_count=count,
            mean_opportunity_bytes=mean,
            last_observed_at_s=observed_at_s,
        )

    def estimate(self, peer_id: str) -> RapidTransferOpportunityEstimate | None:
        _require_id("peer_id", peer_id)
        count = self._sample_count.get(peer_id)
        if count is None:
            return None
        return RapidTransferOpportunityEstimate(
            peer_id=peer_id,
            sample_count=count,
            mean_opportunity_bytes=self._mean_bytes[peer_id],
            last_observed_at_s=self._last_observed_at_s[peer_id],
        )


def estimate_queue_service_meetings(
    queue: Sequence[RapidQueueEntry],
    *,
    bundle_id: bytes,
    expected_transfer_bytes_per_meeting: float,
) -> RapidQueueServiceEstimate:
    """Estimate which future meeting can complete a queued bundle.

    The queue order is explicit input from the caller. The estimator sums bytes
    ahead plus the selected object's own bytes and divides by the expected
    transfer opportunity. It is intentionally a bounded/simple approximation,
    not a hidden physical-capacity model.
    """

    _require_bundle_id(bundle_id)
    if not queue:
        raise ValueError("queue must not be empty")
    if not all(isinstance(item, RapidQueueEntry) for item in queue):
        raise TypeError("queue must contain RapidQueueEntry values")
    bundle_ids = [item.bundle_id for item in queue]
    if len(bundle_ids) != len(set(bundle_ids)):
        raise ValueError("queue bundle IDs must be unique")
    if (
        isinstance(expected_transfer_bytes_per_meeting, bool)
        or not isinstance(expected_transfer_bytes_per_meeting, (int, float))
        or not math.isfinite(float(expected_transfer_bytes_per_meeting))
        or expected_transfer_bytes_per_meeting <= 0
    ):
        raise ValueError(
            "expected_transfer_bytes_per_meeting must be finite and positive"
        )

    bytes_ahead = 0
    selected: RapidQueueEntry | None = None
    for item in queue:
        if item.bundle_id == bundle_id:
            selected = item
            break
        bytes_ahead += item.transfer_bytes
    if selected is None:
        raise KeyError("bundle_id is not present in queue")

    cumulative = bytes_ahead + selected.transfer_bytes
    meetings_needed = max(
        1,
        math.ceil(cumulative / float(expected_transfer_bytes_per_meeting)),
    )
    return RapidQueueServiceEstimate(
        bundle_id=bundle_id,
        bytes_ahead=bytes_ahead,
        transfer_bytes=selected.transfer_bytes,
        cumulative_bytes_through_bundle=cumulative,
        expected_transfer_bytes_per_meeting=float(
            expected_transfer_bytes_per_meeting
        ),
        meetings_needed=meetings_needed,
    )


def estimate_queue_service_from_history(
    queue: Sequence[RapidQueueEntry],
    *,
    bundle_id: bytes,
    destination_id: str,
    opportunity_estimator: RapidTransferOpportunityEstimator,
) -> RapidQueueServiceEstimate | None:
    """Use an observed local destination opportunity mean, or return unknown."""

    if not isinstance(opportunity_estimator, RapidTransferOpportunityEstimator):
        raise TypeError(
            "opportunity_estimator must be RapidTransferOpportunityEstimator"
        )
    estimate = opportunity_estimator.estimate(destination_id)
    if estimate is None:
        return None
    return estimate_queue_service_meetings(
        queue,
        bundle_id=bundle_id,
        expected_transfer_bytes_per_meeting=estimate.mean_opportunity_bytes,
    )
