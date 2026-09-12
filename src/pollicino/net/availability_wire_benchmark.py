from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .availability_reconciliation import (
    AvailabilityResearchCodec,
    availability_codec_candidates,
    decode_availability_candidate,
)
from .link import ScarceLinkProfile, TransferReport, transmit_exact
from .store import AvailabilitySummary


PNA1_BASELINE_ID = "pna1-bitmap"


@dataclass(frozen=True, slots=True)
class AvailabilityWireResult:
    representation_id: str
    source_bytes: int
    frame_count: int
    data_transmissions: int
    retransmissions: int
    ack_transmissions: int
    data_wire_bytes: int
    ack_wire_bytes: int
    total_wire_bytes: int
    exact: bool

    @classmethod
    def from_transfer(
        cls,
        representation_id: str,
        *,
        source_bytes: int,
        report: TransferReport,
        exact: bool,
    ) -> AvailabilityWireResult:
        if not isinstance(representation_id, str) or not representation_id:
            raise ValueError("representation_id must be a non-empty string")
        return cls(
            representation_id=representation_id,
            source_bytes=source_bytes,
            frame_count=report.frame_count,
            data_transmissions=report.data_transmissions,
            retransmissions=report.retransmissions,
            ack_transmissions=report.ack_transmissions,
            data_wire_bytes=report.data_wire_bytes,
            ack_wire_bytes=report.ack_wire_bytes,
            total_wire_bytes=report.total_wire_bytes,
            exact=exact,
        )


@dataclass(frozen=True, slots=True)
class AvailabilityWireBenchmarkReport:
    pna1: AvailabilityWireResult
    alternatives: tuple[AvailabilityWireResult, ...]
    evidence_class: str = "model_synthetic"

    @property
    def all_results(self) -> tuple[AvailabilityWireResult, ...]:
        return (self.pna1, *self.alternatives)

    @property
    def best(self) -> AvailabilityWireResult:
        """Smallest total wire cost; stable ID tie-break for reproducibility."""
        return min(
            self.all_results,
            key=lambda item: (item.total_wire_bytes, item.source_bytes, item.representation_id),
        )

    def result(self, representation_id: str) -> AvailabilityWireResult:
        for item in self.all_results:
            if item.representation_id == representation_id:
                return item
        raise KeyError(f"unknown availability representation: {representation_id!r}")


def benchmark_availability_wire(
    summary: AvailabilitySummary,
    *,
    profile: ScarceLinkProfile,
    transfer_id_base: int = 1,
    codecs: Sequence[AvailabilityResearchCodec] | None = None,
) -> AvailabilityWireBenchmarkReport:
    """Compare PNA1 and lossless research encodings through exact PNF1 transfer.

    Every representation sees the same deterministic ``ScarceLinkProfile``.
    The impairment oracle depends on frame sequence/attempt rather than the
    representation's transfer ID, so using distinct transfer IDs avoids ID
    collision without granting any candidate a different loss pattern for the
    same sequence positions.

    This remains MODEL_SYNTHETIC. It measures exact PNF1 framing/ACK/retry cost,
    not real LoRa airtime or capacity.
    """

    if not isinstance(summary, AvailabilitySummary):
        raise TypeError("summary must be AvailabilitySummary")
    if not isinstance(profile, ScarceLinkProfile):
        raise TypeError("profile must be ScarceLinkProfile")
    if isinstance(transfer_id_base, bool) or not isinstance(transfer_id_base, int):
        raise TypeError("transfer_id_base must be an integer")
    if not 0 <= transfer_id_base <= 0xFFFFFFFF:
        raise ValueError("transfer_id_base must fit an unsigned 32-bit integer")

    selected_codecs = (
        tuple(AvailabilityResearchCodec)
        if codecs is None
        else tuple(codecs)
    )
    if len(selected_codecs) != len(set(selected_codecs)):
        raise ValueError("availability codecs must be unique")
    if not all(isinstance(item, AvailabilityResearchCodec) for item in selected_codecs):
        raise TypeError("codecs must contain AvailabilityResearchCodec values")
    if transfer_id_base + len(selected_codecs) > 0xFFFFFFFF:
        raise ValueError("transfer_id range exceeds unsigned 32-bit space")

    pna1_payload = summary.encode()
    received, pna1_report = transmit_exact(
        pna1_payload,
        transfer_id=transfer_id_base,
        profile=profile,
    )
    pna1_exact = AvailabilitySummary.decode(received) == summary
    pna1 = AvailabilityWireResult.from_transfer(
        PNA1_BASELINE_ID,
        source_bytes=len(pna1_payload),
        report=pna1_report,
        exact=pna1_exact,
    )

    encoded_by_codec = {
        candidate.codec: candidate.encoded
        for candidate in availability_codec_candidates(summary)
    }
    alternatives = []
    for offset, codec in enumerate(selected_codecs, start=1):
        payload = encoded_by_codec[codec]
        received, transfer = transmit_exact(
            payload,
            transfer_id=transfer_id_base + offset,
            profile=profile,
        )
        exact = decode_availability_candidate(received) == summary
        alternatives.append(
            AvailabilityWireResult.from_transfer(
                codec.name.lower(),
                source_bytes=len(payload),
                report=transfer,
                exact=exact,
            )
        )

    if not pna1.exact or not all(item.exact for item in alternatives):
        raise AssertionError("availability wire benchmark lost exact state")
    return AvailabilityWireBenchmarkReport(
        pna1=pna1,
        alternatives=tuple(alternatives),
    )
