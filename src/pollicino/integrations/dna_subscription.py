from __future__ import annotations

from dataclasses import dataclass

from pollicino.bearer_transport import BearerTransferReport, NodeBearerTransport
from pollicino.net.bundle import ForwardBundle
from pollicino.net.store import ChunkManifest
from pollicino.node_runtime import PollicinoNodeRuntime

from .dna import (
    DNAIntegrationError,
    DOMAIN_CODES,
    DNATraceV01,
    dna_trace_from_canonical_json,
    dna_trace_to_descriptor,
)


@dataclass(frozen=True, slots=True)
class DNATopicDecision:
    """Result of one local DNA topic/subscription decision.

    DNA v0.1 does not currently define a durable Topic/Subscription schema.
    This experimental Pollicino integration therefore filters only fields that
    are already canonical in ``DNATraceV01``: ``domains`` and ``intent_codes``.
    """

    accepted: bool
    matched_domains: tuple[str, ...]
    matched_intent_codes: tuple[int, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class DNATopicSubscription:
    """Minimal application-layer subscription over canonical DNA trace fields.

    Within each non-empty selector, any overlap matches. When both domain and
    intent selectors are non-empty, both selector classes must match. An empty
    selector is a wildcard for that class; an entirely empty subscription
    therefore accepts every valid DNA trace.

    This is intentionally not a new DNA wire contract. It is a Pollicino-side
    product experiment that can later be replaced by an authoritative DNA
    Topic/Subscription contract without changing the network core.
    """

    domains: tuple[str, ...] = ()
    intent_codes: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.domains, tuple):
            raise TypeError("domains must be a tuple")
        if any(not isinstance(domain, str) or domain not in DOMAIN_CODES for domain in self.domains):
            raise DNAIntegrationError("subscription domains contain an unsupported value")
        if len(set(self.domains)) != len(self.domains):
            raise DNAIntegrationError("subscription domains must be unique")

        if not isinstance(self.intent_codes, tuple):
            raise TypeError("intent_codes must be a tuple")
        if any(not isinstance(code, int) or not 0 <= code <= 0xFFFF for code in self.intent_codes):
            raise DNAIntegrationError(
                "subscription intent_codes must contain unsigned 16-bit integers"
            )
        if len(set(self.intent_codes)) != len(self.intent_codes):
            raise DNAIntegrationError("subscription intent_codes must be unique")

        object.__setattr__(
            self,
            "domains",
            tuple(sorted(self.domains, key=DOMAIN_CODES.__getitem__)),
        )
        object.__setattr__(self, "intent_codes", tuple(sorted(self.intent_codes)))

    def evaluate(self, trace: DNATraceV01) -> DNATopicDecision:
        if not isinstance(trace, DNATraceV01):
            raise TypeError("trace must be DNATraceV01")

        domain_set = set(self.domains)
        intent_set = set(self.intent_codes)
        matched_domains = tuple(domain for domain in trace.domains if domain in domain_set)
        matched_intents = tuple(code for code in trace.intent_codes if code in intent_set)

        domain_ok = not self.domains or bool(matched_domains)
        intent_ok = not self.intent_codes or bool(matched_intents)
        accepted = domain_ok and intent_ok

        if not domain_ok:
            reason = "domain_miss"
        elif not intent_ok:
            reason = "intent_miss"
        elif not self.domains and not self.intent_codes:
            reason = "wildcard"
        else:
            reason = "matched"

        return DNATopicDecision(
            accepted=accepted,
            matched_domains=matched_domains,
            matched_intent_codes=matched_intents,
            reason=reason,
        )

    def matches(self, trace: DNATraceV01) -> bool:
        return self.evaluate(trace).accepted


@dataclass(frozen=True, slots=True)
class DNAGovernedPublication:
    decision: DNATopicDecision
    manifest: ChunkManifest | None = None
    bundle: ForwardBundle | None = None

    def __post_init__(self) -> None:
        if (self.manifest is None) != (self.bundle is None):
            raise ValueError("manifest and bundle must either both be present or both be absent")

    @property
    def published(self) -> bool:
        return self.manifest is not None


def publish_governed_trace_if_subscribed(
    node: PollicinoNodeRuntime,
    trace: DNATraceV01,
    subscription: DNATopicSubscription,
    *,
    coordinate: bytes,
    chunk_size: int,
    created_at_s: int,
    label: str = "dna-trace",
    prefer_inline: bool = True,
    radio_authenticator: bytes | None = None,
    hop_limit: int = 0,
) -> DNAGovernedPublication:
    """Publish a canonical DNA trace only when local topic policy accepts it.

    Rejection occurs before PCM1/PNB1/PNC1 state is created, so a denied trace
    cannot consume governed-object state accidentally.
    """

    if not isinstance(node, PollicinoNodeRuntime):
        raise TypeError("node must be PollicinoNodeRuntime")
    if not isinstance(subscription, DNATopicSubscription):
        raise TypeError("subscription must be DNATopicSubscription")

    decision = subscription.evaluate(trace)
    if not decision.accepted:
        return DNAGovernedPublication(decision=decision)

    descriptor = dna_trace_to_descriptor(
        trace,
        coordinate=coordinate,
        prefer_inline=prefer_inline,
        radio_authenticator=radio_authenticator,
        hop_limit=hop_limit,
    )
    manifest, bundle = node.publish_governed(
        trace.canonical_json(),
        chunk_size=chunk_size,
        descriptor=descriptor,
        created_at_s=created_at_s,
        label=label,
    )
    return DNAGovernedPublication(
        decision=decision,
        manifest=manifest,
        bundle=bundle,
    )


@dataclass(frozen=True, slots=True)
class DNAGovernedForward:
    decision: DNATopicDecision
    transfer: BearerTransferReport | None = None

    @property
    def forwarded(self) -> bool:
        return self.transfer is not None


def forward_governed_trace_if_subscribed(
    transport: NodeBearerTransport,
    target: PollicinoNodeRuntime,
    bundle: ForwardBundle,
    manifest: ChunkManifest,
    subscription: DNATopicSubscription,
    *,
    transfer_id_base: int,
    max_chunks: int,
    contact_id: str,
    now_s: int,
) -> DNAGovernedForward:
    """Forward a governed DNA trace only when target-facing policy accepts it.

    The decision is made from the authoritative canonical bytes already stored
    by the source, not from caller-supplied topic metadata. A rejection returns
    before bearer evaluation or transfer, preserving the existing bearer and
    governance layers byte-for-byte for accepted traffic.
    """

    if not isinstance(transport, NodeBearerTransport):
        raise TypeError("transport must be NodeBearerTransport")
    if not isinstance(target, PollicinoNodeRuntime):
        raise TypeError("target must be PollicinoNodeRuntime")
    if not isinstance(bundle, ForwardBundle):
        raise TypeError("bundle must be ForwardBundle")
    if not isinstance(manifest, ChunkManifest):
        raise TypeError("manifest must be ChunkManifest")
    if not isinstance(subscription, DNATopicSubscription):
        raise TypeError("subscription must be DNATopicSubscription")
    if bundle.manifest_fingerprint != manifest.fingerprint:
        raise ValueError("bundle and manifest identities do not match")

    source = transport.source
    if not source.knows_manifest(manifest.fingerprint):
        raise ValueError("source runtime does not know the DNA trace manifest")
    if not source.complete(manifest.fingerprint):
        raise ValueError("source runtime does not have the complete DNA trace")

    trace = dna_trace_from_canonical_json(source.reconstruct(manifest.fingerprint))
    decision = subscription.evaluate(trace)
    if not decision.accepted:
        return DNAGovernedForward(decision=decision)

    transfer = transport.send_governed(
        target,
        bundle,
        manifest,
        transfer_id_base=transfer_id_base,
        max_chunks=max_chunks,
        contact_id=contact_id,
        now_s=now_s,
    )
    return DNAGovernedForward(decision=decision, transfer=transfer)
