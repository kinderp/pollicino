from __future__ import annotations

import math

from pollicino.compression.adaptive import (
    AdaptiveNGramCDFProvider,
    NeuralPriorAdaptiveCDFProvider,
    adaptive_fingerprint,
)
from pollicino.compression.quantization import frequencies_to_cdf
from pollicino.compression.range_coder import decode_symbols, encode_symbols


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
    return bits


def test_adaptive_provider_roundtrips_repetition_and_binary():
    factory = lambda: AdaptiveNGramCDFProvider(max_order=3, order_weights=(1, 4, 16, 64))
    assert _roundtrip(b"aaaaabaaaaab" * 80, factory) > 0
    assert _roundtrip(bytes(range(256)) * 4, factory) > 0


def test_adaptive_repetition_beats_uniform_eight_bpb():
    data = b"a" * 1000
    bits = _roundtrip(data, lambda: AdaptiveNGramCDFProvider(max_order=3, order_weights=(1, 4, 16, 64)))
    assert bits / len(data) < 1.0


def test_symbol_mass_matches_generated_cdf_probability():
    provider = AdaptiveNGramCDFProvider(max_order=2, order_weights=(1, 4, 16))
    prefix = [97, 98, 97, 98, 97]
    num, den = provider.symbol_mass(len(prefix), prefix, 98)
    cdf = provider(len(prefix), prefix)
    assert cdf[99] - cdf[98] == num
    assert cdf[-1] == den


class _StaticPrior:
    def __call__(self, _index, _prefix):
        freqs = [1] * 256
        freqs[ord("a")] = 1024
        return frequencies_to_cdf(freqs)


def test_neural_prior_adaptive_roundtrip_is_reproducible():
    factory = lambda: NeuralPriorAdaptiveCDFProvider(
        _StaticPrior(), prior_strength=256, max_order=2, order_weights=(1, 4, 16)
    )
    data = b"adaptive prior aaaabbbbcccc" * 20
    assert _roundtrip(data, factory) > 0


def test_adaptive_fingerprint_changes_with_configuration():
    a = adaptive_fingerprint(max_order=2, order_weights=(1, 4, 16))
    b = adaptive_fingerprint(max_order=3, order_weights=(1, 4, 16, 64))
    c = adaptive_fingerprint(max_order=2, order_weights=(1, 4, 16), prior_strength=256, neural_fingerprint=b"x" * 32)
    assert len(a) == len(b) == len(c) == 32
    assert len({a, b, c}) == 3
