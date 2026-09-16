from __future__ import annotations

from dataclasses import dataclass
import math

from .rapid_control_wire import (
    RapidControlWireBreakdown,
    RapidControlWireProfile,
    account_rapid_control_wire,
)
from .rapid_schedule import RapidScheduleReport


def meetings_needed_from_shared_opportunity_quote(
    transfer_bytes: int,
    *,
    mean_opportunity_bytes: float,
) -> int:
    """Derive isolated-object service meetings from one shared opportunity mean.

    This is the same arithmetic used by the current isolated queue prototype,
    but makes explicit why a per-bundle ``meetings_needed`` quote is redundant
    when many candidate objects share one carrier/destination opportunity mean.
    It is a research helper, not a production control format.
    """

    if isinstance(transfer_bytes, bool) or not isinstance(transfer_bytes, int) or transfer_bytes <= 0:
        raise ValueError("transfer_bytes must be a positive integer")
    if (
        isinstance(mean_opportunity_bytes, bool)
        or not isinstance(mean_opportunity_bytes, (int, float))
        or not math.isfinite(float(mean_opportunity_bytes))
        or mean_opportunity_bytes <= 0
    ):
        raise ValueError("mean_opportunity_bytes must be finite and positive")
    return max(1, math.ceil(transfer_bytes / float(mean_opportunity_bytes)))


def shared_opportunity_quote_entry_bytes(profile: RapidControlWireProfile) -> int:
    """Bytes for one self-contained carrier/destination opportunity estimate.

    Fields: quoting carrier, destination, mean opportunity bytes, sample count,
    last-observed timestamp. Authentication/encryption remain outside this
    MODEL_SYNTHETIC experiment.
    """

    if not isinstance(profile, RapidControlWireProfile):
        raise TypeError("profile must be RapidControlWireProfile")
    return (
        2 * profile.node_reference_bytes
        + profile.float64_bytes
        + profile.sample_count_bytes
        + profile.timestamp_bytes
    )


@dataclass(frozen=True, slots=True)
class RapidSharedOpportunityQuoteBreakdown:
    original: RapidControlWireBreakdown
    original_queue_quote_wire_bytes: int
    shared_queue_quote_wire_bytes: int
    original_queue_quote_entry_count: int
    shared_queue_quote_entry_count: int
    evidence_class: str = "model_synthetic"

    def __post_init__(self) -> None:
        if not isinstance(self.original, RapidControlWireBreakdown):
            raise TypeError("original must be RapidControlWireBreakdown")
        for name, value in (
            ("original_queue_quote_wire_bytes", self.original_queue_quote_wire_bytes),
            ("shared_queue_quote_wire_bytes", self.shared_queue_quote_wire_bytes),
            ("original_queue_quote_entry_count", self.original_queue_quote_entry_count),
            ("shared_queue_quote_entry_count", self.shared_queue_quote_entry_count),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.original_queue_quote_wire_bytes != self.original.queue_quote_wire_bytes:
            raise ValueError("original queue-byte accounting mismatch")
        if self.original_queue_quote_entry_count != self.original.queue_quote_entry_count:
            raise ValueError("original queue-entry accounting mismatch")

    @property
    def queue_wire_savings_bytes(self) -> int:
        return self.original_queue_quote_wire_bytes - self.shared_queue_quote_wire_bytes

    @property
    def modeled_control_wire_bytes(self) -> int:
        return self.original.control_wire_bytes - self.queue_wire_savings_bytes


def account_shared_opportunity_quotes(
    report: RapidScheduleReport,
    *,
    profile: RapidControlWireProfile,
    node_count: int,
) -> RapidSharedOpportunityQuoteBreakdown:
    """Re-account current RAPID decisions with one opportunity quote per window.

    The current one-selection prototype emits one logical queue quote for every
    candidate bundle. For the isolated-service model used by that prototype,
    all of those quotes are derived from the same carrier->destination observed
    opportunity mean. This experiment replaces only that redundant wire
    representation with one shared opportunity estimate per encounter that had
    at least one candidate quote.

    Routing decisions, stores, custody, meeting metadata and replica metadata
    are unchanged. This is deliberately a representation experiment rather
    than a new routing algorithm.
    """

    if not isinstance(report, RapidScheduleReport):
        raise TypeError("report must be RapidScheduleReport")
    if not isinstance(profile, RapidControlWireProfile):
        raise TypeError("profile must be RapidControlWireProfile")

    original = account_rapid_control_wire(
        report,
        profile=profile,
        node_count=node_count,
    )
    shared_entry_count = sum(
        window.encounter.candidate_queue_quote_count > 0
        for window in report.windows
    )
    if shared_entry_count == 0:
        shared_wire = 0
    else:
        # Each qualifying encounter has its own control stream because quotes
        # are exchanged at different contact times/peers.
        shared_wire = shared_entry_count * (
            profile.stream_header_bytes
            + shared_opportunity_quote_entry_bytes(profile)
        )
    return RapidSharedOpportunityQuoteBreakdown(
        original=original,
        original_queue_quote_wire_bytes=original.queue_quote_wire_bytes,
        shared_queue_quote_wire_bytes=shared_wire,
        original_queue_quote_entry_count=original.queue_quote_entry_count,
        shared_queue_quote_entry_count=shared_entry_count,
    )


def rapid_modeled_total_with_shared_opportunity_quotes(
    report: RapidScheduleReport,
    *,
    control: RapidSharedOpportunityQuoteBreakdown,
) -> int:
    if not isinstance(report, RapidScheduleReport):
        raise TypeError("report must be RapidScheduleReport")
    if not isinstance(control, RapidSharedOpportunityQuoteBreakdown):
        raise TypeError("control must be RapidSharedOpportunityQuoteBreakdown")
    return report.total_wire_bytes_excluding_rapid_control + control.modeled_control_wire_bytes
