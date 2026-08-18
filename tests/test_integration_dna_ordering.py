from pollicino.integrations.dna import (
    DNA_FLAG_REFERENCE,
    DNATraceV01,
    dna_trace_to_descriptor,
    is_dna_reference_descriptor,
)


def test_noncanonical_domain_order_uses_reference_to_preserve_array_order() -> None:
    trace = DNATraceV01(
        trace_id="trace-order-domain",
        ephemeral_sender_id="ephem003",
        domains=("social", "travel"),
        intent_codes=(17,),
        rendezvous_capabilities=("internet", "lora"),
        issued_at="2026-08-18T20:00:00Z",
        expires_at="2026-08-18T20:15:00Z",
        nonce=44,
        authenticator=b"order-auth",
    )

    descriptor = dna_trace_to_descriptor(trace, coordinate=b"domain-order")

    assert descriptor.flags == DNA_FLAG_REFERENCE
    assert is_dna_reference_descriptor(descriptor)


def test_noncanonical_capability_order_uses_reference_to_preserve_array_order() -> None:
    trace = DNATraceV01(
        trace_id="trace-order-cap",
        ephemeral_sender_id="ephem004",
        domains=("travel",),
        intent_codes=(17,),
        rendezvous_capabilities=("lora", "internet"),
        issued_at="2026-08-18T20:00:00Z",
        expires_at="2026-08-18T20:15:00Z",
        nonce=45,
        authenticator=b"order-auth",
    )

    descriptor = dna_trace_to_descriptor(trace, coordinate=b"cap-order")

    assert descriptor.flags == DNA_FLAG_REFERENCE
    assert is_dna_reference_descriptor(descriptor)
