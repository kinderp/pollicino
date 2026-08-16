from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence


class SequentialSpecialistRouterCDFProvider:
    """Causal sequential router between a cheap path and a specialist.

    Symbols are coded by the cheap provider while the route is undecided. During
    that phase both providers are evaluated and their exact quantized likelihood
    ratio is accumulated. After ``min_observations`` bytes, the router can:

    * activate the specialist as soon as specialist/cheap exceeds the activation
      ratio;
    * reject the specialist as soon as specialist/cheap falls below the rejection
      ratio;
    * default to cheap when ``max_probe_bytes`` is reached without enough evidence.

    Once cheap is selected, the specialist is never evaluated again. Encoder and
    decoder observe the same decoded prefix and therefore reconstruct the same
    route without a selector side stream.
    """

    def __init__(
        self,
        cheap_provider,
        specialist_provider=None,
        *,
        stream_bytes: int,
        min_stream_bytes: int = 0,
        min_observations: int = 16,
        max_probe_bytes: int = 128,
        activate_ratio_num: int = 16,
        activate_ratio_den: int = 1,
        reject_ratio_num: int = 1,
        reject_ratio_den: int = 16,
        cheap_name: str = "cheap",
        specialist_name: str = "specialist",
    ) -> None:
        if stream_bytes < 0:
            raise ValueError("stream_bytes must be non-negative")
        if min_stream_bytes < 0:
            raise ValueError("min_stream_bytes must be non-negative")
        if min_observations <= 0:
            raise ValueError("min_observations must be positive")
        if max_probe_bytes < min_observations:
            raise ValueError("max_probe_bytes must be >= min_observations")
        if min(
            activate_ratio_num,
            activate_ratio_den,
            reject_ratio_num,
            reject_ratio_den,
        ) <= 0:
            raise ValueError("likelihood ratios must be positive")
        if activate_ratio_num * reject_ratio_den <= reject_ratio_num * activate_ratio_den:
            raise ValueError("activation ratio must exceed rejection ratio")
        if not cheap_name or not specialist_name or cheap_name == specialist_name:
            raise ValueError("route names must be distinct non-empty strings")

        self.cheap_provider = cheap_provider
        self.specialist_provider = specialist_provider
        self.stream_bytes = int(stream_bytes)
        self.min_stream_bytes = int(min_stream_bytes)
        self.min_observations = int(min_observations)
        self.max_probe_bytes = int(max_probe_bytes)
        self.activate_ratio_num = int(activate_ratio_num)
        self.activate_ratio_den = int(activate_ratio_den)
        self.reject_ratio_num = int(reject_ratio_num)
        self.reject_ratio_den = int(reject_ratio_den)
        self.cheap_name = str(cheap_name)
        self.specialist_name = str(specialist_name)

        # If there can be no post-probe payload, probing cannot repay its cost.
        self.specialist_eligible = (
            specialist_provider is not None
            and self.stream_bytes >= self.min_stream_bytes
            and self.stream_bytes > self.min_observations
        )
        self.route = "undecided" if self.specialist_eligible else "cheap"
        self.decision_byte: int | None = 0 if self.route == "cheap" else None

        self._seen: list[int] = []
        self._last_cheap_cdf: Sequence[int] | None = None
        self._last_specialist_cdf: Sequence[int] | None = None
        self._cheap_num = 1
        self._cheap_den = 1
        self._specialist_num = 1
        self._specialist_den = 1

        self.choice_counts = {self.cheap_name: 0, self.specialist_name: 0}
        self.probe_count = 0
        self.specialist_calls = 0

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
        self.specialist_calls += 1
        return self.specialist_provider(len(self._seen), self._seen)

    def _ratio_gt(self, numerator: int, denominator: int) -> bool:
        # specialist / cheap > numerator / denominator
        left = self._specialist_num * self._cheap_den * denominator
        right = self._cheap_num * self._specialist_den * numerator
        return left > right

    def _ratio_lt(self, numerator: int, denominator: int) -> bool:
        left = self._specialist_num * self._cheap_den * denominator
        right = self._cheap_num * self._specialist_den * numerator
        return left < right

    def _maybe_decide(self) -> None:
        if self.route != "undecided":
            return
        seen = len(self._seen)
        if seen < self.min_observations:
            return
        if self._ratio_gt(self.activate_ratio_num, self.activate_ratio_den):
            self.route = "specialist"
            self.decision_byte = seen
            return
        if self._ratio_lt(self.reject_ratio_num, self.reject_ratio_den):
            self.route = "cheap"
            self.decision_byte = seen
            return
        if seen >= min(self.max_probe_bytes, self.stream_bytes):
            self.route = "cheap"
            self.decision_byte = seen

    def _sync(self, prefix: Sequence[int]) -> None:
        prefix_list = [int(v) for v in prefix]
        if len(prefix_list) < len(self._seen) or prefix_list[: len(self._seen)] != self._seen:
            raise ValueError("sequential router received a divergent prefix")

        for symbol in prefix_list[len(self._seen) :]:
            if self.route == "undecided":
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
            self._maybe_decide()

    def __call__(self, index: int, prefix: Sequence[int]) -> Sequence[int]:
        if index != len(prefix):
            raise ValueError("index must equal prefix length")
        self._sync(prefix)

        if self.route == "specialist":
            cdf = self._predict_specialist()
            self._last_specialist_cdf = cdf
            self.choice_counts[self.specialist_name] += 1
            return cdf

        cheap_cdf = self._predict_cheap()
        self._last_cheap_cdf = cheap_cdf
        self.choice_counts[self.cheap_name] += 1
        if self.route == "undecided":
            specialist_cdf = self._predict_specialist()
            self._last_specialist_cdf = specialist_cdf
            self.probe_count += 1
        return cheap_cdf

    @property
    def selected_route(self) -> str:
        if self.route == "specialist":
            return self.specialist_name
        return self.cheap_name

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


def sequential_router_fingerprint(
    *,
    cheap_fingerprint: bytes,
    specialist_fingerprint: bytes | None,
    stream_bytes: int,
    min_stream_bytes: int,
    min_observations: int,
    max_probe_bytes: int,
    activate_ratio_num: int,
    activate_ratio_den: int,
    reject_ratio_num: int,
    reject_ratio_den: int,
) -> bytes:
    if len(cheap_fingerprint) != 32:
        raise ValueError("cheap fingerprint must be 32 bytes")
    if specialist_fingerprint is not None and len(specialist_fingerprint) != 32:
        raise ValueError("specialist fingerprint must be 32 bytes")
    if stream_bytes < 0 or min_stream_bytes < 0:
        raise ValueError("invalid stream size")
    if min_observations <= 0 or max_probe_bytes < min_observations:
        raise ValueError("invalid sequential probe bounds")

    payload = {
        "kind": "pollicino-sequential-specialist-router-v1",
        "cheap_fingerprint": cheap_fingerprint.hex(),
        "specialist_fingerprint": specialist_fingerprint.hex() if specialist_fingerprint else None,
        "stream_bytes": int(stream_bytes),
        "min_stream_bytes": int(min_stream_bytes),
        "min_observations": int(min_observations),
        "max_probe_bytes": int(max_probe_bytes),
        "activate_ratio": [int(activate_ratio_num), int(activate_ratio_den)],
        "reject_ratio": [int(reject_ratio_num), int(reject_ratio_den)],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).digest()
