from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence


class CheapCodelengthAdmissionBlockCDFProvider:
    """Gate expensive block-local specialization using cheap-only evidence.

    Every block starts with a fresh cheap provider.  The first ``probe_bytes`` are
    coded by that provider while their exact quantized likelihood is accumulated.
    Once the probe is complete, the block is admitted to the specialist only when
    the cheap codelength lies inside the configured integer-bit band.

    If a block is rejected, ``specialist_factory`` is never called for that block.
    If it is admitted, the specialist is created lazily and receives the complete
    local prefix.  Stateful specialists may therefore replay/catch up the probe;
    experiments must count that work explicitly.  This class intentionally does
    not expose a misleading generic ``compute_fraction`` property.

    The codelength comparisons are exact.  For likelihood P = num / den,
    ``-log2(P) >= L`` iff ``num * 2**L <= den`` and
    ``-log2(P) <= U`` iff ``num * 2**U >= den``.
    """

    def __init__(
        self,
        cheap_factory: Callable[[], object],
        specialist_factory: Callable[[], object] | None,
        *,
        stream_bytes: int,
        block_bytes: int,
        probe_bytes: int,
        min_probe_code_bits: int,
        max_probe_code_bits: int,
        cheap_name: str = "cheap",
        specialist_name: str = "specialist",
    ) -> None:
        if stream_bytes < 0:
            raise ValueError("stream_bytes must be non-negative")
        if block_bytes <= 0:
            raise ValueError("block_bytes must be positive")
        if probe_bytes <= 0 or probe_bytes >= block_bytes:
            raise ValueError("probe_bytes must be in [1, block_bytes)")
        if min_probe_code_bits < 0 or max_probe_code_bits < min_probe_code_bits:
            raise ValueError("invalid probe codelength band")
        if not cheap_name or not specialist_name or cheap_name == specialist_name:
            raise ValueError("route names must be distinct non-empty strings")

        self.cheap_factory = cheap_factory
        self.specialist_factory = specialist_factory
        self.stream_bytes = int(stream_bytes)
        self.block_bytes = int(block_bytes)
        self.probe_bytes = int(probe_bytes)
        self.min_probe_code_bits = int(min_probe_code_bits)
        self.max_probe_code_bits = int(max_probe_code_bits)
        self.cheap_name = str(cheap_name)
        self.specialist_name = str(specialist_name)

        self._block_index: int | None = None
        self._block_start = 0
        self._cheap = None
        self._specialist = None
        self._probe_seen: list[int] = []
        self._last_probe_cdf: Sequence[int] | None = None
        self._probe_num = 1
        self._probe_den = 1
        self._admitted: bool | None = None
        self._completed: list[dict[str, int | str | bool]] = []
        self._last_prefix: list[int] = []
        self.specialist_output_calls = 0

    @staticmethod
    def _term(cdf: Sequence[int], symbol: int) -> tuple[int, int]:
        if not 0 <= symbol < len(cdf) - 1:
            raise ValueError("symbol outside provider alphabet")
        numerator = int(cdf[symbol + 1]) - int(cdf[symbol])
        denominator = int(cdf[-1])
        if numerator <= 0 or denominator <= 0 or numerator > denominator:
            raise ValueError("provider returned an invalid CDF")
        return numerator, denominator

    def _block_length(self, block_index: int) -> int:
        start = block_index * self.block_bytes
        return max(0, min(self.block_bytes, self.stream_bytes - start))

    def _snapshot(self) -> dict[str, int | str | bool]:
        assert self._block_index is not None
        length = self._block_length(self._block_index)
        admitted = bool(self._admitted)
        decision = min(self.probe_bytes, length)
        return {
            "block_index": self._block_index,
            "block_start": self._block_start,
            "block_bytes": length,
            "probe_bytes_observed": min(len(self._probe_seen), self.probe_bytes),
            "decision_byte": decision,
            "decision_global_byte": self._block_start + decision,
            "admitted": admitted,
            "route": self.specialist_name if admitted else self.cheap_name,
        }

    def _switch_block(self, block_index: int) -> None:
        if self._block_index is not None:
            self._completed.append(self._snapshot())
        self._block_index = block_index
        self._block_start = block_index * self.block_bytes
        self._cheap = self.cheap_factory()
        self._specialist = None
        self._probe_seen = []
        self._last_probe_cdf = None
        self._probe_num = 1
        self._probe_den = 1
        self._admitted = None

    def _sync_probe(self, local_prefix: Sequence[int]) -> None:
        assert self._cheap is not None
        target = min(len(local_prefix), self.probe_bytes)
        if list(local_prefix[: len(self._probe_seen)]) != self._probe_seen:
            raise ValueError("admission router received a divergent block prefix")
        while len(self._probe_seen) < target:
            index = len(self._probe_seen)
            if self._last_probe_cdf is None:
                self._last_probe_cdf = self._cheap(index, self._probe_seen)
            symbol = int(local_prefix[index])
            num, den = self._term(self._last_probe_cdf, symbol)
            self._probe_num *= num
            self._probe_den *= den
            self._probe_seen.append(symbol)
            self._last_probe_cdf = None

    def _in_admission_band(self) -> bool:
        # min_bits <= -log2(P) <= max_bits, compared without floating point.
        at_least_min = self._probe_num * (1 << self.min_probe_code_bits) <= self._probe_den
        at_most_max = self._probe_num * (1 << self.max_probe_code_bits) >= self._probe_den
        return at_least_min and at_most_max

    def _maybe_decide(self, local_index: int) -> None:
        if self._admitted is not None:
            return
        assert self._block_index is not None
        block_length = self._block_length(self._block_index)
        if local_index < min(self.probe_bytes, block_length):
            return
        # No byte remains after the probe, so specialization cannot affect coding.
        if block_length <= self.probe_bytes or self.specialist_factory is None:
            self._admitted = False
            return
        self._admitted = self._in_admission_band()
        if self._admitted:
            self._specialist = self.specialist_factory()

    def __call__(self, index: int, prefix: Sequence[int]):
        if index != len(prefix):
            raise ValueError("index must equal prefix length")
        if index < 0 or index >= self.stream_bytes:
            raise ValueError("index outside configured stream")
        prefix_list = [int(value) for value in prefix]
        if (
            len(prefix_list) < len(self._last_prefix)
            or prefix_list[: len(self._last_prefix)] != self._last_prefix
        ):
            raise ValueError("admission router received a divergent stream prefix")
        self._last_prefix = prefix_list

        block_index = index // self.block_bytes
        if self._block_index != block_index:
            self._switch_block(block_index)
        assert self._cheap is not None

        local_prefix = prefix_list[self._block_start :]
        local_index = len(local_prefix)
        self._sync_probe(local_prefix)
        self._maybe_decide(local_index)

        if self._admitted:
            assert self._specialist is not None
            self.specialist_output_calls += 1
            return self._specialist(local_index, local_prefix)

        cheap_cdf = self._cheap(local_index, local_prefix)
        if local_index < self.probe_bytes:
            self._last_probe_cdf = cheap_cdf
        return cheap_cdf

    def block_summary(self) -> list[dict[str, int | str | bool]]:
        rows = list(self._completed)
        if self._block_index is not None:
            rows.append(self._snapshot())
        return rows

    @property
    def admitted_blocks(self) -> int:
        return sum(bool(row["admitted"]) for row in self.block_summary())

    @property
    def admission_fraction(self) -> float:
        rows = self.block_summary()
        if not rows:
            return 0.0
        return self.admitted_blocks / len(rows)


def cheap_codelength_admission_fingerprint(
    *,
    cheap_fingerprint: bytes,
    specialist_fingerprint: bytes | None,
    stream_bytes: int,
    block_bytes: int,
    probe_bytes: int,
    min_probe_code_bits: int,
    max_probe_code_bits: int,
) -> bytes:
    if len(cheap_fingerprint) != 32:
        raise ValueError("cheap fingerprint must be 32 bytes")
    if specialist_fingerprint is not None and len(specialist_fingerprint) != 32:
        raise ValueError("specialist fingerprint must be 32 bytes")
    if stream_bytes < 0 or block_bytes <= 0:
        raise ValueError("invalid stream/block size")
    if probe_bytes <= 0 or probe_bytes >= block_bytes:
        raise ValueError("invalid probe size")
    if min_probe_code_bits < 0 or max_probe_code_bits < min_probe_code_bits:
        raise ValueError("invalid probe codelength band")
    payload = {
        "kind": "pollicino-cheap-codelength-admission-v1",
        "cheap_fingerprint": cheap_fingerprint.hex(),
        "specialist_fingerprint": specialist_fingerprint.hex() if specialist_fingerprint else None,
        "stream_bytes": int(stream_bytes),
        "block_bytes": int(block_bytes),
        "probe_bytes": int(probe_bytes),
        "min_probe_code_bits": int(min_probe_code_bits),
        "max_probe_code_bits": int(max_probe_code_bits),
        "state_scope": "block-reset",
        "specialist_creation": "lazy-after-cheap-probe",
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).digest()
