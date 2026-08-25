from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .link import DeliveryError, ScarceLinkProfile, fragment_payload, reassemble_frames
from .rf import RFReplayTrace, RFTraceSample


class RFReplayExhausted(RuntimeError):
    """Raised when a physical trace is exhausted without explicit repetition."""


@dataclass(frozen=True, slots=True)
class RFReplayTransferReport:
    """Accounting for one PNF1 transfer driven by physical transaction outcomes.

    Local data-transmission bytes are exact because every replay attempt means
    the local transmitter emitted that frame. Return/ACK bytes are a lower
    bound: for a failed untethered transaction the remote node may have sent a
    response that never returned, and the physical trace cannot distinguish
    that case from a failure before remote transmission.
    """

    source_bytes: int
    reconstructed_bytes: int
    frame_count: int
    payload_capacity_bytes: int
    data_transmissions: int
    retransmissions: int
    data_wire_bytes_exact: int
    confirmed_ack_transmissions: int
    confirmed_ack_wire_bytes_lower_bound: int
    total_wire_bytes_lower_bound: int
    nominal_serialization_seconds_lower_bound: float
    trace_samples_consumed: int
    trace_start_position: int
    trace_end_position: int
    failure_classes: tuple[tuple[str, int], ...]
    delivery_unknown_failures: int
    success: bool

    @property
    def failure_class_counts(self) -> dict[str, int]:
        return dict(self.failure_classes)

    @property
    def wire_accounting(self) -> str:
        return "local_data_exact_remote_ack_lower_bound"


class RFReplayTransmitter:
    """Consume an observed RF trace as a deterministic transaction oracle.

    One physical sample represents one round-trip transaction attempt. A
    successful sample confirms both outward data delivery and the returning
    acknowledgement at the abstraction used by this replay adapter. A failed
    sample remains observationally unresolved and is conservatively *not*
    treated as receiver delivery.

    By default a recorded frame-size value must match the encoded PNF1 frame.
    Disabling that check is an explicit extrapolation and is not physical
    evidence for the new frame size.
    """

    def __init__(
        self,
        trace: RFReplayTrace,
        *,
        repeat: bool = False,
        strict_frame_bytes: bool = True,
    ) -> None:
        if not isinstance(trace, RFReplayTrace):
            raise TypeError("trace must be an RFReplayTrace")
        if not trace.samples:
            raise ValueError("trace must contain at least one physical sample")
        self.trace = trace
        self.repeat = bool(repeat)
        self.strict_frame_bytes = bool(strict_frame_bytes)
        self.position = 0

    @property
    def remaining(self) -> int | None:
        if self.repeat:
            return None
        return max(len(self.trace.samples) - self.position, 0)

    def _take(self, expected_frame_bytes: int) -> RFTraceSample:
        if not self.repeat and self.position >= len(self.trace.samples):
            raise RFReplayExhausted(
                f"physical trace exhausted at position {self.position}; "
                "explicit repeat=True is required for synthetic reuse"
            )
        sample = self.trace.samples[self.position % len(self.trace.samples)]
        self.position += 1
        if (
            self.strict_frame_bytes
            and sample.frame_bytes is not None
            and sample.frame_bytes != expected_frame_bytes
        ):
            raise ValueError(
                "physical trace frame-size mismatch: "
                f"sample={sample.frame_bytes} encoded_pnf1={expected_frame_bytes}; "
                "set strict_frame_bytes=False only for explicit extrapolation"
            )
        return sample

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": "pollicino-rf-replay-cursor-v1",
            "trace_source": self.trace.source,
            "trace_schema": self.trace.schema,
            "trace_lab": self.trace.lab,
            "position": self.position,
            "repeat": self.repeat,
            "strict_frame_bytes": self.strict_frame_bytes,
            "remaining": self.remaining,
        }

    def transmit_exact(
        self,
        data: bytes,
        *,
        transfer_id: int,
        profile: ScarceLinkProfile,
    ) -> tuple[bytes, RFReplayTransferReport]:
        """Run PNF1 stop-and-wait using physical success/failure observations."""

        frames = fragment_payload(
            data,
            transfer_id=transfer_id,
            max_frame_bytes=profile.max_frame_bytes,
        )
        received = {}
        start_position = self.position
        data_transmissions = 0
        data_wire_bytes_exact = 0
        confirmed_ack_transmissions = 0
        confirmed_ack_wire_bytes = 0
        failure_counts: dict[str, int] = {}
        delivery_unknown_failures = 0

        for frame in frames:
            encoded = frame.encode()
            acknowledged = False
            for attempt in range(profile.max_retries + 1):
                data_transmissions += 1
                data_wire_bytes_exact += len(encoded)
                sample = self._take(len(encoded))

                if not sample.success:
                    failure_class = sample.failure_class or "other_failure"
                    failure_counts[failure_class] = failure_counts.get(failure_class, 0) + 1
                    delivery_unknown_failures += 1
                    continue

                received[frame.sequence] = frame
                if profile.ack_bytes:
                    confirmed_ack_transmissions += 1
                    confirmed_ack_wire_bytes += profile.ack_bytes
                acknowledged = True
                break

            if not acknowledged:
                raise DeliveryError(
                    f"frame {frame.sequence}/{frame.total} exceeded retry budget under "
                    f"physical replay after {profile.max_retries + 1} attempts"
                )

        reconstructed = reassemble_frames(list(received.values()))
        if reconstructed != data:
            raise AssertionError("physical-replay exact reconstruction mismatch")

        total_lower_bound = data_wire_bytes_exact + confirmed_ack_wire_bytes
        report = RFReplayTransferReport(
            source_bytes=len(data),
            reconstructed_bytes=len(reconstructed),
            frame_count=len(frames),
            payload_capacity_bytes=profile.payload_capacity_bytes,
            data_transmissions=data_transmissions,
            retransmissions=data_transmissions - len(frames),
            data_wire_bytes_exact=data_wire_bytes_exact,
            confirmed_ack_transmissions=confirmed_ack_transmissions,
            confirmed_ack_wire_bytes_lower_bound=confirmed_ack_wire_bytes,
            total_wire_bytes_lower_bound=total_lower_bound,
            nominal_serialization_seconds_lower_bound=(
                total_lower_bound * 8 / profile.bitrate_bps
            ),
            trace_samples_consumed=self.position - start_position,
            trace_start_position=start_position,
            trace_end_position=self.position,
            failure_classes=tuple(sorted(failure_counts.items())),
            delivery_unknown_failures=delivery_unknown_failures,
            success=True,
        )
        return reconstructed, report
