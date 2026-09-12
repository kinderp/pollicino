from __future__ import annotations

from dataclasses import dataclass

from .availability_reconciliation import decode_availability_candidate
from .availability_wire_benchmark import (
    PNA1_BASELINE_ID,
    AvailabilityWireBenchmarkReport,
    benchmark_availability_wire,
)
from .link import ScarceLinkProfile
from .store import AvailabilitySummary
from .wire import DiscoveryDescriptor


@dataclass(frozen=True, slots=True)
class AvailabilityNegotiationDecision:
    source_supports_alternative: bool
    receiver_supports_alternative: bool
    representation_id: str
    payload: bytes
    modeled_wire_bytes: int
    evidence_class: str = "model_synthetic"

    @property
    def uses_pna1(self) -> bool:
        return self.representation_id == PNA1_BASELINE_ID


def _validate_capability_bit(capability_bit: int) -> None:
    if (
        isinstance(capability_bit, bool)
        or not isinstance(capability_bit, int)
        or capability_bit <= 0
        or capability_bit > 0x8000
        or capability_bit & (capability_bit - 1)
    ):
        raise ValueError("capability_bit must be one bit in the 16-bit PND1 mask")


def select_availability_response(
    summary: AvailabilitySummary,
    *,
    source_descriptor: DiscoveryDescriptor,
    receiver_supports_alternative: bool,
    capability_bit: int,
    profile: ScarceLinkProfile,
) -> AvailabilityNegotiationDecision:
    """Research selection of PNA1 vs a lossless alternative.

    PND1 already carries a fixed-width 16-bit ``capability_mask``. This helper
    intentionally does **not** reserve a production bit. The caller supplies a
    one-bit research mask so experiments can test backward-compatible behavior
    without changing PND1's wire format.

    Rules:
    - if either side lacks support, return ordinary PNA1;
    - if both support alternatives, still include PNA1 in the wire-cost race;
    - choose an alternative only when its deterministic PNF1 wire cost is lower.

    No new negotiation packet is modeled because the capability field already
    exists in every PND1 header. A future production specification must allocate
    and govern the actual capability bit before adoption.
    """

    if not isinstance(summary, AvailabilitySummary):
        raise TypeError("summary must be AvailabilitySummary")
    if not isinstance(source_descriptor, DiscoveryDescriptor):
        raise TypeError("source_descriptor must be DiscoveryDescriptor")
    if not isinstance(receiver_supports_alternative, bool):
        raise TypeError("receiver_supports_alternative must be bool")
    if not isinstance(profile, ScarceLinkProfile):
        raise TypeError("profile must be ScarceLinkProfile")
    _validate_capability_bit(capability_bit)

    source_supports = bool(source_descriptor.capability_mask & capability_bit)
    if not source_supports or not receiver_supports_alternative:
        benchmark = benchmark_availability_wire(
            summary,
            profile=profile,
            codecs=(),
        )
        return AvailabilityNegotiationDecision(
            source_supports_alternative=source_supports,
            receiver_supports_alternative=receiver_supports_alternative,
            representation_id=PNA1_BASELINE_ID,
            payload=summary.encode(),
            modeled_wire_bytes=benchmark.pna1.total_wire_bytes,
        )

    benchmark: AvailabilityWireBenchmarkReport = benchmark_availability_wire(
        summary,
        profile=profile,
    )
    best = benchmark.best
    if best.representation_id == PNA1_BASELINE_ID:
        payload = summary.encode()
    else:
        candidate = next(
            item
            for item in benchmark.alternatives
            if item.representation_id == best.representation_id
        )
        # Wire benchmark results intentionally don't retain payload bytes. Find
        # the encoded research candidate by re-running the lossless codec list
        # indirectly through the representation ID. Keep this lookup local so
        # negotiation does not add a second selection algorithm.
        from .availability_reconciliation import availability_codec_candidates

        encoded = {
            item.codec.name.lower(): item.encoded
            for item in availability_codec_candidates(summary)
        }
        payload = encoded[candidate.representation_id]
        if decode_availability_candidate(payload) != summary:
            raise AssertionError("selected alternative does not reconstruct availability")

    return AvailabilityNegotiationDecision(
        source_supports_alternative=True,
        receiver_supports_alternative=True,
        representation_id=best.representation_id,
        payload=payload,
        modeled_wire_bytes=best.total_wire_bytes,
    )
