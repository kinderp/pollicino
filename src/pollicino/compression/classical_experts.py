from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence

from .quantization import frequencies_to_cdf


class RunLengthCDFProvider:
    """Cheap causal expert for local byte runs.

    Every symbol keeps positive base mass. When a run is in progress, the last
    observed byte receives an integer boost proportional to the current run
    length. The state is reconstructed only from the decoded prefix, so encoder
    and decoder require no side information.
    """

    def __init__(
        self,
        *,
        alphabet_size: int = 256,
        base_count: int = 1,
        run_weight: int = 64,
        max_run: int = 4096,
    ) -> None:
        if alphabet_size <= 1 or alphabet_size > 256:
            raise ValueError("alphabet_size must be in [2, 256]")
        if base_count <= 0 or run_weight <= 0 or max_run <= 0:
            raise ValueError("counts and max_run must be positive")
        self.alphabet_size = int(alphabet_size)
        self.base_count = int(base_count)
        self.run_weight = int(run_weight)
        self.max_run = int(max_run)
        self._seen: list[int] = []
        self._last_symbol: int | None = None
        self._run_length = 0

    def _sync(self, prefix: Sequence[int]) -> None:
        prefix_list = [int(v) for v in prefix]
        if len(prefix_list) < len(self._seen) or prefix_list[: len(self._seen)] != self._seen:
            raise ValueError("run expert received a divergent prefix")
        for symbol in prefix_list[len(self._seen) :]:
            if not 0 <= symbol < self.alphabet_size:
                raise ValueError("symbol outside run expert alphabet")
            if symbol == self._last_symbol:
                self._run_length += 1
            else:
                self._last_symbol = symbol
                self._run_length = 1
            self._seen.append(symbol)

    def frequencies(self, index: int, prefix: Sequence[int]) -> list[int]:
        if index != len(prefix):
            raise ValueError("index must equal prefix length")
        self._sync(prefix)
        frequencies = [self.base_count] * self.alphabet_size
        if self._last_symbol is not None:
            frequencies[self._last_symbol] += self.run_weight * min(self._run_length, self.max_run)
        return frequencies

    def __call__(self, index: int, prefix: Sequence[int]) -> list[int]:
        return frequencies_to_cdf(self.frequencies(index, prefix))


def run_length_fingerprint(
    *,
    alphabet_size: int = 256,
    base_count: int = 1,
    run_weight: int = 64,
    max_run: int = 4096,
) -> bytes:
    payload = {
        "kind": "pollicino-run-length-expert-v1",
        "alphabet_size": int(alphabet_size),
        "base_count": int(base_count),
        "run_weight": int(run_weight),
        "max_run": int(max_run),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).digest()
