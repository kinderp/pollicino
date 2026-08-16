from __future__ import annotations

from pollicino.compression.adaptive import AdaptiveNGramCDFProvider, adaptive_fingerprint
from pollicino.compression.classical_experts import RunLengthCDFProvider, run_length_fingerprint
from pollicino.compression.gating import DeterministicExpertGateCDFProvider, expert_gate_fingerprint
from pollicino.compression.range_coder import decode_symbols, encode_symbols


NAMES = ("adaptive-o0", "adaptive-o1", "adaptive-o2", "adaptive-o3", "run")


def _factory(window: int = 64):
    return DeterministicExpertGateCDFProvider(
        [
            AdaptiveNGramCDFProvider(max_order=0, order_weights=(1,)),
            AdaptiveNGramCDFProvider(max_order=1, order_weights=(1, 4)),
            AdaptiveNGramCDFProvider(max_order=2, order_weights=(1, 4, 16)),
            AdaptiveNGramCDFProvider(max_order=3, order_weights=(1, 4, 16, 64)),
            RunLengthCDFProvider(run_weight=64),
        ],
        names=NAMES,
        window=window,
    )


def _fingerprint(window: int = 64):
    return expert_gate_fingerprint(
        expert_fingerprints=[
            adaptive_fingerprint(max_order=0, order_weights=(1,)),
            adaptive_fingerprint(max_order=1, order_weights=(1, 4)),
            adaptive_fingerprint(max_order=2, order_weights=(1, 4, 16)),
            adaptive_fingerprint(max_order=3, order_weights=(1, 4, 16, 64)),
            run_length_fingerprint(run_weight=64),
        ],
        names=NAMES,
        window=window,
    )


def _roundtrip(data: bytes, window: int = 64):
    enc = _factory(window)
    prefix: list[int] = []
    cdfs = []
    for i, symbol in enumerate(data):
        cdfs.append(enc(i, prefix))
        prefix.append(symbol)
    payload, bits = encode_symbols(data, cdfs)
    dec = _factory(window)
    restored = bytes(decode_symbols(payload, len(data), dec))
    assert restored == data
    assert enc.choice_counts == dec.choice_counts
    return bits, enc.choice_fractions()


def test_cheap_gate_roundtrip_mixed_data():
    data = (b"ABRACADABRA\n" * 50) + bytes(range(256)) + (b"Z" * 400)
    bits, fractions = _roundtrip(data)
    assert bits > 0
    assert abs(sum(fractions.values()) - 1.0) < 1e-12


def test_cheap_gate_uses_run_expert_on_long_repetition():
    bits, fractions = _roundtrip(b"A" * 2000)
    assert bits / 2000 < 0.2
    assert fractions["run"] > 0.5


def test_cheap_gate_fingerprint_changes_with_window():
    assert _fingerprint(64) != _fingerprint(256)
