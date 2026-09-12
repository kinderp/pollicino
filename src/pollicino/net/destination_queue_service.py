from __future__ import annotations

from dataclasses import dataclass
import math


def _positive_finite(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return numeric


def _non_negative_int(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _positive_int(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


@dataclass(frozen=True, slots=True)
class DestinationQueueServiceEstimate:
    """Minimal queue-aware service-time estimate for one destination carrier.

    This research baseline deliberately adds exactly one dimension missing from
    ``DestinationServiceStrategy``: explicit bytes already ahead of the target
    object in the carrier's destination-facing queue.

    It does not model probability, replica gossip, transitivity, deadline
    utility, future contacts or bearer-derived capacity.
    """

    mean_interval_seconds: float
    mean_opportunity_bytes: float
    bytes_ahead: int
    object_bytes: int
    meetings_needed: int
    service_seconds: float


def estimate_destination_queue_service(
    *,
    mean_interval_seconds: float,
    mean_opportunity_bytes: float,
    bytes_ahead: int,
    object_bytes: int,
) -> DestinationQueueServiceEstimate:
    """Estimate completion service time from explicit interval/opportunity/queue state."""

    interval = _positive_finite("mean_interval_seconds", mean_interval_seconds)
    opportunity = _positive_finite("mean_opportunity_bytes", mean_opportunity_bytes)
    ahead = _non_negative_int("bytes_ahead", bytes_ahead)
    size = _positive_int("object_bytes", object_bytes)

    meetings = max(1, math.ceil((ahead + size) / opportunity))
    return DestinationQueueServiceEstimate(
        mean_interval_seconds=interval,
        mean_opportunity_bytes=opportunity,
        bytes_ahead=ahead,
        object_bytes=size,
        meetings_needed=meetings,
        service_seconds=interval * meetings,
    )


def queue_service_prefers_target(
    *,
    source: DestinationQueueServiceEstimate,
    target: DestinationQueueServiceEstimate,
) -> bool:
    """Return True only for strict progress under the minimal queue-aware score."""

    if not isinstance(source, DestinationQueueServiceEstimate):
        raise TypeError("source must be DestinationQueueServiceEstimate")
    if not isinstance(target, DestinationQueueServiceEstimate):
        raise TypeError("target must be DestinationQueueServiceEstimate")
    return target.service_seconds < source.service_seconds
