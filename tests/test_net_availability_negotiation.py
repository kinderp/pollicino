import hashlib
import math

from pollicino.net.availability_negotiation import select_availability_response
from pollicino.net.availability_reconciliation import decode_availability_candidate
from pollicino.net.availability_wire_benchmark import PNA1_BASELINE_ID
from pollicino.net.link import ScarceLinkProfile
from pollicino.net.store import AvailabilitySummary, MAX_CHUNKS
from pollicino.net.wire import DiscoveryDescriptor


RESEARCH_CAPABILITY_BIT = 0x8000


def _profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=181,
    )


def _descriptor(*, supports: bool) -> DiscoveryDescriptor:
    return DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"availability-neg",
        ttl_seconds=1000,
        hop_limit=8,
        nonce=1,
        capability_mask=RESEARCH_CAPABILITY_BIT if supports else 0,
    )


def _summary(available_indices, *, label: str) -> AvailabilitySummary:
    bits = bytearray(math.ceil(MAX_CHUNKS / 8))
    for index in available_indices:
        byte_index, bit_index = divmod(index, 8)
        bits[byte_index] |= 1 << bit_index
    return AvailabilitySummary(
        manifest_fingerprint=hashlib.sha256(label.encode()).digest(),
        chunk_count=MAX_CHUNKS,
        available_bits=bytes(bits),
    )


def test_capability_bit_uses_existing_pnd1_width_without_new_packet_bytes() -> None:
    legacy = _descriptor(supports=False)
    capable = _descriptor(supports=True)

    assert legacy.encoded_size == capable.encoded_size
    assert len(legacy.encode()) == len(capable.encode())
    assert DiscoveryDescriptor.decode(capable.encode()).capability_mask == RESEARCH_CAPABILITY_BIT


def test_legacy_source_forces_pna1_even_if_receiver_supports_alternatives() -> None:
    missing = set(range(100, 140, 2))
    summary = _summary(
        (index for index in range(MAX_CHUNKS) if index not in missing),
        label="legacy-source",
    )
    decision = select_availability_response(
        summary,
        source_descriptor=_descriptor(supports=False),
        receiver_supports_alternative=True,
        capability_bit=RESEARCH_CAPABILITY_BIT,
        profile=_profile(),
    )

    assert decision.uses_pna1
    assert decision.payload == summary.encode()
    assert AvailabilitySummary.decode(decision.payload) == summary


def test_legacy_receiver_forces_pna1_even_with_capable_source() -> None:
    summary = _summary((), label="legacy-receiver")
    decision = select_availability_response(
        summary,
        source_descriptor=_descriptor(supports=True),
        receiver_supports_alternative=False,
        capability_bit=RESEARCH_CAPABILITY_BIT,
        profile=_profile(),
    )

    assert decision.representation_id == PNA1_BASELINE_ID
    assert decision.payload == summary.encode()


def test_two_capable_peers_choose_sparse_alternative_when_it_reduces_wire() -> None:
    missing = set(range(100, 140, 2))
    summary = _summary(
        (index for index in range(MAX_CHUNKS) if index not in missing),
        label="capable-sparse",
    )
    decision = select_availability_response(
        summary,
        source_descriptor=_descriptor(supports=True),
        receiver_supports_alternative=True,
        capability_bit=RESEARCH_CAPABILITY_BIT,
        profile=_profile(),
    )

    assert decision.representation_id == "missing_u16"
    assert len(decision.payload) == 80
    assert decode_availability_candidate(decision.payload) == summary
    assert decision.modeled_wire_bytes < 12_885


def test_two_capable_peers_still_choose_pna1_for_high_entropy_state() -> None:
    bitmap_bytes = math.ceil(MAX_CHUNKS / 8)
    raw = bytearray()
    counter = 0
    while len(raw) < bitmap_bytes:
        raw.extend(hashlib.sha256(counter.to_bytes(4, "big")).digest())
        counter += 1
    raw = raw[:bitmap_bytes]
    raw[-1] &= 0x7F
    summary = AvailabilitySummary(
        manifest_fingerprint=hashlib.sha256(b"negotiation-noisy").digest(),
        chunk_count=MAX_CHUNKS,
        available_bits=bytes(raw),
    )
    decision = select_availability_response(
        summary,
        source_descriptor=_descriptor(supports=True),
        receiver_supports_alternative=True,
        capability_bit=RESEARCH_CAPABILITY_BIT,
        profile=_profile(),
    )

    assert decision.uses_pna1
    assert decision.payload == summary.encode()
