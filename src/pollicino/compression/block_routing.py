from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence

from .bit_credit_routing import BitCreditSpecialistRouterCDFProvider


class BlockLocalBitCreditRouterCDFProvider:
    """Reset and re-route cheap/specialist experts independently in fixed blocks.

    Each block owns a fresh :class:`BitCreditSpecialistRouterCDFProvider`. Only the
    bytes already decoded inside the current block are shown to that router and to
    its experts. This makes neural compute accounting honest: after a cheap reject,
    the specialist is not evaluated again until the next block, where a fresh
    specialist starts from deterministic empty block state rather than replaying
    skipped bytes from the preceding block.

    The reset is part of the codec definition and creates an explicit context-reset
    tax. Encoder and decoder know the same block boundaries and reconstruct the same
    route decisions without selector side bits.
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

        self._block_index: int | None = None
        self._block_start = 0
        self._router: BitCreditSpecialistRouterCDFProvider | None = None
        self._completed: list[dict[str, int | str | float]] = []
        self._last_prefix: list[int] = []

    def _block_length(self, block_index: int) -> int:
        start = block_index * self.block_bytes
        return max(0, min(self.block_bytes, self.stream_bytes - start))

    def _new_router(self, block_index: int) -> BitCreditSpecialistRouterCDFProvider:
        length = self._block_length(block_index)
        specialist = self.specialist_factory() if self.specialist_factory is not None else None
        return BitCreditSpecialistRouterCDFProvider(
            self.cheap_factory(),
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

    def _switch_block(self, block_index: int) -> None:
        if self._router is not None and self._block_index is not None:
            self._completed.append(self._snapshot(self._block_index, self._router))
        self._block_index = block_index
        self._block_start = block_index * self.block_bytes
        self._router = self._new_router(block_index)

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
            self._switch_block(block_index)
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
    """Run a fresh provider instance in every deterministic fixed-size block."""

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
        "state_scope": "block-reset",
        "min_observations": int(min_observations),
        "max_probe_bytes": int(max_probe_bytes),
        "activation_credit_bits": int(activation_credit_bits),
        "rejection_credit_bits": int(rejection_credit_bits),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).digest()
