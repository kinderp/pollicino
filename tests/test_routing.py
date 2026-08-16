from __future__ import annotations

from pollicino.compression.quantization import frequencies_to_cdf
from pollicino.compression.range_coder import decode_symbols, encode_symbols
from pollicino.compression.routing import (
    CostAwareSpecialistRouterCDFProvider,
    cost_aware_router_fingerprint,
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


def _roundtrip(data: bytes, factory, fingerprint: bytes):
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
    assert encoder.selected_route == decoder.selected_route
    assert encoder.choice_counts == decoder.choice_counts
    return encoder, decoder, bits


def test_router_activates_specialist_after_probe_when_likelihood_is_better():
    data = b"A" * 200

    def factory():
        return CostAwareSpecialistRouterCDFProvider(
            _BiasedProvider(ord("B")),
            _BiasedProvider(ord("A")),
            stream_bytes=len(data),
            probe_bytes=32,
            min_stream_bytes=64,
        )

    encoder, _decoder, bits = _roundtrip(data, factory, b"x" * 32)
    assert encoder.selected_route == "specialist"
    assert encoder.probe_count == 32
    assert encoder.choice_counts["cheap"] == 32
    assert encoder.choice_counts["specialist"] == len(data) - 32
    assert bits / len(data) < 3.0


def test_router_locks_cheap_and_stops_specialist_compute_when_specialist_is_worse():
    data = b"B" * 200
    cheap = _BiasedProvider(ord("B"))
    specialist = _BiasedProvider(ord("A"))
    router = CostAwareSpecialistRouterCDFProvider(
        cheap,
        specialist,
        stream_bytes=len(data),
        probe_bytes=40,
        min_stream_bytes=64,
    )

    prefix: list[int] = []
    for i, symbol in enumerate(data):
        router(i, prefix)
        prefix.append(symbol)

    assert router.selected_route == "cheap"
    assert specialist.calls == 40
    assert cheap.calls == len(data)


def test_router_skips_specialist_when_stream_is_below_cost_threshold():
    data = b"A" * 128
    cheap = _BiasedProvider(ord("B"))
    specialist = _BiasedProvider(ord("A"))
    router = CostAwareSpecialistRouterCDFProvider(
        cheap,
        specialist,
        stream_bytes=len(data),
        probe_bytes=32,
        min_stream_bytes=1024,
    )

    prefix: list[int] = []
    for i, symbol in enumerate(data):
        router(i, prefix)
        prefix.append(symbol)

    assert router.selected_route == "cheap"
    assert router.probe_count == 0
    assert specialist.calls == 0
    assert cheap.calls == len(data)


def test_router_required_ratio_can_reject_a_small_specialist_advantage():
    data = bytes([65, 66]) * 100
    cheap = _BiasedProvider(65, weight=300)
    specialist = _BiasedProvider(65, weight=320)
    router = CostAwareSpecialistRouterCDFProvider(
        cheap,
        specialist,
        stream_bytes=len(data),
        probe_bytes=64,
        min_stream_bytes=0,
        required_ratio_num=4,
        required_ratio_den=1,
    )

    prefix: list[int] = []
    for i, symbol in enumerate(data):
        router(i, prefix)
        prefix.append(symbol)

    assert router.selected_route == "cheap"


def test_router_fingerprint_commits_to_policy_and_stream_size():
    base = dict(
        cheap_fingerprint=b"a" * 32,
        specialist_fingerprint=b"b" * 32,
        stream_bytes=4096,
        probe_bytes=256,
        min_stream_bytes=1024,
    )
    fp = cost_aware_router_fingerprint(**base)
    assert len(fp) == 32
    assert fp != cost_aware_router_fingerprint(**{**base, "stream_bytes": 8192})
    assert fp != cost_aware_router_fingerprint(**{**base, "probe_bytes": 128})
    assert fp != cost_aware_router_fingerprint(**{**base, "min_stream_bytes": 2048})


def test_router_roundtrip_is_independent_between_encoder_and_decoder():
    data = (b"POLLICINO" * 50) + bytes(range(64))

    def factory():
        return CostAwareSpecialistRouterCDFProvider(
            _BiasedProvider(ord("P"), weight=32),
            _BiasedProvider(ord("O"), weight=48),
            stream_bytes=len(data),
            probe_bytes=48,
            min_stream_bytes=64,
        )

    encoder, decoder, _bits = _roundtrip(data, factory, b"z" * 32)
    assert encoder.selected_route in {"cheap", "specialist"}
    assert decoder.selected_route == encoder.selected_route
