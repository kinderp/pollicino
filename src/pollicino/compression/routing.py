from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence


class CostAwareSpecialistRouterCDFProvider:
    """Two-stage causal router between a cheap codec path and a specialist.

    The first ``probe_bytes`` symbols are always coded by ``cheap_provider``.
    When a specialist is available and the stream is large enough to satisfy the
    configured cost policy, the router evaluates both providers during the probe
    and compares their *exact quantized likelihood products*.

    After the probe it makes one deterministic decision and locks it for the rest
    of the stream. If the cheap path wins, the specialist is never evaluated
    again, so routing can reduce real compute rather than merely selecting a CDF.

    Streams that fit entirely inside the probe stay on the cheap path: there are
    no post-probe symbols on which specialist activation could recover probe cost.

    Encoder and decoder reach the same decision from the same already-known
    prefix. No selector side stream is required.
    """

    def __init__(
        self,
        cheap_provider,
        specialist_provider=None,
        *,
        stream_bytes: int,
        probe_bytes: int = 256,
        min_stream_bytes: int = 0,
        required_ratio_num: int = 1,
        required_ratio_den: int = 1,
        cheap_name: str = "cheap",
        specialist_name: str = "specialist",
    ) -> None:
        if stream_bytes < 0:
            raise ValueError("stream_bytes must be non-negative")
        if probe_bytes <= 0:
            raise ValueError("probe_bytes must be positive")
        if min_stream_bytes < 0:
            raise ValueError("min_stream_bytes must be non-negative")
        if required_ratio_num <= 0 or required_ratio_den <= 0:
            raise ValueError("required likelihood ratio must be positive")
        if not cheap_name or not specialist_name or cheap_name == specialist_name:
            raise ValueError("route names must be distinct non-empty strings")

        self.cheap_provider = cheap_provider
        self.specialist_provider = specialist_provider
        self.stream_bytes = int(stream_bytes)
        self.probe_bytes = int(probe_bytes)
        self.min_stream_bytes = int(min_stream_bytes)
        self.required_ratio_num = int(required_ratio_num)
        self.required_ratio_den = int(required_ratio_den)
        self.cheap_name = str(cheap_name)
        self.specialist_name = str(specialist_name)

        self.specialist_eligible = (
            specialist_provider is not None
            and self.stream_bytes > self.probe_bytes
            and self.stream_bytes >= self.min_stream_bytes
        )
        self.route = "probe" if self.specialist_eligible else "cheap"
        self._seen: list[int] = []
        self._last_cheap_cdf: Sequence[int] | None = None
        self._last_specialist_cdf: Sequence[int] | None = None

        # Exact cumulative likelihoods over the probe.
        self._cheap_num = 1
        self._cheap_den = 1
        self._specialist_num = 1
        self._specialist_den = 1

        self.choice_counts = {self.cheap_name: 0, self.specialist_name: 0}
        self.probe_count = 0

    @staticmethod
    def _term(cdf: Sequence[int], symbol: int) -> tuple[int, int]:
        if not 0 <= symbol < len(cdf) - 1:
            raise ValueError("symbol outside provider alphabet")
        numerator = int(cdf[symbol + 1]) - int(cdf[symbol])
        denominator = int(cdf[-1])
        if numerator <= 0 or denominator <= 0 or numerator > denominator:
            raise ValueError("provider returned an invalid CDF")
        return numerator, denominator

    def _predict_cheap(self) -> Sequence[int]:
        return self.cheap_provider(len(self._seen), self._seen)

    def _predict_specialist(self) -> Sequence[int]:
        if self.specialist_provider is None:
            raise RuntimeError("specialist provider is unavailable")
        return self.specialist_provider(len(self._seen), self._seen)

    def _decide(self) -> None:
        # specialist/cheap > required_ratio_num/required_ratio_den
        left = (
            self._specialist_num
            * self._cheap_den
            * self.required_ratio_den
        )
        right = (
            self._cheap_num
            * self._specialist_den
            * self.required_ratio_num
        )
        self.route = "specialist" if left > right else "cheap"

    def _sync(self, prefix: Sequence[int]) -> None:
        prefix_list = [int(v) for v in prefix]
        if len(prefix_list) < len(self._seen) or prefix_list[: len(self._seen)] != self._seen:
            raise ValueError("specialist router received a divergent prefix")

        for symbol in prefix_list[len(self._seen) :]:
            if self.route == "probe":
                if self._last_cheap_cdf is None:
                    self._last_cheap_cdf = self._predict_cheap()
                if self._last_specialist_cdf is None:
                    self._last_specialist_cdf = self._predict_specialist()

                cheap_num, cheap_den = self._term(self._last_cheap_cdf, symbol)
                specialist_num, specialist_den = self._term(self._last_specialist_cdf, symbol)
                self._cheap_num *= cheap_num
                self._cheap_den *= cheap_den
                self._specialist_num *= specialist_num
                self._specialist_den *= specialist_den

            self._seen.append(symbol)
            self._last_cheap_cdf = None
            self._last_specialist_cdf = None

            if self.route == "probe" and len(self._seen) >= self.probe_bytes:
                self._decide()

    def __call__(self, index: int, prefix: Sequence[int]) -> Sequence[int]:
        if index != len(prefix):
            raise ValueError("index must equal prefix length")
        self._sync(prefix)

        if self.route == "probe":
            cheap_cdf = self._predict_cheap()
            specialist_cdf = self._predict_specialist()
            self._last_cheap_cdf = cheap_cdf
            self._last_specialist_cdf = specialist_cdf
            self.probe_count += 1
            self.choice_counts[self.cheap_name] += 1
            return cheap_cdf

        if self.route == "specialist":
            cdf = self._predict_specialist()
            self._last_specialist_cdf = cdf
            self.choice_counts[self.specialist_name] += 1
            return cdf

        cdf = self._predict_cheap()
        self._last_cheap_cdf = cdf
        self.choice_counts[self.cheap_name] += 1
        return cdf

    @property
    def selected_route(self) -> str:
        if self.route == "probe":
            return "undecided"
        return self.specialist_name if self.route == "specialist" else self.cheap_name

    def choice_fractions(self) -> dict[str, float]:
        total = sum(self.choice_counts.values())
        if total == 0:
            return {name: 0.0 for name in self.choice_counts}
        return {name: count / total for name, count in self.choice_counts.items()}

    def evidence_ratio_terms(self) -> dict[str, int]:
        return {
            "cheap_num": self._cheap_num,
            "cheap_den": self._cheap_den,
            "specialist_num": self._specialist_num,
            "specialist_den": self._specialist_den,
        }


def cost_aware_router_fingerprint(
    *,
    cheap_fingerprint: bytes,
    specialist_fingerprint: bytes | None,
    stream_bytes: int,
    probe_bytes: int,
    min_stream_bytes: int,
    required_ratio_num: int = 1,
    required_ratio_den: int = 1,
) -> bytes:
    if len(cheap_fingerprint) != 32:
        raise ValueError("cheap fingerprint must be 32 bytes")
    if specialist_fingerprint is not None and len(specialist_fingerprint) != 32:
        raise ValueError("specialist fingerprint must be 32 bytes")
    if stream_bytes < 0 or probe_bytes <= 0 or min_stream_bytes < 0:
        raise ValueError("invalid routing size parameter")
    if required_ratio_num <= 0 or required_ratio_den <= 0:
        raise ValueError("required likelihood ratio must be positive")

    payload = {
        "kind": "pollicino-cost-aware-specialist-router-v1",
        "cheap_fingerprint": cheap_fingerprint.hex(),
        "specialist_fingerprint": specialist_fingerprint.hex() if specialist_fingerprint else None,
        "stream_bytes": int(stream_bytes),
        "probe_bytes": int(probe_bytes),
        "min_stream_bytes": int(min_stream_bytes),
        "required_ratio": [int(required_ratio_num), int(required_ratio_den)],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).digest()
