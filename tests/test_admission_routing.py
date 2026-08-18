from __future__ import annotations

from pollicino.compression.admission_routing import (
    CheapCodelengthAdmissionBlockCDFProvider,
    cheap_codelength_admission_fingerprint,
)
from pollicino.compression.codec import decode_pol, encode_shared
from pollicino.compression.quantization import frequencies_to_cdf


class _UniformProvider:
    def __call__(self, index, prefix):
        assert index == len(prefix)
        return frequencies_to_cdf([1] * 256)


class _BiasedProvider:
    def __init__(self, preferred: int, weight: int = 4096):
        self.preferred = preferred
        self.weight = weight

    def __call__(self, index, prefix):
        assert index == len(prefix)
        freq = [1] * 256
        freq[self.preferred] = self.weight
        return frequencies_to_cdf(freq)


def test_exact_uniform_probe_band_admits_and_roundtrips():
    data = b"A" * 16
    fp = b"a" * 32

    def factory():
        return CheapCodelengthAdmissionBlockCDFProvider(
            _UniformProvider,
            lambda: _BiasedProvider(ord("A")),
            stream_bytes=len(data),
            block_bytes=8,
            probe_bytes=4,
            min_probe_code_bits=32,
            max_probe_code_bits=32,
            cheap_name="cheap",
            specialist_name="neural",
        )

    enc = factory()
    blob = encode_shared(data, enc, fp, precision_bits=18)
    dec = factory()
    restored = decode_pol(blob, shared_provider=dec, expected_model_fingerprint=fp)
    assert restored == data
    assert enc.block_summary() == dec.block_summary()
    assert enc.admitted_blocks == 2
    assert enc.admission_fraction == 1.0
    assert enc.admitted_byte_fraction == 1.0
    assert {row["route"] for row in enc.block_summary()} == {"neural"}
    assert {row["decision_byte"] for row in enc.block_summary()} == {4}


def test_rejected_blocks_never_construct_specialist():
    data = b"A" * 16
    created = 0

    def specialist_factory():
        nonlocal created
        created += 1
        return _BiasedProvider(ord("A"))

    router = CheapCodelengthAdmissionBlockCDFProvider(
        _UniformProvider,
        specialist_factory,
        stream_bytes=len(data),
        block_bytes=8,
        probe_bytes=4,
        min_probe_code_bits=0,
        max_probe_code_bits=31,
    )
    prefix: list[int] = []
    for index, symbol in enumerate(data):
        router(index, prefix)
        prefix.append(symbol)

    assert created == 0
    assert router.admitted_blocks == 0
    assert router.specialist_output_calls == 0
    assert {row["route"] for row in router.block_summary()} == {"cheap"}


def test_probe_likelihood_is_reset_and_can_change_admission_per_block():
    data = (b"A" * 8) + (b"B" * 8)
    created = 0

    def specialist_factory():
        nonlocal created
        created += 1
        return _BiasedProvider(ord("A"))

    router = CheapCodelengthAdmissionBlockCDFProvider(
        lambda: _BiasedProvider(ord("A")),
        specialist_factory,
        stream_bytes=len(data),
        block_bytes=8,
        probe_bytes=4,
        min_probe_code_bits=0,
        max_probe_code_bits=20,
        cheap_name="cheap",
        specialist_name="neural",
    )
    prefix: list[int] = []
    for index, symbol in enumerate(data):
        router(index, prefix)
        prefix.append(symbol)

    rows = router.block_summary()
    assert [row["admitted"] for row in rows] == [True, False]
    assert [row["route"] for row in rows] == ["neural", "cheap"]
    assert created == 1


def test_admitted_byte_budget_is_a_causal_hard_cap():
    data = b"A" * 24
    created = 0

    def specialist_factory():
        nonlocal created
        created += 1
        return _BiasedProvider(ord("A"))

    router = CheapCodelengthAdmissionBlockCDFProvider(
        _UniformProvider,
        specialist_factory,
        stream_bytes=len(data),
        block_bytes=8,
        probe_bytes=4,
        min_probe_code_bits=32,
        max_probe_code_bits=32,
        max_admitted_bytes=8,
    )
    prefix: list[int] = []
    for index, symbol in enumerate(data):
        router(index, prefix)
        prefix.append(symbol)

    rows = router.block_summary()
    assert [row["band_match"] for row in rows] == [True, True, True]
    assert [row["admitted"] for row in rows] == [True, False, False]
    assert [row["budget_limited"] for row in rows] == [False, True, True]
    assert router.admitted_bytes == 8
    assert router.admitted_byte_fraction == 1 / 3
    assert created == 1


def test_short_last_block_cannot_pay_specialist_probe():
    data = b"A" * 11
    created = 0

    def specialist_factory():
        nonlocal created
        created += 1
        return _BiasedProvider(ord("A"))

    router = CheapCodelengthAdmissionBlockCDFProvider(
        _UniformProvider,
        specialist_factory,
        stream_bytes=len(data),
        block_bytes=8,
        probe_bytes=4,
        min_probe_code_bits=32,
        max_probe_code_bits=32,
    )
    prefix: list[int] = []
    for index, symbol in enumerate(data):
        router(index, prefix)
        prefix.append(symbol)

    rows = router.block_summary()
    assert [row["block_bytes"] for row in rows] == [8, 3]
    assert [row["admitted"] for row in rows] == [True, False]
    assert created == 1


def test_admission_fingerprint_commits_to_probe_band_and_budget():
    base = dict(
        cheap_fingerprint=b"c" * 32,
        specialist_fingerprint=b"n" * 32,
        stream_bytes=4096,
        block_bytes=512,
        probe_bytes=32,
        min_probe_code_bits=96,
        max_probe_code_bits=224,
        max_admitted_bytes=2048,
    )
    fp = cheap_codelength_admission_fingerprint(**base)
    assert len(fp) == 32
    assert fp != cheap_codelength_admission_fingerprint(**{**base, "probe_bytes": 64})
    assert fp != cheap_codelength_admission_fingerprint(**{**base, "max_probe_code_bits": 240})
    assert fp != cheap_codelength_admission_fingerprint(**{**base, "max_admitted_bytes": 1024})
