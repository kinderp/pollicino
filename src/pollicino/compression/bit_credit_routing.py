from __future__ import annotations

import hashlib
import json

from .sequential_routing import SequentialSpecialistRouterCDFProvider


class BitCreditSpecialistRouterCDFProvider(SequentialSpecialistRouterCDFProvider):
    """Deterministic cheap/specialist router parameterized directly in bit credit.

    Let ``R = P_specialist(prefix) / P_cheap(prefix)`` over observed probe bytes.
    The cumulative specialist credit is ``log2(R)`` bits. The implementation never
    computes that logarithm: integer likelihood products are compared directly to
    powers of two, so encoder and decoder make the same decision without floating
    point or a selector side stream.

    Activation and rejection credits are intentionally asymmetric. A false negative
    can cost far more compression bits than a false positive, so the policy is tuned
    on regret rather than route-classification accuracy.
    """

    def __init__(
        self,
        cheap_provider,
        specialist_provider=None,
        *,
        stream_bytes: int,
        min_stream_bytes: int = 0,
        min_observations: int = 8,
        max_probe_bytes: int = 64,
        activation_credit_bits: int = 8,
        rejection_credit_bits: int = 8,
        cheap_name: str = "cheap",
        specialist_name: str = "specialist",
    ) -> None:
        if activation_credit_bits < 0 or rejection_credit_bits < 0:
            raise ValueError("bit-credit thresholds must be non-negative")
        self.activation_credit_bits = int(activation_credit_bits)
        self.rejection_credit_bits = int(rejection_credit_bits)
        super().__init__(
            cheap_provider,
            specialist_provider,
            stream_bytes=stream_bytes,
            min_stream_bytes=min_stream_bytes,
            min_observations=min_observations,
            max_probe_bytes=max_probe_bytes,
            activate_ratio_num=1 << self.activation_credit_bits,
            activate_ratio_den=1,
            reject_ratio_num=1,
            reject_ratio_den=1 << self.rejection_credit_bits,
            cheap_name=cheap_name,
            specialist_name=specialist_name,
        )

    @property
    def compute_fraction(self) -> float:
        if self.stream_bytes <= 0:
            return 0.0
        return min(1.0, self.specialist_calls / self.stream_bytes)


def bit_credit_router_fingerprint(
    *,
    cheap_fingerprint: bytes,
    specialist_fingerprint: bytes | None,
    stream_bytes: int,
    min_stream_bytes: int,
    min_observations: int,
    max_probe_bytes: int,
    activation_credit_bits: int,
    rejection_credit_bits: int,
) -> bytes:
    if len(cheap_fingerprint) != 32:
        raise ValueError("cheap fingerprint must be 32 bytes")
    if specialist_fingerprint is not None and len(specialist_fingerprint) != 32:
        raise ValueError("specialist fingerprint must be 32 bytes")
    if stream_bytes < 0 or min_stream_bytes < 0:
        raise ValueError("invalid stream size")
    if min_observations <= 0 or max_probe_bytes < min_observations:
        raise ValueError("invalid probe bounds")
    if activation_credit_bits < 0 or rejection_credit_bits < 0:
        raise ValueError("bit-credit thresholds must be non-negative")
    payload = {
        "kind": "pollicino-bit-credit-specialist-router-v1",
        "cheap_fingerprint": cheap_fingerprint.hex(),
        "specialist_fingerprint": specialist_fingerprint.hex() if specialist_fingerprint else None,
        "stream_bytes": int(stream_bytes),
        "min_stream_bytes": int(min_stream_bytes),
        "min_observations": int(min_observations),
        "max_probe_bytes": int(max_probe_bytes),
        "activation_credit_bits": int(activation_credit_bits),
        "rejection_credit_bits": int(rejection_credit_bits),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).digest()
