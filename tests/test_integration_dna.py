import base64
import subprocess
import sys

import pytest

from pollicino.integrations.dna import (
    DNAIntegrationError,
    DNA_FLAG_INLINE,
    DNA_FLAG_REFERENCE,
    DNATraceV01,
    dna_trace_from_canonical_json,
    dna_trace_from_inline_descriptor,
    dna_trace_manifest,
    dna_trace_to_descriptor,
    is_dna_reference_descriptor,
)
from pollicino.net import (
    DiscoveryDescriptor,
    InMemoryContentProvider,
    InMemoryResolver,
    retrieve_exact,
)


def compact_trace() -> DNATraceV01:
    return DNATraceV01(
        trace_id="trace-a1b2",
        ephemeral_sender_id="ephem001",
        domains=("travel",),
        intent_codes=(17, 24),
        rendezvous_capabilities=("internet", "lora"),
        issued_at="2026-08-18T20:00:00Z",
        expires_at="2026-08-18T20:15:00Z",
        nonce=41,
        authenticator=b"dna-auth",
        coarse_geo_cell="cell38S",
    )


def large_trace() -> DNATraceV01:
    return DNATraceV01(
        trace_id="trace-" + "a" * 40,
        ephemeral_sender_id="sender-" + "b" * 64,
        domains=("travel", "shopping", "social", "mobility", "local_services"),
        intent_codes=tuple(range(100, 116)),
        rendezvous_capabilities=(
            "internet",
            "ble",
            "nfc",
            "wifi_aware",
            "wifi_direct",
            "lora",
            "qr",
        ),
        issued_at="2026-08-18T20:00:00Z",
        expires_at="2026-08-18T21:00:00Z",
        nonce=42,
        authenticator=b"large-auth",
        coarse_geo_cell="geo-" + "c" * 28,
    )


def test_pollicino_net_core_does_not_import_dna_integration() -> None:
    code = (
        "import sys; import pollicino.net; "
        "assert 'pollicino.integrations.dna' not in sys.modules"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_compact_canonical_trace_round_trips_inline() -> None:
    trace = compact_trace()
    descriptor = dna_trace_to_descriptor(
        trace,
        coordinate=bytes.fromhex("102030405060708090a0b0c0"),
    )

    assert descriptor.flags == DNA_FLAG_INLINE
    wire = descriptor.encode()
    decoded_descriptor = DiscoveryDescriptor.decode(wire)
    decoded_trace = dna_trace_from_inline_descriptor(decoded_descriptor)
    assert decoded_trace == trace


def test_large_trace_uses_reference_and_retrieves_exact_canonical_json() -> None:
    trace = large_trace()
    coordinate = bytes.fromhex("d0c0b0a09080706050403020")
    locator = b"dna/trace/large"
    descriptor = dna_trace_to_descriptor(trace, coordinate=coordinate)

    assert descriptor.flags == DNA_FLAG_REFERENCE
    assert is_dna_reference_descriptor(descriptor)
    with pytest.raises(DNAIntegrationError, match="not an inline"):
        dna_trace_from_inline_descriptor(descriptor)

    resolver = InMemoryResolver()
    provider = InMemoryContentProvider()
    canonical = trace.canonical_json()
    provider.put(locator, canonical)
    resolver.register(
        coordinate,
        dna_trace_manifest(trace, provider_id="memory", locator=locator),
    )

    reconstructed, report = retrieve_exact(
        descriptor,
        resolver=resolver,
        providers={"memory": provider},
    )
    assert reconstructed == canonical
    assert report.exact
    assert dna_trace_from_canonical_json(reconstructed) == trace


def test_noncanonical_timestamp_representation_falls_back_to_reference() -> None:
    trace = DNATraceV01(
        trace_id="trace-time",
        ephemeral_sender_id="ephem002",
        domains=("travel",),
        intent_codes=(1,),
        rendezvous_capabilities=("lora",),
        issued_at="2026-08-18T22:00:00+02:00",
        expires_at="2026-08-18T22:10:00+02:00",
        nonce=43,
        authenticator=b"time-auth",
    )
    descriptor = dna_trace_to_descriptor(trace, coordinate=b"time-coordinate")
    assert descriptor.flags == DNA_FLAG_REFERENCE
    assert is_dna_reference_descriptor(descriptor)


def test_distinct_radio_authenticator_forces_reference() -> None:
    descriptor = dna_trace_to_descriptor(
        compact_trace(),
        coordinate=b"scoped-coordinate",
        radio_authenticator=b"radio-auth",
    )
    assert descriptor.flags == DNA_FLAG_REFERENCE
    assert descriptor.authenticator == b"radio-auth"


def test_mapping_validation_matches_current_dna_contract_shape() -> None:
    trace = compact_trace()
    mapping = trace.to_mapping()
    assert mapping["schemaVersion"] == "0.1"
    assert base64.b64decode(mapping["authenticator"], validate=True) == trace.authenticator
    assert DNATraceV01.from_mapping(mapping) == trace

    bad_domain = dict(mapping)
    bad_domain["domains"] = ["unknown"]
    with pytest.raises(DNAIntegrationError, match="unsupported"):
        DNATraceV01.from_mapping(bad_domain)

    bad_auth = dict(mapping)
    bad_auth["authenticator"] = "***not-base64***"
    with pytest.raises(DNAIntegrationError, match="base64"):
        DNATraceV01.from_mapping(bad_auth)
