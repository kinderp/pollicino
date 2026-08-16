from __future__ import annotations

import hashlib
import json
from collections import deque
from collections.abc import Sequence


class StabilityValueSpecialistRouterCDFProvider:
    """Causal specialist router requiring stable evidence and future value.

    While undecided, symbols are encoded with the cheap provider and both paths
    are scored using their exact integer CDF masses. Neural activation requires:

    * strong cumulative evidence;
    * a recent-window likelihood advantage of at least ``2**recent_gain_bits``;
    * that condition to persist for ``persistence_observations`` consecutive
      decoded symbols;
    * a conservative lower bound on future recoverable bits to exceed
      ``min_projected_gain_bits``.

    The future-value bound uses only integers::

        floor(remaining_bytes / recent_window) * recent_gain_bits

    so the decision is independent of CPU, wall-clock timing, floating-point
    logarithms, or hardware. Encoder and decoder see the same prefix and make the
    same decision without selector side bits.
    """

    def __init__(
        self,
        cheap_provider,
        specialist_provider=None,
        *,
        stream_bytes: int,
        min_stream_bytes: int = 0,
        min_observations: int = 8,
        max_probe_bytes: int = 96,
        activate_ratio_num: int = 256,
        activate_ratio_den: int = 1,
        reject_ratio_num: int = 1,
        reject_ratio_den: int = 256,
        recent_window: int = 8,
        recent_gain_bits: int = 2,
        persistence_observations: int = 4,
        min_projected_gain_bits: int = 64,
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
        if recent_window <= 0:
            raise ValueError("recent_window must be positive")
        if recent_gain_bits <= 0:
            raise ValueError("recent_gain_bits must be positive")
        if persistence_observations <= 0:
            raise ValueError("persistence_observations must be positive")
        if min_projected_gain_bits < 0:
            raise ValueError("min_projected_gain_bits must be non-negative")
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
        self.recent_window = int(recent_window)
        self.recent_gain_bits = int(recent_gain_bits)
        self.persistence_observations = int(persistence_observations)
        self.min_projected_gain_bits = int(min_projected_gain_bits)
        self.cheap_name = str(cheap_name)
        self.specialist_name = str(specialist_name)

        potential_after_min = self._projected_gain_bits(self.min_observations)
        self.specialist_eligible = (
            specialist_provider is not None
            and self.stream_bytes >= self.min_stream_bytes
            and self.stream_bytes > self.min_observations
            and potential_after_min >= self.min_projected_gain_bits
        )
        self.route = "undecided" if self.specialist_eligible else "cheap"
        self.decision_byte: int | None = 0 if self.route == "cheap" else None
        self.decision_reason: str | None = "ineligible" if self.route == "cheap" else None

        self._seen: list[int] = []
        self._last_cheap_cdf: Sequence[int] | None = None
        self._last_specialist_cdf: Sequence[int] | None = None
        self._cheap_num = 1
        self._cheap_den = 1
        self._specialist_num = 1
        self._specialist_den = 1
        self._recent_terms: deque[tuple[int, int, int, int]] = deque(maxlen=self.recent_window)
        self._candidate_streak = 0

        self.choice_counts = {self.cheap_name: 0, self.specialist_name: 0}
        self.probe_count = 0
        self.specialist_calls = 0
        self.activation_candidate_count = 0
        self.max_candidate_streak = 0

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
        left = self._specialist_num * self._cheap_den * denominator
        right = self._cheap_num * self._specialist_den * numerator
        return left > right

    def _ratio_lt(self, numerator: int, denominator: int) -> bool:
        left = self._specialist_num * self._cheap_den * denominator
        right = self._cheap_num * self._specialist_den * numerator
        return left < right

    def _recent_ratio_gt_power2(self) -> bool:
        if len(self._recent_terms) < self.recent_window:
            return False
        cheap_num = cheap_den = specialist_num = specialist_den = 1
        for cn, cd, sn, sd in self._recent_terms:
            cheap_num *= cn
            cheap_den *= cd
            specialist_num *= sn
            specialist_den *= sd
        left = specialist_num * cheap_den
        right = cheap_num * specialist_den * (1 << self.recent_gain_bits)
        return left > right

    def _projected_gain_bits(self, seen: int) -> int:
        remaining = max(0, self.stream_bytes - int(seen))
        return (remaining // self.recent_window) * self.recent_gain_bits

    def _activation_candidate(self) -> bool:
        seen = len(self._seen)
        if seen < self.min_observations:
            return False
        if not self._ratio_gt(self.activate_ratio_num, self.activate_ratio_den):
            return False
        if not self._recent_ratio_gt_power2():
            return False
        if self._projected_gain_bits(seen) < self.min_projected_gain_bits:
            return False
        return True

    def _lock(self, route: str, reason: str) -> None:
        self.route = route
        self.decision_byte = len(self._seen)
        self.decision_reason = reason

    def _maybe_decide(self) -> None:
        if self.route != "undecided":
            return
        seen = len(self._seen)
        if seen < self.min_observations:
            return

        if self._ratio_lt(self.reject_ratio_num, self.reject_ratio_den):
            self._lock("cheap", "cumulative-reject")
            return

        candidate = self._activation_candidate()
        if candidate:
            self.activation_candidate_count += 1
            self._candidate_streak += 1
            self.max_candidate_streak = max(self.max_candidate_streak, self._candidate_streak)
            if self._candidate_streak >= self.persistence_observations:
                self._lock("specialist", "stable-value-activate")
                return
        else:
            self._candidate_streak = 0

        # Once even the policy's conservative gain floor cannot repay the required
        # value margin, future bytes cannot restore eligibility because remaining
        # bytes only decrease.
        if self._projected_gain_bits(seen) < self.min_projected_gain_bits:
            self._lock("cheap", "value-exhausted")
            return

        if seen >= min(self.max_probe_bytes, self.stream_bytes):
            self._lock("cheap", "probe-cap")

    def _sync(self, prefix: Sequence[int]) -> None:
        prefix_list = [int(v) for v in prefix]
        if len(prefix_list) < len(self._seen) or prefix_list[: len(self._seen)] != self._seen:
            raise ValueError("stability router received a divergent prefix")

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
                self._recent_terms.append((cheap_num, cheap_den, specialist_num, specialist_den))

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


def stability_value_router_fingerprint(
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
    recent_window: int,
    recent_gain_bits: int,
    persistence_observations: int,
    min_projected_gain_bits: int,
) -> bytes:
    if len(cheap_fingerprint) != 32:
        raise ValueError("cheap fingerprint must be 32 bytes")
    if specialist_fingerprint is not None and len(specialist_fingerprint) != 32:
        raise ValueError("specialist fingerprint must be 32 bytes")
    if stream_bytes < 0 or min_stream_bytes < 0:
        raise ValueError("invalid stream size")
    if min_observations <= 0 or max_probe_bytes < min_observations:
        raise ValueError("invalid probe bounds")
    if recent_window <= 0 or recent_gain_bits <= 0 or persistence_observations <= 0:
        raise ValueError("invalid stability parameter")
    if min_projected_gain_bits < 0:
        raise ValueError("invalid projected gain threshold")

    payload = {
        "kind": "pollicino-stability-value-specialist-router-v1",
        "cheap_fingerprint": cheap_fingerprint.hex(),
        "specialist_fingerprint": specialist_fingerprint.hex() if specialist_fingerprint else None,
        "stream_bytes": int(stream_bytes),
        "min_stream_bytes": int(min_stream_bytes),
        "min_observations": int(min_observations),
        "max_probe_bytes": int(max_probe_bytes),
        "activate_ratio": [int(activate_ratio_num), int(activate_ratio_den)],
        "reject_ratio": [int(reject_ratio_num), int(reject_ratio_den)],
        "recent_window": int(recent_window),
        "recent_gain_bits": int(recent_gain_bits),
        "persistence_observations": int(persistence_observations),
        "min_projected_gain_bits": int(min_projected_gain_bits),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).digest()
