from __future__ import annotations

from pollicino.compression.adaptive import AdaptiveNGramCDFProvider, adaptive_fingerprint
from pollicino.compression.gating import (
    DeterministicExpertGateCDFProvider,
    RollingLikelihoodGate,
    expert_gate_fingerprint,
)
from pollicino.compression.quantization import frequencies_to_cdf
from pollicino.compression.range_coder import decode_symbols, encode_symbols


class _StaticExpert:
    def __init__(self, favored: int):
        self.favored = favored

    def __call__(self, _index, _prefix):
        freqs = [1] * 256
        freqs[self.favored] = 1000
        return frequencies_to_cdf(freqs)


def _roundtrip(data: bytes, factory):
    encoder = factory()
    prefix: list[int] = []
    cdfs = []
    for i, symbol in enumerate(data):
        cdfs.append(encoder(i, prefix))
        prefix.append(symbol)
    payload, bits = encode_symbols(data, cdfs)
    decoder = factory()
    restored = bytes(decode_symbols(payload, len(data), decoder))
    assert restored == data
    return bits, encoder, decoder


def test_rolling_gate_uses_exact_integer_likelihood_and_stable_ties():
    gate = RollingLikelihoodGate(2, window=3)
    assert gate.choice() == 0
    gate.observe([(1, 10), (9, 10)])
    assert gate.choice() == 1
    gate.observe([(9, 10), (1, 10)])
    assert gate.choice() == 0  # exact tie -> first expert
    gate.observe([(9, 10), (1, 10)])
    assert gate.choice() == 0
    gate.observe([(1, 10), (9, 10)])  # first observation falls out
    assert gate.choice() == 0


def test_expert_gate_switches_after_causal_evidence():
    factory = lambda: DeterministicExpertGateCDFProvider(
        [_StaticExpert(ord("a")), _StaticExpert(ord("b"))],
        names=("a", "b"),
        window=4,
    )
    provider = factory()
    prefix: list[int] = []
    provider(0, prefix)
    assert provider.choice_counts == [1, 0]
    prefix.append(ord("b"))
    provider(1, prefix)
    assert provider.choice_counts == [1, 1]


def test_expert_gate_roundtrip_with_adaptive_experts():
    def factory():
        return DeterministicExpertGateCDFProvider(
            [
                AdaptiveNGramCDFProvider(max_order=2, order_weights=(1, 4, 16)),
                AdaptiveNGramCDFProvider(max_order=3, order_weights=(1, 4, 16, 64)),
            ],
            names=("o2", "o3"),
            window=16,
        )

    data = (b"abracadabra" * 100) + bytes(range(64))
    bits, encoder, decoder = _roundtrip(data, factory)
    assert bits > 0
    assert encoder.choice_counts == decoder.choice_counts
    assert sum(encoder.choice_counts) == len(data)


def test_gate_fingerprint_changes_with_window_or_expert():
    a = adaptive_fingerprint(max_order=2, order_weights=(1, 4, 16))
    b = adaptive_fingerprint(max_order=3, order_weights=(1, 4, 16, 64))
    fp1 = expert_gate_fingerprint(expert_fingerprints=(a, b), names=("o2", "o3"), window=16)
    fp2 = expert_gate_fingerprint(expert_fingerprints=(a, b), names=("o2", "o3"), window=64)
    fp3 = expert_gate_fingerprint(expert_fingerprints=(b, a), names=("o3", "o2"), window=16)
    assert len(fp1) == len(fp2) == len(fp3) == 32
    assert len({fp1, fp2, fp3}) == 3
