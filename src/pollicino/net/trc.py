from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .link import ScarceLinkProfile, fragment_payload


@dataclass(frozen=True, slots=True)
class TransferWireBreakdown:
    """Non-overlapping wire accounting for one successful exact transfer.

    ``primary_*`` is one successful transmission/ACK per PNF1 frame.
    ``retransmission_*`` contains only additional traffic, so summing the four
    byte fields does not double count retransmissions.
    """

    primary_data_wire_bytes: int
    primary_ack_wire_bytes: int
    retransmission_data_wire_bytes: int
    retransmission_ack_wire_bytes: int
    unknown_remote_failure_count: int
    accounting: str

    def __post_init__(self) -> None:
        for name, value in (
            ("primary_data_wire_bytes", self.primary_data_wire_bytes),
            ("primary_ack_wire_bytes", self.primary_ack_wire_bytes),
            ("retransmission_data_wire_bytes", self.retransmission_data_wire_bytes),
            ("retransmission_ack_wire_bytes", self.retransmission_ack_wire_bytes),
            ("unknown_remote_failure_count", self.unknown_remote_failure_count),
        ):
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if not isinstance(self.accounting, str) or not self.accounting:
            raise ValueError("accounting must be a non-empty string")

    @property
    def primary_wire_bytes(self) -> int:
        return self.primary_data_wire_bytes + self.primary_ack_wire_bytes

    @property
    def retransmission_wire_bytes(self) -> int:
        return self.retransmission_data_wire_bytes + self.retransmission_ack_wire_bytes

    @property
    def accounted_wire_bytes(self) -> int:
        return self.primary_wire_bytes + self.retransmission_wire_bytes

    @property
    def accounted_bits(self) -> int:
        return self.accounted_wire_bytes * 8

    def to_dict(self) -> dict[str, int | str]:
        return {
            "primary_data_wire_bytes": self.primary_data_wire_bytes,
            "primary_ack_wire_bytes": self.primary_ack_wire_bytes,
            "retransmission_data_wire_bytes": self.retransmission_data_wire_bytes,
            "retransmission_ack_wire_bytes": self.retransmission_ack_wire_bytes,
            "primary_wire_bytes": self.primary_wire_bytes,
            "retransmission_wire_bytes": self.retransmission_wire_bytes,
            "accounted_wire_bytes": self.accounted_wire_bytes,
            "accounted_bits": self.accounted_bits,
            "unknown_remote_failure_count": self.unknown_remote_failure_count,
            "accounting": self.accounting,
        }


def classify_transfer_wire(
    data: bytes,
    *,
    transfer_id: int,
    profile: ScarceLinkProfile,
    report: Any,
) -> TransferWireBreakdown:
    """Split one transfer into primary and retransmission wire bytes.

    The deterministic PN-002 simulator exposes exact data and ACK bytes.
    ``RFReplayTransferReport`` exposes exact local data bytes but only a lower
    bound for returned ACK bytes when failed untethered attempts are
    observationally ambiguous. The returned ``accounting`` label preserves
    that distinction.
    """

    frames = fragment_payload(
        data,
        transfer_id=transfer_id,
        max_frame_bytes=profile.max_frame_bytes,
    )
    report_frame_count = getattr(report, "frame_count", len(frames))
    if int(report_frame_count) != len(frames):
        raise ValueError("transfer report frame count does not match PNF1 fragmentation")

    primary_data = sum(len(frame.encode()) for frame in frames)
    primary_ack = len(frames) * profile.ack_bytes

    if hasattr(report, "data_wire_bytes") and hasattr(report, "ack_wire_bytes"):
        data_total = int(report.data_wire_bytes)
        ack_total = int(report.ack_wire_bytes)
        if data_total < primary_data:
            raise ValueError("reported data wire bytes are below one PNF1 transmission per frame")
        if ack_total < primary_ack:
            raise ValueError("reported ACK wire bytes are below one successful ACK per frame")
        reported_total = int(getattr(report, "total_wire_bytes", data_total + ack_total))
        if reported_total != data_total + ack_total:
            raise ValueError("transfer report total wire bytes are internally inconsistent")
        return TransferWireBreakdown(
            primary_data_wire_bytes=primary_data,
            primary_ack_wire_bytes=primary_ack,
            retransmission_data_wire_bytes=data_total - primary_data,
            retransmission_ack_wire_bytes=ack_total - primary_ack,
            unknown_remote_failure_count=0,
            accounting=str(getattr(report, "wire_accounting", "deterministic_model_exact")),
        )

    if hasattr(report, "data_wire_bytes_exact") and hasattr(
        report, "confirmed_ack_wire_bytes_lower_bound"
    ):
        data_total = int(report.data_wire_bytes_exact)
        ack_lower_bound = int(report.confirmed_ack_wire_bytes_lower_bound)
        if data_total < primary_data:
            raise ValueError("replay data wire bytes are below one PNF1 transmission per frame")
        if ack_lower_bound < primary_ack:
            raise ValueError("replay confirmed ACK bytes are below one ACK per successful frame")
        reported_total = int(
            getattr(report, "total_wire_bytes_lower_bound", data_total + ack_lower_bound)
        )
        if reported_total != data_total + ack_lower_bound:
            raise ValueError("RF replay lower-bound wire total is internally inconsistent")
        return TransferWireBreakdown(
            primary_data_wire_bytes=primary_data,
            primary_ack_wire_bytes=primary_ack,
            retransmission_data_wire_bytes=data_total - primary_data,
            retransmission_ack_wire_bytes=ack_lower_bound - primary_ack,
            unknown_remote_failure_count=int(
                getattr(report, "delivery_unknown_failures", 0)
            ),
            accounting=str(
                getattr(report, "wire_accounting", "physical_replay_lower_bound")
            ),
        )

    raise TypeError("unsupported transfer report for TRC wire classification")
