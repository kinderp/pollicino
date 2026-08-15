from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Sequence

from .quantization import frequencies_to_cdf


@dataclass
class _ContextCounts:
    counts: dict[int, int]
    total: int = 0


class AdaptiveNGramCDFProvider:
    """Causal integer n-gram model reconstructed from the decoded prefix only.

    The distribution is a deterministic weighted backoff over order 0..N counts.
    Every symbol keeps a positive base mass, so unseen bytes are always encodable.
    No learned or mutable state needs to be transmitted: a fresh decoder reaches the
    same state by replaying the bytes it has already decoded.
    """

    def __init__(
        self,
        *,
        max_order: int = 3,
        order_weights: Sequence[int] = (1, 4, 16, 64),
        alphabet_size: int = 256,
        base_count: int = 1,
    ) -> None:
        if max_order < 0:
            raise ValueError("max_order must be non-negative")
        if len(order_weights) != max_order + 1:
            raise ValueError("order_weights must contain one weight for every order")
        if alphabet_size <= 1 or alphabet_size > 256:
            raise ValueError("alphabet_size must be in [2, 256]")
        if base_count <= 0 or any((not isinstance(w, int)) or w <= 0 for w in order_weights):
            raise ValueError("base_count and order weights must be positive integers")
        self.max_order = max_order
        self.order_weights = tuple(int(w) for w in order_weights)
        self.alphabet_size = alphabet_size
        self.base_count = base_count
        self._tables: list[dict[bytes, _ContextCounts]] = [dict() for _ in range(max_order + 1)]
        self._seen: list[int] = []

    def _context(self, order: int) -> bytes:
        if order == 0:
            return b""
        return bytes(self._seen[max(0, len(self._seen) - order):])

    def _sync(self, prefix: Sequence[int]) -> None:
        if len(prefix) < len(self._seen) or list(prefix[:len(self._seen)]) != self._seen:
            raise ValueError("adaptive provider received a divergent prefix")
        for raw_symbol in prefix[len(self._seen):]:
            symbol = int(raw_symbol)
            if not 0 <= symbol < self.alphabet_size:
                raise ValueError("symbol outside adaptive alphabet")
            position = len(self._seen)
            for order in range(self.max_order + 1):
                context = b"" if order == 0 else bytes(self._seen[max(0, position - order):position])
                state = self._tables[order].get(context)
                if state is None:
                    state = _ContextCounts({})
                    self._tables[order][context] = state
                state.counts[symbol] = state.counts.get(symbol, 0) + 1
                state.total += 1
            self._seen.append(symbol)

    def symbol_mass(self, index: int, prefix: Sequence[int], symbol: int) -> tuple[int, int]:
        if index != len(prefix):
            raise ValueError("index must equal prefix length")
        if not 0 <= symbol < self.alphabet_size:
            raise ValueError("symbol outside adaptive alphabet")
        self._sync(prefix)
        numerator = self.base_count
        denominator = self.base_count * self.alphabet_size
        for order, weight in enumerate(self.order_weights):
            state = self._tables[order].get(self._context(order))
            if state is None:
                continue
            numerator += weight * state.counts.get(symbol, 0)
            denominator += weight * state.total
        return numerator, denominator

    def frequencies(self, index: int, prefix: Sequence[int]) -> list[int]:
        if index != len(prefix):
            raise ValueError("index must equal prefix length")
        self._sync(prefix)
        frequencies = [self.base_count] * self.alphabet_size
        for order, weight in enumerate(self.order_weights):
            state = self._tables[order].get(self._context(order))
            if state is None:
                continue
            for symbol, count in state.counts.items():
                frequencies[symbol] += weight * count
        return frequencies

    def __call__(self, index: int, prefix: Sequence[int]) -> list[int]:
        return frequencies_to_cdf(self.frequencies(index, prefix))


def _rescale_nonnegative(values: Sequence[int], target_total: int) -> list[int]:
    if target_total < 0:
        raise ValueError("target_total must be non-negative")
    if any((not isinstance(v, int)) or v < 0 for v in values):
        raise ValueError("values must be non-negative integers")
    if target_total == 0:
        return [0] * len(values)
    source_total = sum(values)
    if source_total <= 0:
        raise ValueError("values must have positive total mass")
    products = [v * target_total for v in values]
    scaled = [p // source_total for p in products]
    remainders = [p % source_total for p in products]
    leftover = target_total - sum(scaled)
    ranking = sorted(range(len(values)), key=lambda i: (-remainders[i], i))
    for i in ranking[:leftover]:
        scaled[i] += 1
    assert sum(scaled) == target_total
    return scaled


class NeuralPriorAdaptiveCDFProvider:
    """Adaptive n-gram model with a fixed integer neural pseudo-count prior.

    `prior_provider` must itself be deterministic for the same prefix. Its CDF is
    converted to `prior_strength` pseudo-counts and added to the adaptive counts.
    As file-local evidence accumulates, the adaptive counts naturally dominate the
    fixed prior without any gradient update or transmitted delta.
    """

    def __init__(
        self,
        prior_provider,
        *,
        prior_strength: int = 256,
        max_order: int = 3,
        order_weights: Sequence[int] = (1, 4, 16, 64),
        alphabet_size: int = 256,
        base_count: int = 1,
    ) -> None:
        if prior_strength < 0:
            raise ValueError("prior_strength must be non-negative")
        self.prior_provider = prior_provider
        self.prior_strength = int(prior_strength)
        self.adaptive = AdaptiveNGramCDFProvider(
            max_order=max_order,
            order_weights=order_weights,
            alphabet_size=alphabet_size,
            base_count=base_count,
        )

    def __call__(self, index: int, prefix: Sequence[int]) -> list[int]:
        adaptive = self.adaptive.frequencies(index, prefix)
        if self.prior_strength == 0:
            return frequencies_to_cdf(adaptive)
        prior_cdf = self.prior_provider(index, prefix)
        prior_freq = [b - a for a, b in zip(prior_cdf, prior_cdf[1:])]
        if len(prior_freq) != len(adaptive) or any(v <= 0 for v in prior_freq):
            raise ValueError("prior provider returned an incompatible CDF")
        pseudo = _rescale_nonnegative(prior_freq, self.prior_strength)
        return frequencies_to_cdf([a + p for a, p in zip(adaptive, pseudo)])


def adaptive_fingerprint(
    *,
    max_order: int,
    order_weights: Sequence[int],
    base_count: int = 1,
    prior_strength: int = 0,
    neural_fingerprint: bytes | None = None,
) -> bytes:
    payload = {
        "kind": "pollicino-adaptive-ngram-v1",
        "max_order": int(max_order),
        "order_weights": [int(v) for v in order_weights],
        "base_count": int(base_count),
        "prior_strength": int(prior_strength),
        "neural_fingerprint": neural_fingerprint.hex() if neural_fingerprint else None,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).digest()
