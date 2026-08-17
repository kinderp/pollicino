from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence

from .bit_credit_routing import BitCreditSpecialistRouterCDFProvider


class _GlobalPrefixAdapter:
    """Expose a global-state provider through a block-local prefix interface."""

    def __init__(self, provider, base_prefix: Sequence[int]) -> None:
        self.provider = provider
        self.base_prefix = tuple(int(value) for value in base_prefix)

    def __call__(self, index: int, prefix: Sequence[int]):
        if index != len(prefix):
            raise ValueError("index must equal prefix length")
        global_prefix = self.base_prefix + tuple(int(value) for value in prefix)
        return self.provider(len(global_prefix), global_prefix)


class BlockLocalBitCreditRouterCDFProvider:
    """Re-evaluate a cheap/specialist route independently in fixed-size blocks.

    The routing evidence and decision are reset at deterministic block boundaries,
    but the cheap and specialist provider instances are *not* reset.  Both experts
    continue to see the complete decoded prefix of the file.  This isolates the
    effect of local routing from a second, confounding change in model context.

    A specialist that was not evaluated for part of a block is allowed to catch up
    from the global prefix when the next block starts.  POLLICINO providers are
    causal prefix-replay providers, so encoder and decoder reconstruct the same
    expert state without a selector side stream.
    """

    def __init__(
        self,
        cheap_factory: Callable[[], object],
        specialist_factory: Callable[[], object] | None,
        *,
        stream_bytes: int,
        block_bytes: int,
        min_observations: int,
        max_probe_bytes: int,
        activation_credit_bits: int,
        rejection_credit_bits: int,
        cheap_name: str = "cheap",
        specialist_name: str = "specialist",
    ) -> None:
        if stream_bytes < 0:
            raise ValueError("stream_bytes must be non-negative")
        if block_bytes <= 0:
            raise ValueError("block_bytes must be positive")
        if min_observations <= 0:
            raise ValueError("min_observations must be positive")
        if max_probe_bytes < min_observations:
            raise ValueError("max_probe_bytes must be >= min_observations")
        if activation_credit_bits < 0 or rejection_credit_bits < 0:
            raise ValueError("bit-credit thresholds must be non-negative")
        if not cheap_name or not specialist_name or cheap_name == specialist_name:
            raise ValueError("route names must be distinct non-empty strings")

        self.cheap_factory = cheap_factory
        self.specialist_factory = specialist_factory
        self.stream_bytes = int(stream_bytes)
        self.block_bytes = int(block_bytes)
        self.min_observations = int(min_observations)
        self.max_probe_bytes = int(max_probe_bytes)
        self.activation_credit_bits = int(activation_credit_bits)
        self.rejection_credit_bits = int(rejection_credit_bits)
        self.cheap_name = str(cheap_name)
        self.specialist_name = str(specialist_name)

        # Expert state is file-global. Only these router wrappers are replaced at
        # block boundaries.
        self._cheap_provider = self.cheap_factory()
        self._specialist_provider = (
            self.specialist_factory() if self.specialist_factory is not None else None
        )

        self._block_index: int | None = None
        self._block_start = 0
        self._router: BitCreditSpecialistRouterCDFProvider | None = None
        self._completed: list[dict[str, int | str | float]] = []
        self._last_prefix: list[int] = []

    def _block_length(self, block_index: int) -> int:
        start = block_index * self.block_bytes
        return max(0, min(self.block_bytes, self.stream_bytes - start))

    def _new_router(
        self,
        block_index: int,
        base_prefix: Sequence[int],
    ) -> BitCreditSpecialistRouterCDFProvider:
        length = self._block_length(block_index)
        cheap = _GlobalPrefixAdapter(self._cheap_provider, base_prefix)
        specialist = (
            _GlobalPrefixAdapter(self._specialist_provider, base_prefix)
            if self._specialist_provider is not None
            else None
        )
        return BitCreditSpecialistRouterCDFProvider(
            cheap,
            specialist,
            stream_bytes=length,
            min_stream_bytes=0,
            min_observations=self.min_observations,
            max_probe_bytes=self.max_probe_bytes,
            activation_credit_bits=self.activation_credit_bits,
            rejection_credit_bits=self.rejection_credit_bits,
            cheap_name=self.cheap_name,
            specialist_name=self.specialist_name,
        )

    def _snapshot(
        self,
        block_index: int,
        router: BitCreditSpecialistRouterCDFProvider,
    ) -> dict[str, int | str | float]:
        local_decision = int(router.decision_byte or 0)
        return {
            "block_index": block_index,
            "block_start": block_index * self.block_bytes,
            "block_bytes": self._block_length(block_index),
            "route": router.selected_route,
            "decision_byte": local_decision,
            "decision_global_byte": block_index * self.block_bytes + local_decision,
            "specialist_calls": int(router.specialist_calls),
            "compute_fraction": float(router.compute_fraction),
        }

    def _switch_block(self, block_index: int, prefix: Sequence[int]) -> None:
        if self._router is not None and self._block_index is not None:
            self._completed.append(self._snapshot(self._block_index, self._router))
        self._block_index = block_index
        self._block_start = block_index * self.block_bytes
        base_prefix = prefix[: self._block_start]
        self._router = self._new_router(block_index, base_prefix)

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
            raise ValueError("block router received a divergent prefix")
        self._last_prefix = prefix_list

        block_index = index // self.block_bytes
        if self._block_index != block_index:
            self._switch_block(block_index, prefix_list)
        assert self._router is not None
        local_prefix = prefix_list[self._block_start :]
        return self._router(len(local_prefix), local_prefix)

    def block_summary(self) -> list[dict[str, int | str | float]]:
        rows = list(self._completed)
        if self._router is not None and self._block_index is not None:
            rows.append(self._snapshot(self._block_index, self._router))
        return rows

    @property
    def specialist_calls(self) -> int:
        return sum(int(row["specialist_calls"]) for row in self.block_summary())

    @property
    def compute_fraction(self) -> float:
        if self.stream_bytes <= 0:
            return 0.0
        return min(1.0, self.specialist_calls / self.stream_bytes)

    @property
    def switch_count(self) -> int:
        routes = [str(row["route"]) for row in self.block_summary()]
        return sum(a != b for a, b in zip(routes, routes[1:]))


class BlockResetCDFProvider:
    """Ablation provider that deliberately resets model state in every block."""

    def __init__(self, provider_factory: Callable[[], object], *, stream_bytes: int, block_bytes: int) -> None:
        if stream_bytes < 0 or block_bytes <= 0:
            raise ValueError("invalid stream/block size")
        self.provider_factory = provider_factory
        self.stream_bytes = int(stream_bytes)
        self.block_bytes = int(block_bytes)
        self._block_index: int | None = None
        self._block_start = 0
        self._provider = None

    def __call__(self, index: int, prefix: Sequence[int]):
        if index != len(prefix):
            raise ValueError("index must equal prefix length")
        if index < 0 or index >= self.stream_bytes:
            raise ValueError("index outside configured stream")
        block_index = index // self.block_bytes
        if self._block_index != block_index:
            self._block_index = block_index
            self._block_start = block_index * self.block_bytes
            self._provider = self.provider_factory()
        assert self._provider is not None
        local_prefix = prefix[self._block_start :]
        return self._provider(len(local_prefix), local_prefix)


def block_local_router_fingerprint(
    *,
    cheap_fingerprint: bytes,
    specialist_fingerprint: bytes | None,
    stream_bytes: int,
    block_bytes: int,
    min_observations: int,
    max_probe_bytes: int,
    activation_credit_bits: int,
    rejection_credit_bits: int,
) -> bytes:
    if len(cheap_fingerprint) != 32:
        raise ValueError("cheap fingerprint must be 32 bytes")
    if specialist_fingerprint is not None and len(specialist_fingerprint) != 32:
        raise ValueError("specialist fingerprint must be 32 bytes")
    if stream_bytes < 0 or block_bytes <= 0:
        raise ValueError("invalid stream/block size")
    if min_observations <= 0 or max_probe_bytes < min_observations:
        raise ValueError("invalid probe bounds")
    if activation_credit_bits < 0 or rejection_credit_bits < 0:
        raise ValueError("bit-credit thresholds must be non-negative")
    payload = {
        "kind": "pollicino-block-local-bit-credit-router-v1",
        "cheap_fingerprint": cheap_fingerprint.hex(),
        "specialist_fingerprint": specialist_fingerprint.hex() if specialist_fingerprint else None,
        "stream_bytes": int(stream_bytes),
        "block_bytes": int(block_bytes),
        "min_observations": int(min_observations),
        "max_probe_bytes": int(max_probe_bytes),
        "activation_credit_bits": int(activation_credit_bits),
        "rejection_credit_bits": int(rejection_credit_bits),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).digest()
