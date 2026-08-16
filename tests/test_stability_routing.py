from __future__ import annotations

from pollicino.compression.quantization import frequencies_to_cdf
from pollicino.compression.range_coder import decode_symbols, encode_symbols
from pollicino.compression.stability_routing import (
    StabilityValueSpecialistRouterCDFProvider,
    stability_value_router_fingerprint,
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


class _PhaseProvider:
    def __init__(self, *, good_until: int, symbol: int, good_weight: int = 4096, bad_weight: int = 4096):
        self.good_until = good_until
        self.symbol = symbol
        self.good_weight = good_weight
        self.bad_weight = bad_weight
        self.calls = 0

    def __call__(self, index, _prefix):
        self.calls += 1
        frequencies = [1] * 256
        if index < self.good_until:
            frequencies[self.symbol] = self.good_weight
        else:
            frequencies[(self.symbol + 1) % 256] = self.bad_weight
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
    assert enc.decision_reason == dec.decision_reason
    assert enc.choice_counts == dec.choice_counts
    assert enc.max_candidate_streak == dec.max_candidate_streak
    return enc, dec, bits


def test_stability_router_requires_persistent_recent_evidence_before_activation():
    data = b"A" * 200

    def factory():
        return StabilityValueSpecialistRouterCDFProvider(
            _BiasedProvider(ord("B")),
            _BiasedProvider(ord("A")),
            stream_bytes=len(data),
            min_observations=8,
            max_probe_bytes=64,
            activate_ratio_num=16,
            reject_ratio_num=1,
            reject_ratio_den=16,
            recent_window=4,
            recent_gain_bits=1,
            persistence_observations=3,
            min_projected_gain_bits=8,
        )

    enc, _dec, bits = _roundtrip(data, factory)
    assert enc.selected_route == "specialist"
    assert enc.decision_byte == 10
    assert enc.decision_reason == "stable-value-activate"
    assert enc.max_candidate_streak >= 3
    assert bits / len(data) < 3.0


def test_stability_router_rejects_transient_spike_without_persistence():
    data = b"A" * 80

    def factory():
        return StabilityValueSpecialistRouterCDFProvider(
            _BiasedProvider(ord("A"), weight=128),
            _PhaseProvider(good_until=8, symbol=ord("A")),
            stream_bytes=len(data),
            min_observations=8,
            max_probe_bytes=24,
            activate_ratio_num=2,
            reject_ratio_num=1,
            reject_ratio_den=1024,
            recent_window=1,
            recent_gain_bits=1,
            persistence_observations=2,
            min_projected_gain_bits=1,
        )

    enc, _dec, _bits = _roundtrip(data, factory)
    assert enc.selected_route == "cheap"
    assert enc.decision_byte <= 24
    assert enc.max_candidate_streak == 1


def test_stability_router_early_reject_stops_specialist_compute():
    data = b"B" * 200
    cheap = _BiasedProvider(ord("B"))
    specialist = _BiasedProvider(ord("A"))
    router = StabilityValueSpecialistRouterCDFProvider(
        cheap,
        specialist,
        stream_bytes=len(data),
        min_observations=8,
        max_probe_bytes=64,
        activate_ratio_num=16,
        reject_ratio_num=1,
        reject_ratio_den=16,
        recent_window=4,
        recent_gain_bits=1,
        persistence_observations=2,
        min_projected_gain_bits=8,
    )
    prefix: list[int] = []
    for i, symbol in enumerate(data):
        router(i, prefix)
        prefix.append(symbol)

    assert router.selected_route == "cheap"
    assert router.decision_byte == 8
    assert router.decision_reason == "cumulative-reject"
    assert specialist.calls == 8
    assert router.specialist_calls == 8


def test_stability_router_skips_specialist_when_future_value_cannot_repay_margin():
    data = b"A" * 40
    specialist = _BiasedProvider(ord("A"))
    router = StabilityValueSpecialistRouterCDFProvider(
        _BiasedProvider(ord("B")),
        specialist,
        stream_bytes=len(data),
        min_observations=8,
        max_probe_bytes=32,
        recent_window=8,
        recent_gain_bits=2,
        persistence_observations=2,
        min_projected_gain_bits=64,
    )
    prefix: list[int] = []
    for i, symbol in enumerate(data):
        router(i, prefix)
        prefix.append(symbol)

    assert router.selected_route == "cheap"
    assert router.decision_byte == 0
    assert router.decision_reason == "ineligible"
    assert router.specialist_calls == 0
    assert specialist.calls == 0


def test_stability_router_defaults_to_cheap_at_probe_cap_when_ambiguous():
    data = bytes([65, 66]) * 100

    def factory():
        return StabilityValueSpecialistRouterCDFProvider(
            _BiasedProvider(65, weight=300),
            _BiasedProvider(65, weight=301),
            stream_bytes=len(data),
            min_observations=8,
            max_probe_bytes=32,
            activate_ratio_num=1_000_000,
            reject_ratio_num=1,
            reject_ratio_den=1_000_000,
            recent_window=4,
            recent_gain_bits=8,
            persistence_observations=4,
            min_projected_gain_bits=0,
        )

    enc, _dec, _bits = _roundtrip(data, factory)
    assert enc.selected_route == "cheap"
    assert enc.decision_byte == 32
    assert enc.decision_reason == "probe-cap"


def test_stability_router_fingerprint_commits_to_stability_and_value_policy():
    base = dict(
        cheap_fingerprint=b"a" * 32,
        specialist_fingerprint=b"b" * 32,
        stream_bytes=4096,
        min_stream_bytes=0,
        min_observations=8,
        max_probe_bytes=96,
        activate_ratio_num=256,
        activate_ratio_den=1,
        reject_ratio_num=1,
        reject_ratio_den=256,
        recent_window=8,
        recent_gain_bits=2,
        persistence_observations=4,
        min_projected_gain_bits=64,
    )
    fp = stability_value_router_fingerprint(**base)
    assert len(fp) == 32
    assert fp != stability_value_router_fingerprint(**{**base, "recent_window": 16})
    assert fp != stability_value_router_fingerprint(**{**base, "persistence_observations": 8})
    assert fp != stability_value_router_fingerprint(**{**base, "min_projected_gain_bits": 128})
    assert fp != stability_value_router_fingerprint(**{**base, "stream_bytes": 8192})


def test_stability_router_roundtrip_with_separate_state():
    data = (b"POLLICINO" * 80) + bytes(range(128))

    def factory():
        return StabilityValueSpecialistRouterCDFProvider(
            _BiasedProvider(ord("P"), weight=32),
            _BiasedProvider(ord("O"), weight=48),
            stream_bytes=len(data),
            min_observations=8,
            max_probe_bytes=64,
            activate_ratio_num=4,
            activate_ratio_den=1,
            reject_ratio_num=1,
            reject_ratio_den=4,
            recent_window=4,
            recent_gain_bits=1,
            persistence_observations=3,
            min_projected_gain_bits=8,
        )

    enc, dec, _bits = _roundtrip(data, factory)
    assert enc.selected_route in {"cheap", "specialist"}
    assert dec.selected_route == enc.selected_route
