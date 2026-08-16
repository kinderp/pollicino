from __future__ import annotations

import hashlib
import json
from collections import deque
from collections.abc import Sequence


class RollingLikelihoodGate:
    """Select the expert with the best exact likelihood over a rolling window.

    Each observation is supplied as ``(symbol_mass, total_mass)`` for every
    expert. Products are kept as Python integers and compared by cross
    multiplication, so the choice is independent of floating-point rounding.
    Ties are resolved by expert order.
    """

    def __init__(self, expert_count: int, *, window: int = 64) -> None:
        if expert_count <= 0:
            raise ValueError("expert_count must be positive")
        if window <= 0:
            raise ValueError("window must be positive")
        self.expert_count = int(expert_count)
        self.window = int(window)
        self._history = [deque() for _ in range(expert_count)]
        self._numerators = [1] * expert_count
        self._denominators = [1] * expert_count

    def choice(self) -> int:
        best = 0
        for i in range(1, self.expert_count):
            left = self._numerators[i] * self._denominators[best]
            right = self._numerators[best] * self._denominators[i]
            if left > right:
                best = i
        return best

    def observe(self, terms: Sequence[tuple[int, int]]) -> None:
        if len(terms) != self.expert_count:
            raise ValueError("one likelihood term is required for every expert")
        for i, (numerator, denominator) in enumerate(terms):
            if not isinstance(numerator, int) or not isinstance(denominator, int):
                raise ValueError("likelihood terms must be integers")
            if numerator <= 0 or denominator <= 0 or numerator > denominator:
                raise ValueError("invalid likelihood term")
            q = self._history[i]
            q.append((numerator, denominator))
            self._numerators[i] *= numerator
            self._denominators[i] *= denominator
            if len(q) > self.window:
                old_num, old_den = q.popleft()
                self._numerators[i] //= old_num
                self._denominators[i] //= old_den


class DeterministicExpertGateCDFProvider:
    """Causal gate over deterministic CDF providers.

    The gate chooses an expert for byte *i* using only likelihood evidence from
    bytes ``< i``. Encoder and decoder therefore make the same choice without a
    selector side stream. Providers may be stateful themselves, but must be
    deterministic for the same sequential prefix.
    """

    def __init__(
        self,
        experts: Sequence,
        *,
        names: Sequence[str] | None = None,
        window: int = 64,
    ) -> None:
        if not experts:
            raise ValueError("at least one expert is required")
        if names is None:
            names = tuple(f"expert-{i}" for i in range(len(experts)))
        if len(names) != len(experts):
            raise ValueError("names must match expert count")
        self.experts = tuple(experts)
        self.names = tuple(str(v) for v in names)
        self.gate = RollingLikelihoodGate(len(experts), window=window)
        self.window = int(window)
        self.choice_counts = [0] * len(experts)
        self._seen: list[int] = []
        self._last_cdfs: list[Sequence[int]] | None = None

    @staticmethod
    def _term(cdf: Sequence[int], symbol: int) -> tuple[int, int]:
        if not 0 <= symbol < len(cdf) - 1:
            raise ValueError("symbol outside expert alphabet")
        numerator = int(cdf[symbol + 1]) - int(cdf[symbol])
        denominator = int(cdf[-1])
        if numerator <= 0 or denominator <= 0 or numerator > denominator:
            raise ValueError("expert returned an invalid CDF")
        return numerator, denominator

    def _predict_all(self) -> list[Sequence[int]]:
        index = len(self._seen)
        return [expert(index, self._seen) for expert in self.experts]

    def _sync(self, prefix: Sequence[int]) -> None:
        prefix_list = [int(v) for v in prefix]
        if len(prefix_list) < len(self._seen) or prefix_list[: len(self._seen)] != self._seen:
            raise ValueError("expert gate received a divergent prefix")
        for symbol in prefix_list[len(self._seen) :]:
            if self._last_cdfs is None:
                self._last_cdfs = self._predict_all()
            terms = [self._term(cdf, symbol) for cdf in self._last_cdfs]
            self.gate.observe(terms)
            self._seen.append(symbol)
            self._last_cdfs = None

    def __call__(self, index: int, prefix: Sequence[int]) -> Sequence[int]:
        if index != len(prefix):
            raise ValueError("index must equal prefix length")
        self._sync(prefix)
        cdfs = self._predict_all()
        choice = self.gate.choice()
        self.choice_counts[choice] += 1
        self._last_cdfs = cdfs
        return cdfs[choice]

    def choice_fractions(self) -> dict[str, float]:
        total = sum(self.choice_counts)
        if total == 0:
            return {name: 0.0 for name in self.names}
        return {name: count / total for name, count in zip(self.names, self.choice_counts)}


def expert_gate_fingerprint(
    *,
    expert_fingerprints: Sequence[bytes],
    names: Sequence[str],
    window: int,
) -> bytes:
    if not expert_fingerprints:
        raise ValueError("expert_fingerprints cannot be empty")
    if len(expert_fingerprints) != len(names):
        raise ValueError("names must match expert fingerprints")
    if any(len(fp) != 32 for fp in expert_fingerprints):
        raise ValueError("expert fingerprints must be 32 bytes")
    if window <= 0:
        raise ValueError("window must be positive")
    payload = {
        "kind": "pollicino-deterministic-expert-gate-v1",
        "window": int(window),
        "experts": [
            {"name": str(name), "fingerprint": fp.hex()}
            for name, fp in zip(names, expert_fingerprints)
        ],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).digest()
