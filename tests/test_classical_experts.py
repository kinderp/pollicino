from __future__ import annotations

from pollicino.compression.classical_experts import RunLengthCDFProvider, run_length_fingerprint
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


def test_run_length_roundtrip_repetition_and_binary():
    factory = lambda: RunLengthCDFProvider(run_weight=64)
    assert _roundtrip(b"A" * 500 + b"B" * 300, factory) > 0
    assert _roundtrip(bytes(range(256)) * 2, factory) > 0


def test_run_length_compresses_long_run():
    bits = _roundtrip(b"A" * 2000, lambda: RunLengthCDFProvider(run_weight=64))
    assert bits / 2000 < 0.2


def test_run_length_keeps_every_symbol_possible():
    provider = RunLengthCDFProvider(run_weight=64)
    prefix = [65] * 20
    cdf = provider(len(prefix), prefix)
    frequencies = [b - a for a, b in zip(cdf, cdf[1:])]
    assert len(frequencies) == 256
    assert all(value > 0 for value in frequencies)
    assert frequencies[65] > frequencies[66]


def test_run_length_rejects_divergent_prefix():
    provider = RunLengthCDFProvider()
    provider(2, [65, 65])
    try:
        provider(2, [65, 66])
    except ValueError:
        pass
    else:
        raise AssertionError("divergent prefix must be rejected")


def test_run_length_fingerprint_tracks_configuration():
    a = run_length_fingerprint(run_weight=64)
    b = run_length_fingerprint(run_weight=32)
    assert len(a) == len(b) == 32
    assert a != b
