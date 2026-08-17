from __future__ import annotations

from pollicino.compression.block_routing import (
    BlockLocalBitCreditRouterCDFProvider,
    BlockResetCDFProvider,
    block_local_router_fingerprint,
)
from pollicino.compression.codec import decode_pol, encode_shared
from pollicino.compression.quantization import frequencies_to_cdf


class _BiasedProvider:
    def __init__(self, preferred: int, weight: int = 4096):
        self.preferred = preferred
        self.weight = weight
        self.calls = 0

    def __call__(self, _index, _prefix):
        self.calls += 1
        freq = [1] * 256
        freq[self.preferred] = self.weight
        return frequencies_to_cdf(freq)


def _factory(data: bytes, block_bytes: int = 64):
    return BlockLocalBitCreditRouterCDFProvider(
        lambda: _BiasedProvider(ord("B")),
        lambda: _BiasedProvider(ord("A")),
        stream_bytes=len(data),
        block_bytes=block_bytes,
        min_observations=4,
        max_probe_bytes=16,
        activation_credit_bits=2,
        rejection_credit_bits=2,
        cheap_name="cheap",
        specialist_name="neural",
    )


def test_block_router_can_switch_routes_between_blocks_and_roundtrip():
    data = (b"A" * 64) + (b"B" * 64) + (b"A" * 64)
    fp = b"r" * 32
    enc = _factory(data)
    blob = encode_shared(data, enc, fp, precision_bits=18)
    dec = _factory(data)
    restored = decode_pol(blob, shared_provider=dec, expected_model_fingerprint=fp)
    assert restored == data
    assert enc.block_summary() == dec.block_summary()
    assert [row["route"] for row in enc.block_summary()] == ["neural", "cheap", "neural"]
    assert enc.switch_count == 2


def test_block_router_reject_stops_specialist_only_for_current_block():
    data = (b"B" * 64) + (b"A" * 64)
    router = _factory(data)
    prefix: list[int] = []
    for i, symbol in enumerate(data):
        router(i, prefix)
        prefix.append(symbol)
    rows = router.block_summary()
    assert rows[0]["route"] == "cheap"
    assert rows[0]["specialist_calls"] <= 16
    assert rows[1]["route"] == "neural"
    assert rows[1]["specialist_calls"] == 64
    assert rows[1]["decision_global_byte"] == 64 + rows[1]["decision_byte"]


def test_block_router_recreates_experts_and_restarts_local_prefix_each_block():
    creations = {"cheap": 0, "specialist": 0}
    seen_indexes = {"cheap": [], "specialist": []}

    class Recorder:
        def __init__(self, name: str):
            self.name = name
            creations[name] += 1

        def __call__(self, index, prefix):
            assert index == len(prefix)
            seen_indexes[self.name].append(index)
            return frequencies_to_cdf([1] * 256)

    data = bytes(range(20))
    router = BlockLocalBitCreditRouterCDFProvider(
        lambda: Recorder("cheap"),
        lambda: Recorder("specialist"),
        stream_bytes=len(data),
        block_bytes=8,
        min_observations=2,
        max_probe_bytes=4,
        activation_credit_bits=20,
        rejection_credit_bits=20,
    )
    prefix: list[int] = []
    for i, symbol in enumerate(data):
        router(i, prefix)
        prefix.append(symbol)

    assert creations == {"cheap": 3, "specialist": 3}
    assert seen_indexes["cheap"].count(0) == 3
    assert seen_indexes["specialist"].count(0) == 3
    assert max(seen_indexes["cheap"]) <= 7
    assert max(seen_indexes["specialist"]) <= 3


def test_block_router_handles_short_last_block():
    data = (b"A" * 64) + (b"B" * 17)
    router = _factory(data)
    prefix: list[int] = []
    for i, symbol in enumerate(data):
        router(i, prefix)
        prefix.append(symbol)
    rows = router.block_summary()
    assert [row["block_bytes"] for row in rows] == [64, 17]
    assert sum(int(row["block_bytes"]) for row in rows) == len(data)


def test_block_router_without_specialist_is_all_cheap():
    data = b"A" * 150
    router = BlockLocalBitCreditRouterCDFProvider(
        lambda: _BiasedProvider(ord("A")),
        None,
        stream_bytes=len(data),
        block_bytes=64,
        min_observations=4,
        max_probe_bytes=16,
        activation_credit_bits=0,
        rejection_credit_bits=2,
    )
    prefix: list[int] = []
    for i, symbol in enumerate(data):
        router(i, prefix)
        prefix.append(symbol)
    assert {row["route"] for row in router.block_summary()} == {"cheap"}
    assert router.specialist_calls == 0


def test_block_reset_provider_restarts_local_index_each_block():
    seen_indexes: list[list[int]] = []

    class Recorder:
        def __init__(self):
            seen_indexes.append([])

        def __call__(self, index, _prefix):
            seen_indexes[-1].append(index)
            return frequencies_to_cdf([1] * 256)

    data = bytes(range(10))
    provider = BlockResetCDFProvider(Recorder, stream_bytes=len(data), block_bytes=4)
    prefix: list[int] = []
    for i, symbol in enumerate(data):
        provider(i, prefix)
        prefix.append(symbol)
    assert seen_indexes == [[0, 1, 2, 3], [0, 1, 2, 3], [0, 1]]


def test_block_router_fingerprint_commits_to_block_and_policy():
    base = dict(
        cheap_fingerprint=b"a" * 32,
        specialist_fingerprint=b"b" * 32,
        stream_bytes=4096,
        block_bytes=1024,
        min_observations=4,
        max_probe_bytes=16,
        activation_credit_bits=8,
        rejection_credit_bits=6,
    )
    fp = block_local_router_fingerprint(**base)
    assert len(fp) == 32
    assert fp != block_local_router_fingerprint(**{**base, "block_bytes": 512})
    assert fp != block_local_router_fingerprint(**{**base, "activation_credit_bits": 10})
