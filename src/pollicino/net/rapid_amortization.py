from __future__ import annotations

from dataclasses import dataclass

from .rapid_control_wire import RapidControlWireBreakdown


def _require_non_negative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _require_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class RapidAmortizationInput:
    """Research-only decomposition for repeated similar bundle decisions.

    ``shared_control_wire_bytes`` is paid once for the modeled reuse scope.
    ``per_bundle_control_wire_bytes`` is paid once per bundle.  The caller must
    justify that decomposition from an observed/control report; this module does
    not silently decide that arbitrary RAPID state is shareable.
    """

    rapid_transfer_wire_bytes_per_bundle: int
    baseline_wire_bytes_per_bundle: int
    shared_control_wire_bytes: int
    per_bundle_control_wire_bytes: int
    evidence_class: str = "model_synthetic"

    def __post_init__(self) -> None:
        for name, value in (
            ("rapid_transfer_wire_bytes_per_bundle", self.rapid_transfer_wire_bytes_per_bundle),
            ("baseline_wire_bytes_per_bundle", self.baseline_wire_bytes_per_bundle),
            ("shared_control_wire_bytes", self.shared_control_wire_bytes),
            ("per_bundle_control_wire_bytes", self.per_bundle_control_wire_bytes),
        ):
            _require_non_negative_int(name, value)
        if not isinstance(self.evidence_class, str) or not self.evidence_class:
            raise ValueError("evidence_class must be a non-empty string")

    @classmethod
    def from_control_breakdown(
        cls,
        *,
        rapid_transfer_wire_bytes_per_bundle: int,
        baseline_wire_bytes_per_bundle: int,
        control: RapidControlWireBreakdown,
    ) -> RapidAmortizationInput:
        """Use a conservative, explicit first decomposition.

        Meeting knowledge and the optional node-index bootstrap are considered
        reusable campaign/node state. Replica, delivery and queue-quote traffic
        remains bundle-specific. This is a sensitivity model, not a production
        protocol claim; refresh/dissemination costs must be added separately in
        later experiments.
        """

        if not isinstance(control, RapidControlWireBreakdown):
            raise TypeError("control must be RapidControlWireBreakdown")
        return cls(
            rapid_transfer_wire_bytes_per_bundle=rapid_transfer_wire_bytes_per_bundle,
            baseline_wire_bytes_per_bundle=baseline_wire_bytes_per_bundle,
            shared_control_wire_bytes=(
                control.meeting_wire_bytes + control.bootstrap_wire_bytes
            ),
            per_bundle_control_wire_bytes=(
                control.replica_wire_bytes
                + control.delivery_wire_bytes
                + control.queue_quote_wire_bytes
            ),
            evidence_class=control.evidence_class,
        )


@dataclass(frozen=True, slots=True)
class RapidAmortizationPoint:
    bundle_count: int
    baseline_total_wire_bytes: int
    rapid_transfer_total_wire_bytes: int
    rapid_shared_control_wire_bytes: int
    rapid_per_bundle_control_total_wire_bytes: int
    rapid_modeled_total_wire_bytes: int

    @property
    def delta_vs_baseline_bytes(self) -> int:
        return self.rapid_modeled_total_wire_bytes - self.baseline_total_wire_bytes

    @property
    def rapid_is_cheaper(self) -> bool:
        return self.delta_vs_baseline_bytes < 0

    @property
    def shared_control_wire_bytes_per_bundle(self) -> float:
        return self.rapid_shared_control_wire_bytes / self.bundle_count


@dataclass(frozen=True, slots=True)
class RapidAmortizationSweep:
    input: RapidAmortizationInput
    points: tuple[RapidAmortizationPoint, ...]

    @property
    def first_cheaper_bundle_count(self) -> int | None:
        for point in self.points:
            if point.rapid_is_cheaper:
                return point.bundle_count
        return None


def rapid_amortization_point(
    model: RapidAmortizationInput,
    *,
    bundle_count: int,
) -> RapidAmortizationPoint:
    if not isinstance(model, RapidAmortizationInput):
        raise TypeError("model must be RapidAmortizationInput")
    _require_positive_int("bundle_count", bundle_count)

    baseline = model.baseline_wire_bytes_per_bundle * bundle_count
    rapid_transfer = model.rapid_transfer_wire_bytes_per_bundle * bundle_count
    per_bundle_control = model.per_bundle_control_wire_bytes * bundle_count
    rapid_total = rapid_transfer + model.shared_control_wire_bytes + per_bundle_control
    return RapidAmortizationPoint(
        bundle_count=bundle_count,
        baseline_total_wire_bytes=baseline,
        rapid_transfer_total_wire_bytes=rapid_transfer,
        rapid_shared_control_wire_bytes=model.shared_control_wire_bytes,
        rapid_per_bundle_control_total_wire_bytes=per_bundle_control,
        rapid_modeled_total_wire_bytes=rapid_total,
    )


def sweep_rapid_amortization(
    model: RapidAmortizationInput,
    bundle_counts: tuple[int, ...],
) -> RapidAmortizationSweep:
    if not isinstance(model, RapidAmortizationInput):
        raise TypeError("model must be RapidAmortizationInput")
    if not isinstance(bundle_counts, tuple) or not bundle_counts:
        raise ValueError("bundle_counts must be a non-empty tuple")
    if len(bundle_counts) != len(set(bundle_counts)):
        raise ValueError("bundle_counts must be unique")
    for value in bundle_counts:
        _require_positive_int("bundle_count", value)
    ordered = tuple(sorted(bundle_counts))
    return RapidAmortizationSweep(
        input=model,
        points=tuple(
            rapid_amortization_point(model, bundle_count=count)
            for count in ordered
        ),
    )
