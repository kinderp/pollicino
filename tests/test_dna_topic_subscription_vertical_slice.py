from __future__ import annotations

import pytest

from pollicino.bearer_runtime import NodeBearerController
from pollicino.bearer_transport import NodeBearerTransport
from pollicino.integrations.dna import DNAIntegrationError, DNATraceV01, dna_trace_from_canonical_json
from pollicino.integrations.dna_subscription import (
    DNATopicSubscription,
    forward_governed_trace_if_subscribed,
    publish_governed_trace_if_subscribed,
)
from pollicino.integrations.loramesher_pnf1 import (
    LoRaMesherGovernedBearerAdapter,
    LoRaMesherPnf1Receiver,
)
from pollicino.integrations.loramesher_runtime import (
    LoRaMesherBearerProbe,
    LoRaMesherRuntimeSnapshot,
)
from pollicino.integrations.loramesher_transport import InMemoryLoRaMesherBus
from pollicino.net import ScarceLinkProfile
from pollicino.node_runtime import NodeMode, PollicinoNodeRuntime


def _trace(
    *,
    trace_id: str,
    domains: tuple[str, ...],
    intents: tuple[int, ...],
    nonce: int,
) -> DNATraceV01:
    return DNATraceV01(
        trace_id=trace_id,
        ephemeral_sender_id="student-ephemeral-001",
        domains=domains,
        intent_codes=intents,
        rendezvous_capabilities=("lora",),
        issued_at="2026-08-30T06:00:00Z",
        expires_at="2026-08-30T07:00:00Z",
        nonce=nonce,
        authenticator=b"dna-topic-test",
        coarse_geo_cell="school-cell",
    )


def _mesh_snapshot() -> LoRaMesherRuntimeSnapshot:
    return LoRaMesherRuntimeSnapshot(
        running=True,
        current_state="NORMAL_OPERATION",
        connected_nodes=1,
        is_synchronized=True,
        ready_to_send=True,
        time_since_last_sync_ms=5,
    )


def _mesh_profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        data_loss_ppm=0,
        ack_loss_ppm=0,
        max_retries=0,
        ack_bytes=0,
        seed=401,
    )


def test_subscription_uses_only_canonical_dna_domains_and_intents() -> None:
    social = _trace(
        trace_id="social-lesson-share",
        domains=("social",),
        intents=(700, 701),
        nonce=1,
    )
    travel = _trace(
        trace_id="travel-bus-share",
        domains=("travel",),
        intents=(17,),
        nonce=2,
    )

    subscription = DNATopicSubscription(domains=("social",), intent_codes=(700,))
    decision = subscription.evaluate(social)
    assert decision.accepted
    assert decision.matched_domains == ("social",)
    assert decision.matched_intent_codes == (700,)
    assert decision.reason == "matched"

    assert not subscription.matches(travel)
    assert subscription.evaluate(travel).reason == "domain_miss"
    assert DNATopicSubscription().evaluate(travel).reason == "wildcard"

    with pytest.raises(DNAIntegrationError, match="unsupported"):
        DNATopicSubscription(domains=("not-a-dna-domain",))
    with pytest.raises(DNAIntegrationError, match="unique"):
        DNATopicSubscription(intent_codes=(700, 700))


def test_subscription_rejects_before_governed_publication(tmp_path) -> None:
    node = PollicinoNodeRuntime(tmp_path / "publisher", node_id="student-a")
    social_only = DNATopicSubscription(domains=("social",), intent_codes=(700,))
    travel = _trace(
        trace_id="travel-rejected-before-publish",
        domains=("travel",),
        intents=(17,),
        nonce=10,
    )

    before_objects = node.known_object_count
    before_bundles = node.known_bundle_count
    result = publish_governed_trace_if_subscribed(
        node,
        travel,
        social_only,
        coordinate=b"dna/travel/rejected",
        chunk_size=48,
        created_at_s=1000,
        hop_limit=4,
    )

    assert not result.published
    assert result.decision.reason == "domain_miss"
    assert result.manifest is None
    assert result.bundle is None
    assert node.known_object_count == before_objects
    assert node.known_bundle_count == before_bundles


def test_subscription_filters_before_forward_then_reuses_loramesher_governance(tmp_path) -> None:
    source = PollicinoNodeRuntime(tmp_path / "source", node_id="student-a")
    target = PollicinoNodeRuntime(tmp_path / "target", node_id="student-b")
    target.transition(NodeMode.CONNECTED_MESH)

    bus = InMemoryLoRaMesherBus()
    source_port = bus.attach(0x2001)
    target_port = bus.attach(0x2002)
    receiver = LoRaMesherPnf1Receiver(target_port)
    controller = NodeBearerController(source, (LoRaMesherBearerProbe(_mesh_snapshot),))
    adapter = LoRaMesherGovernedBearerAdapter(
        source_port,
        profile=_mesh_profile(),
        target_addresses={"student-b": 0x2002},
        receivers={0x2002: receiver},
    )
    transport = NodeBearerTransport(source, controller, {"loramesher": adapter})

    wildcard = DNATopicSubscription()
    social_only = DNATopicSubscription(domains=("social",), intent_codes=(700,))

    travel = _trace(
        trace_id="travel-present-at-source",
        domains=("travel",),
        intents=(17,),
        nonce=20,
    )
    travel_publication = publish_governed_trace_if_subscribed(
        source,
        travel,
        wildcard,
        coordinate=b"dna/travel/source",
        chunk_size=48,
        created_at_s=1000,
        hop_limit=4,
    )
    assert travel_publication.published
    assert travel_publication.manifest is not None
    assert travel_publication.bundle is not None

    rejected = forward_governed_trace_if_subscribed(
        transport,
        target,
        travel_publication.bundle,
        travel_publication.manifest,
        social_only,
        transfer_id_base=16000,
        max_chunks=64,
        contact_id="dna-travel-rejected",
        now_s=1010,
    )
    assert not rejected.forwarded
    assert rejected.transfer is None
    assert rejected.decision.reason == "domain_miss"
    assert source.mode is NodeMode.DISCOVERING
    assert not target.knows_manifest(travel_publication.manifest.fingerprint)
    assert target.custody_record(travel_publication.bundle.bundle_id) is None

    social = _trace(
        trace_id="social-school-share",
        domains=("social",),
        intents=(700, 701),
        nonce=21,
    )
    social_publication = publish_governed_trace_if_subscribed(
        source,
        social,
        wildcard,
        coordinate=b"dna/social/source",
        chunk_size=48,
        created_at_s=1000,
        hop_limit=4,
    )
    assert social_publication.published
    assert social_publication.manifest is not None
    assert social_publication.bundle is not None

    accepted = forward_governed_trace_if_subscribed(
        transport,
        target,
        social_publication.bundle,
        social_publication.manifest,
        social_only,
        transfer_id_base=17000,
        max_chunks=64,
        contact_id="dna-social-accepted",
        now_s=1010,
    )
    assert accepted.forwarded
    assert accepted.transfer is not None
    assert accepted.transfer.adapter_id == "loramesher"
    assert accepted.transfer.exact
    assert source.mode is NodeMode.CONNECTED_MESH
    assert target.complete(social_publication.manifest.fingerprint)

    recovered = dna_trace_from_canonical_json(
        target.reconstruct(social_publication.manifest.fingerprint)
    )
    assert recovered == social

    custody = target.custody_record(social_publication.bundle.bundle_id)
    assert custody is not None
    assert custody.hop_count == 1
    assert custody.complete
    assert accepted.transfer.contact.governance.accounting == "loramesher_host_application_bytes"
    assert accepted.transfer.contact.governance.inner is not None
    assert (
        accepted.transfer.contact.governance.inner.accounting
        == "loramesher_host_application_bytes"
    )
    assert accepted.transfer.total_wire_bytes > 0
