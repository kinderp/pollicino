from __future__ import annotations

from pollicino.compression.bit_credit_routing import (
    BitCreditSpecialistRouterCDFProvider,
    bit_credit_router_fingerprint,
)
from pollicino.compression.quantization import frequencies_to_cdf
from pollicino.compression.range_coder import decode_symbols, encode_symbols


class _BiasedProvider:
    def __init__(self, preferred: int, weight: int = 1024):
        self.preferred = preferred
        self.weight = weight
        self.calls = 0

    def __call__(self, _index, _prefix):
        self.calls += 1
        frequencies = [1] * 256
        frequencies[self.preferred] = self.weight
        return frequencies_to_cdf(frequencies)


def _roundtrip(data: bytes, factory):
    encoder = factory()
    prefix: list[int] = []
    cdfs = []
    for index, symbol in enumerate(data):
        cdfs.append(encoder(index, prefix))
        prefix.append(symbol)
    payload, bit_length = encode_symbols(data, cdfs)
    decoder = factory()
    restored = bytes(decode_symbols(payload, len(data), decoder))
    assert restored == data
    assert encoder.selected_route == decoder.selected_route
    assert encoder.decision_byte == decoder.decision_byte
    return encoder, decoder, bit_length


def test_bit_credit_activates_on_positive_credit():
    data = b"A" * 200

    def factory():
        return BitCreditSpecialistRouterCDFProvider(
            _BiasedProvider(ord("B")),
            _BiasedProvider(ord("A")),
            stream_bytes=len(data),
            min_observations=8,
            max_probe_bytes=64,
            activation_credit_bits=4,
            rejection_credit_bits=12,
        )

    encoder, _decoder, _bits = _roundtrip(data, factory)
    assert encoder.selected_route == "specialist"
    assert encoder.decision_byte == 8


def test_bit_credit_supports_asymmetric_rejection():
    data = b"B" * 200

    fast_reject = BitCreditSpecialistRouterCDFProvider(
        _BiasedProvider(ord("B")),
        _BiasedProvider(ord("A")),
        stream_bytes=len(data),
        min_observations=8,
        max_probe_bytes=64,
        activation_credit_bits=8,
        rejection_credit_bits=2,
    )
    prefix: list[int] = []
    for index, symbol in enumerate(data):
        fast_reject(index, prefix)
        prefix.append(symbol)
    assert fast_reject.selected_route == "cheap"
    assert fast_reject.decision_byte == 8
    assert fast_reject.specialist_calls == 8


def test_bit_credit_compute_fraction_tracks_specialist_calls():
    data = b"B" * 200
    router = BitCreditSpecialistRouterCDFProvider(
        _BiasedProvider(ord("B")),
        _BiasedProvider(ord("A")),
        stream_bytes=len(data),
        min_observations=8,
        max_probe_bytes=64,
        activation_credit_bits=8,
        rejection_credit_bits=2,
    )
    prefix: list[int] = []
    for index, symbol in enumerate(data):
        router(index, prefix)
        prefix.append(symbol)
    assert router.compute_fraction == 8 / len(data)


def test_bit_credit_fingerprint_commits_to_asymmetric_thresholds():
    base = dict(
        cheap_fingerprint=b"a" * 32,
        specialist_fingerprint=b"b" * 32,
        stream_bytes=4096,
        min_stream_bytes=0,
        min_observations=8,
        max_probe_bytes=64,
        activation_credit_bits=8,
        rejection_credit_bits=8,
    )
    fp = bit_credit_router_fingerprint(**base)
    assert len(fp) == 32
    assert fp != bit_credit_router_fingerprint(**{**base, "activation_credit_bits": 6})
    assert fp != bit_credit_router_fingerprint(**{**base, "rejection_credit_bits": 12})
    assert fp != bit_credit_router_fingerprint(**{**base, "stream_bytes": 8192})


def test_bit_credit_unavailable_specialist_is_cheap_without_calls():
    router = BitCreditSpecialistRouterCDFProvider(
        _BiasedProvider(ord("A")),
        None,
        stream_bytes=200,
        min_observations=8,
        max_probe_bytes=64,
        activation_credit_bits=4,
        rejection_credit_bits=8,
    )
    prefix: list[int] = []
    for index, symbol in enumerate(b"A" * 20):
        router(index, prefix)
        prefix.append(symbol)
    assert router.selected_route == "cheap"
    assert router.specialist_calls == 0
