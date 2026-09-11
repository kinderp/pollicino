from __future__ import annotations

import random

import pytest

from pollicino.net.compact_reconciliation import (
    CompactDecodeStatus,
    CompactIndependentEndpoint,
    FingerprintRequestMessage,
    IdentityRevealMessage,
    build_summary,
    decode_compact_message,
    decode_difference,
)
from pollicino.net.endpoint import RecordKind
from px10_support import memory_endpoint, query


def _ids(values) -> tuple[bytes, ...]:
    return tuple(int(value).to_bytes(4, "big") for value in values)


def _candidate_ids(source_values, receiver_values, capacity: int) -> tuple[bytes, ...] | None:
    source = memory_endpoint("source")
    receiver = memory_endpoint("receiver")
    source.query_results.add_queries(query(value) for value in source_values)
    receiver.query_results.add_queries(query(value) for value in receiver_values)
    source_endpoint = CompactIndependentEndpoint(source.catalog, source.query_results)
    receiver_endpoint = CompactIndependentEndpoint(receiver.catalog, receiver.query_results)
    result = receiver_endpoint.receive_summary(
        source_endpoint.summary_message(RecordKind.QUERY, capacity)
    )
    assert result.difference is not None
    if not result.difference.decode_success:
        return None
    if result.difference.status is CompactDecodeStatus.EQUAL:
        return ()
    request = decode_compact_message(result.outbound_messages[0])
    assert isinstance(request, FingerprintRequestMessage)
    reveals = source_endpoint.receive_fingerprint_request(result.outbound_messages[0])
    identities: list[bytes] = []
    for encoded in reveals.outbound_messages:
        message = decode_compact_message(encoded)
        assert isinstance(message, IdentityRevealMessage)
        identities.extend(entry.identity for entry in message.entries)
    return tuple(sorted(identities))


@pytest.mark.parametrize(
    ("size", "missing"),
    ((100, 1), (100, 10), (1_000, 1), (1_000, 10), (1_000, 100),
     (10_000, 1), (10_000, 10), (10_000, 100), (10_000, 1_000)),
)
def test_compact_discovery_matches_exact_oracle_for_high_overlap(size: int, missing: int) -> None:
    source = tuple(range(size))
    receiver = tuple(range(size - missing))
    candidate = _candidate_ids(source, receiver, missing)
    assert candidate == _ids(range(size - missing, size))


@pytest.mark.parametrize("topology", ("prefix", "suffix", "alternating", "sparse", "block"))
def test_difference_topologies_match_exact_oracle(topology: str) -> None:
    source = set(range(1_000))
    if topology == "prefix":
        missing = set(range(100))
    elif topology == "suffix":
        missing = set(range(900, 1_000))
    elif topology == "alternating":
        missing = set(range(0, 200, 2))
    elif topology == "sparse":
        missing = {0, 9, 99, 499, 999}
    else:
        missing = set(range(450, 550))
    receiver = source - missing
    assert _candidate_ids(sorted(source), sorted(receiver), max(1, len(missing))) == _ids(sorted(missing))


def test_seeded_randomized_differential_pairs_match_exact_oracle() -> None:
    for seed in range(64):
        generator = random.Random(seed)
        size = generator.choice((100, 1_000))
        missing_count = generator.choice((1, 10, 32, 100))
        missing_count = min(missing_count, size)
        source = tuple(range(size))
        missing = set(generator.sample(source, missing_count))
        receiver = tuple(value for value in source if value not in missing)
        assert _candidate_ids(source, receiver, missing_count) == _ids(sorted(missing))


def test_symmetric_difference_matches_exact_oracle_in_both_directions() -> None:
    left = tuple(range(1_000))
    right = tuple(range(50, 1_050))
    assert _candidate_ids(left, right, 100) == _ids(range(50))
    assert _candidate_ids(right, left, 100) == _ids(range(1_000, 1_050))


def test_full_set_digest_detects_equal_cardinality_non_equal_sets() -> None:
    summary = build_summary(RecordKind.QUERY, _ids(range(100)), 10)
    result = decode_difference(summary, _ids(range(1, 101)))
    assert result.status is CompactDecodeStatus.DECODED
    assert len(result.source_only_fingerprints) == 1
    assert len(result.receiver_only_fingerprints) == 1

