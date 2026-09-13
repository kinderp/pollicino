from __future__ import annotations

import random
import zlib
from dataclasses import replace

from pollicino.compression.admission_routing import (
    AdmissionBudgetState,
    CheapAdmissionDecisionTree,
    DecisionTreeNode,
    QuantizedLinearAdmissionRule,
    RichCheapAdmissionBlockCDFProvider,
    extract_cheap_admission_features,
    rich_cheap_admission_decision,
    rich_cheap_admission_fingerprint,
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
        frequencies = [1] * 256
        frequencies[self.preferred] = self.weight
        return frequencies_to_cdf(frequencies)


def _feature_rule(feature: str, weight: int, threshold: int):
    return QuantizedLinearAdmissionRule((feature,), (weight,), bias=0, threshold=threshold)


def test_exact_rich_feature_definitions_on_uniform_probe():
    features = extract_cheap_admission_features(_UniformProvider, b"AAAABBCD")
    assert features.probe_code_bits_floor == 64
    assert features.probe_code_bits_ceil == 64
    assert features.unique_count == 4
    assert features.max_hist_count == 4
    assert features.transition_count == 3
    assert features.distinct_transition_count == 5
    assert features.longest_run == 4
    assert features.surprise_sum_ceil == 64
    assert features.surprise_max_ceil == 8
    assert features.surprise_range_ceil == 0
    assert features.surprise_variance_proxy == 0
    assert features.surprise_early_minus_late == 0
    assert features.very_surprising_count == 0


def test_quantized_linear_score_boundaries_are_exact():
    features = extract_cheap_admission_features(_UniformProvider, b"ABCD")
    rule = _feature_rule("unique_count", 3, threshold=12)
    budget = AdmissionBudgetState(0, 8)
    assert rich_cheap_admission_decision(
        replace(features, unique_count=3), rule, budget, 8
    ).score == 9
    at = rich_cheap_admission_decision(features, rule, budget, 8)
    assert at.score == at.threshold == 12
    assert at.admitted
    assert rich_cheap_admission_decision(
        replace(features, unique_count=5), rule, budget, 8
    ).score == 15


def test_tree_checks_both_sides_of_every_boundary():
    tree = CheapAdmissionDecisionTree(
        (
            DecisionTreeNode("unique_count", 2, 1, 2),
            DecisionTreeNode(value=-1),
            DecisionTreeNode("longest_run", 2, 3, 4),
            DecisionTreeNode(value=3),
            DecisionTreeNode(value=1),
        ),
        threshold=1,
    )
    features = extract_cheap_admission_features(_UniformProvider, b"ABCD")
    assert tree.score(replace(features, unique_count=2)) == -1
    assert tree.score(replace(features, unique_count=3, longest_run=2)) == 3
    assert tree.score(replace(features, unique_count=3, longest_run=3)) == 1


def test_rich_admission_roundtrip_routes_and_budget_are_identical():
    data = b"A" * 24
    rule = _feature_rule("unique_count", 1, threshold=1)

    def factory(max_bytes=16):
        return RichCheapAdmissionBlockCDFProvider(
            _UniformProvider,
            lambda: _BiasedProvider(ord("A")),
            rule,
            stream_bytes=len(data),
            block_bytes=8,
            probe_bytes=4,
            max_admitted_bytes=max_bytes,
            cheap_name="cheap",
            specialist_name="neural",
        )

    fingerprint = rich_cheap_admission_fingerprint(
        cheap_fingerprint=b"c" * 32,
        specialist_fingerprint=b"n" * 32,
        stream_bytes=len(data),
        block_bytes=8,
        probe_bytes=4,
        rule=rule,
        max_admitted_bytes=16,
    )
    encoder = factory()
    blob = encode_shared(data, encoder, fingerprint, precision_bits=18)
    decoder = factory()
    restored = decode_pol(blob, shared_provider=decoder, expected_model_fingerprint=fingerprint)
    assert restored == data
    assert encoder.block_summary() == decoder.block_summary()
    assert [row["admitted"] for row in encoder.block_summary()] == [True, True, False]
    assert encoder.admitted_bytes == 16


def test_one_block_beyond_budget_is_denied():
    data = b"A" * 24
    rule = _feature_rule("unique_count", 1, threshold=1)
    router = RichCheapAdmissionBlockCDFProvider(
        _UniformProvider,
        lambda: _BiasedProvider(ord("A")),
        rule,
        stream_bytes=len(data),
        block_bytes=8,
        probe_bytes=4,
        max_admitted_bytes=15,
    )
    prefix = []
    for index, symbol in enumerate(data):
        router(index, prefix)
        prefix.append(symbol)
    assert [row["admitted"] for row in router.block_summary()] == [True, False, False]
    assert [row["budget_limited"] for row in router.block_summary()] == [False, True, True]


def test_specialist_is_never_created_before_probe_decision():
    created = 0

    def specialist_factory():
        nonlocal created
        created += 1
        return _BiasedProvider(ord("A"))

    router = RichCheapAdmissionBlockCDFProvider(
        _UniformProvider,
        specialist_factory,
        _feature_rule("unique_count", 1, threshold=1),
        stream_bytes=8,
        block_bytes=8,
        probe_bytes=4,
    )
    prefix = []
    for index in range(4):
        router(index, prefix)
        prefix.append(ord("A"))
        assert created == 0
    router(4, prefix)
    assert created == 1


def test_future_tail_cannot_change_route_and_single_probe_byte_can():
    rule = _feature_rule("unique_count", 1, threshold=2)

    def route(data):
        router = RichCheapAdmissionBlockCDFProvider(
            _UniformProvider,
            lambda: _BiasedProvider(ord("A")),
            rule,
            stream_bytes=len(data),
            block_bytes=len(data),
            probe_bytes=4,
        )
        prefix = []
        for index, symbol in enumerate(data):
            router(index, prefix)
            prefix.append(symbol)
        return router.block_summary()[0]["route"]

    assert route(b"AAAA" + b"B" * 8) == route(b"AAAA" + b"CDEFGHIJ") == "cheap"
    assert route(b"AAAB" + b"B" * 8) == "specialist"


def test_random_compressed_and_restart_routes_are_deterministic():
    generator = random.Random(14014)
    random_data = bytes(generator.randrange(256) for _ in range(64))
    compressed = zlib.compress(bytes(range(256)) * 4, 9)
    rule = QuantizedLinearAdmissionRule(
        ("unique_count", "transition_count", "surprise_max_ceil"),
        (7, -2, 3),
        bias=-20,
        threshold=0,
    )
    for data in (b"\0" * 64, random_data, compressed[:64]):
        first = rich_cheap_admission_decision(
            extract_cheap_admission_features(_UniformProvider, data[:16]),
            rule,
            AdmissionBudgetState(0, 32),
            32,
        )
        second = rich_cheap_admission_decision(
            extract_cheap_admission_features(_UniformProvider, data[:16]),
            rule,
            AdmissionBudgetState(0, 32),
            32,
        )
        assert first == second


def test_fingerprint_commits_to_feature_rule_and_budget():
    base = dict(
        cheap_fingerprint=b"c" * 32,
        specialist_fingerprint=b"n" * 32,
        stream_bytes=4096,
        block_bytes=512,
        probe_bytes=16,
        rule=QuantizedLinearAdmissionRule(("unique_count",), (2,), -3, 7),
        max_admitted_bytes=2048,
    )
    fingerprint = rich_cheap_admission_fingerprint(**base)
    assert len(fingerprint) == 32
    assert fingerprint != rich_cheap_admission_fingerprint(
        **{**base, "rule": QuantizedLinearAdmissionRule(("unique_count",), (3,), -3, 7)}
    )
    assert fingerprint != rich_cheap_admission_fingerprint(
        **{**base, "max_admitted_bytes": 1536}
    )
