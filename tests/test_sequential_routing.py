from __future__ import annotations

from pollicino.compression.quantization import frequencies_to_cdf
from pollicino.compression.range_coder import decode_symbols, encode_symbols
from pollicino.compression.sequential_routing import (
    SequentialSpecialistRouterCDFProvider,
    sequential_router_fingerprint,
)


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
    enc = factory()
    prefix: list[int] = []
    cdfs = []
    for i, symbol in enumerate(data):
        cdfs.append(enc(i, prefix))
        prefix.append(symbol)
    payload, bits = encode_symbols(data, cdfs)
    dec = factory()
    restored = bytes(decode_symbols(payload, len(data), dec))
    assert restored == data
    assert enc.selected_route == dec.selected_route
    assert enc.decision_byte == dec.decision_byte
    assert enc.choice_counts == dec.choice_counts
    return enc, dec, bits


def test_sequential_router_activates_specialist_early_on_strong_evidence():
    data = b"A" * 200

    def factory():
        return SequentialSpecialistRouterCDFProvider(
            _BiasedProvider(ord("B")),
            _BiasedProvider(ord("A")),
            stream_bytes=len(data),
            min_observations=8,
            max_probe_bytes=64,
            activate_ratio_num=16,
            reject_ratio_num=1,
            reject_ratio_den=16,
        )

    enc, _dec, bits = _roundtrip(data, factory)
    assert enc.selected_route == "specialist"
    assert enc.decision_byte == 8
    assert enc.probe_count == 8
    assert bits / len(data) < 3.0


def test_sequential_router_rejects_specialist_early_and_stops_compute():
    data = b"B" * 200
    cheap = _BiasedProvider(ord("B"))
    specialist = _BiasedProvider(ord("A"))
    router = SequentialSpecialistRouterCDFProvider(
        cheap,
        specialist,
        stream_bytes=len(data),
        min_observations=8,
        max_probe_bytes=64,
        activate_ratio_num=16,
        reject_ratio_num=1,
        reject_ratio_den=16,
    )
    prefix: list[int] = []
    for i, symbol in enumerate(data):
        router(i, prefix)
        prefix.append(symbol)

    assert router.selected_route == "cheap"
    assert router.decision_byte == 8
    assert router.specialist_calls == 8
    assert specialist.calls == 8
    assert cheap.calls == len(data)


def test_sequential_router_defaults_to_cheap_at_probe_cap():
    data = bytes([65, 66]) * 100

    def factory():
        return SequentialSpecialistRouterCDFProvider(
            _BiasedProvider(65, weight=300),
            _BiasedProvider(65, weight=301),
            stream_bytes=len(data),
            min_observations=8,
            max_probe_bytes=32,
            activate_ratio_num=1_000_000,
            reject_ratio_num=1,
            reject_ratio_den=1_000_000,
        )

    enc, _dec, _bits = _roundtrip(data, factory)
    assert enc.selected_route == "cheap"
    assert enc.decision_byte == 32
    assert enc.specialist_calls == 32


def test_sequential_router_skips_specialist_if_unavailable_or_too_short():
    data = b"A" * 8
    cheap = _BiasedProvider(ord("A"))
    specialist = _BiasedProvider(ord("A"))
    router = SequentialSpecialistRouterCDFProvider(
        cheap,
        specialist,
        stream_bytes=len(data),
        min_observations=8,
        max_probe_bytes=32,
    )
    prefix: list[int] = []
    for i, symbol in enumerate(data):
        router(i, prefix)
        prefix.append(symbol)
    assert router.selected_route == "cheap"
    assert router.specialist_calls == 0

    unavailable = SequentialSpecialistRouterCDFProvider(
        _BiasedProvider(ord("A")),
        None,
        stream_bytes=200,
        min_observations=8,
        max_probe_bytes=32,
    )
    prefix = []
    for i, symbol in enumerate(b"A" * 20):
        unavailable(i, prefix)
        prefix.append(symbol)
    assert unavailable.selected_route == "cheap"
    assert unavailable.specialist_calls == 0


def test_sequential_router_respects_min_stream_cost_gate():
    specialist = _BiasedProvider(ord("A"))
    router = SequentialSpecialistRouterCDFProvider(
        _BiasedProvider(ord("B")),
        specialist,
        stream_bytes=4096,
        min_stream_bytes=1 << 20,
        min_observations=8,
        max_probe_bytes=32,
    )
    prefix: list[int] = []
    for i, symbol in enumerate(b"A" * 20):
        router(i, prefix)
        prefix.append(symbol)
    assert router.selected_route == "cheap"
    assert specialist.calls == 0


def test_sequential_router_fingerprint_commits_to_thresholds():
    base = dict(
        cheap_fingerprint=b"a" * 32,
        specialist_fingerprint=b"b" * 32,
        stream_bytes=4096,
        min_stream_bytes=0,
        min_observations=16,
        max_probe_bytes=128,
        activate_ratio_num=16,
        activate_ratio_den=1,
        reject_ratio_num=1,
        reject_ratio_den=16,
    )
    fp = sequential_router_fingerprint(**base)
    assert len(fp) == 32
    assert fp != sequential_router_fingerprint(**{**base, "min_observations": 32})
    assert fp != sequential_router_fingerprint(**{**base, "activate_ratio_num": 32})
    assert fp != sequential_router_fingerprint(**{**base, "stream_bytes": 8192})


def test_sequential_router_roundtrip_with_separate_state():
    data = (b"POLLICINO" * 60) + bytes(range(128))

    def factory():
        return SequentialSpecialistRouterCDFProvider(
            _BiasedProvider(ord("P"), weight=32),
            _BiasedProvider(ord("O"), weight=48),
            stream_bytes=len(data),
            min_observations=16,
            max_probe_bytes=64,
            activate_ratio_num=4,
            activate_ratio_den=1,
            reject_ratio_num=1,
            reject_ratio_den=4,
        )

    enc, dec, _bits = _roundtrip(data, factory)
    assert enc.selected_route in {"cheap", "specialist"}
    assert dec.selected_route == enc.selected_route
