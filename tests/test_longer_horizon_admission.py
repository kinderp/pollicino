from __future__ import annotations

from pollicino.compression.admission_routing import (
    CheapAdmissionDecisionTree,
    DecisionTreeNode,
    RichCheapAdmissionBlockCDFProvider,
)
from pollicino.compression.codec import decode_pol, encode_shared
from pollicino.compression.quantization import frequencies_to_cdf


class _UniformProvider:
    def __call__(self, index, prefix):
        assert index == len(prefix)
        return frequencies_to_cdf([1] * 256)


class _PreferredProvider:
    def __init__(self, preferred: int):
        self.preferred = preferred

    def __call__(self, index, prefix):
        assert index == len(prefix)
        frequencies = [1] * 256
        frequencies[self.preferred] = 4096
        return frequencies_to_cdf(frequencies)


def _rule(threshold: int) -> CheapAdmissionDecisionTree:
    return CheapAdmissionDecisionTree(
        (
            DecisionTreeNode(
                feature="unique_count", threshold=threshold, less_equal=1, greater=2
            ),
            DecisionTreeNode(value=1),
            DecisionTreeNode(value=0),
        ),
        threshold=1,
    )


def _route(data: bytes, *, threshold: int = 20, max_bytes: int | None = None):
    created = 0

    def specialist_factory():
        nonlocal created
        created += 1
        return _PreferredProvider(ord("A"))

    provider = RichCheapAdmissionBlockCDFProvider(
        _UniformProvider,
        specialist_factory,
        _rule(threshold),
        stream_bytes=len(data),
        block_bytes=64,
        probe_bytes=32,
        max_admitted_bytes=len(data) if max_bytes is None else max_bytes,
    )
    prefix: list[int] = []
    created_before_decision = []
    for index, symbol in enumerate(data):
        provider(index, prefix)
        if index < 32:
            created_before_decision.append(created)
        prefix.append(symbol)
    return provider, created_before_decision


def test_exactly_32_consumed_bytes_control_route_and_byte_33_cannot():
    probe = bytes(range(20)) + b"\0" * 12
    first, _ = _route(probe + b"B" * 32, threshold=20)
    second, _ = _route(probe + bytes(range(100, 132)), threshold=20)
    assert first.block_summary()[0]["admitted"]
    assert second.block_summary()[0]["admitted"]
    changed_probe, _ = _route(bytes(range(21)) + b"A" * 11 + b"B" * 32, threshold=20)
    assert not changed_probe.block_summary()[0]["admitted"]


def test_neural_provider_is_not_created_before_32_byte_decision():
    provider, created_before_decision = _route(b"A" * 64, threshold=20)
    assert created_before_decision == [0] * 32
    assert provider.block_summary()[0]["decision_byte"] == 32
    assert provider.block_summary()[0]["admitted"]


def test_each_preregistered_threshold_boundary_is_exact():
    for threshold in (20, 22, 24, 26, 28, 30):
        at = bytes(range(threshold)) + bytes([0]) * (32 - threshold) + b"A" * 32
        above = (
            bytes(range(threshold + 1))
            + bytes([0]) * (31 - threshold)
            + b"A" * 32
        )
        assert _route(at, threshold=threshold)[0].block_summary()[0]["admitted"]
        assert not _route(above, threshold=threshold)[0].block_summary()[0]["admitted"]


def test_complete_block_budget_boundary_denies_one_block_beyond_limit():
    data = b"A" * 192
    allowed, _ = _route(data, threshold=20, max_bytes=128)
    denied, _ = _route(data, threshold=20, max_bytes=127)
    assert [row["admitted"] for row in allowed.block_summary()] == [True, True, False]
    assert [row["admitted"] for row in denied.block_summary()] == [True, False, False]


def test_32_byte_horizon_roundtrip_and_routes_match_without_side_bits():
    data = (b"A" * 64) + bytes(range(64)) + (b"AB" * 32)

    def factory():
        return RichCheapAdmissionBlockCDFProvider(
            _UniformProvider,
            lambda: _PreferredProvider(ord("A")),
            _rule(20),
            stream_bytes=len(data),
            block_bytes=64,
            probe_bytes=32,
            max_admitted_bytes=128,
        )

    fingerprint = b"p" * 32
    encoder = factory()
    blob = encode_shared(data, encoder, fingerprint, precision_bits=18)
    decoder = factory()
    restored = decode_pol(
        blob,
        shared_provider=decoder,
        expected_model_fingerprint=fingerprint,
    )
    assert restored == data
    assert encoder.block_summary() == decoder.block_summary()
