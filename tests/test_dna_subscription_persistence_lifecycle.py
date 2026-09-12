from __future__ import annotations

from dataclasses import dataclass

from pollicino.bearer_runtime import BearerObservation, NodeBearerController
from pollicino.bearer_transport import DeterministicGovernedBearerAdapter, NodeBearerTransport
from pollicino.integrations.dna import DNATraceV01, dna_trace_from_canonical_json
from pollicino.integrations.dna_subscription import (
    DNATopicSubscription,
    forward_governed_trace_if_subscribed,
    publish_governed_trace_if_subscribed,
)
from pollicino.integrations.dna_subscription_store import DNASubscriptionRegistry
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
    domain: str,
    intents: tuple[int, ...],
    nonce: int,
) -> DNATraceV01:
    return DNATraceV01(
        trace_id=trace_id,
        ephemeral_sender_id="student-ephemeral-002",
        domains=(domain,),
        intent_codes=intents,
        rendezvous_capabilities=("lora",),
        issued_at="2026-08-30T06:00:00Z",
        expires_at="2026-08-30T08:00:00Z",
        nonce=nonce,
        authenticator=b"dna-lifecycle-test",
        coarse_geo_cell="school-cell",
    )


def _mesh_snapshot() -> LoRaMesherRuntimeSnapshot:
    return LoRaMesherRuntimeSnapshot(
        running=True,
        current_state="NORMAL_OPERATION",
        connected_nodes=1,
        is_synchronized=True,
        ready_to_send=True,
        time_since_last_sync_ms=4,
    )


def _school_profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        data_loss_ppm=0,
        ack_loss_ppm=0,
        max_retries=0,
        ack_bytes=0,
        seed=410,
    )


def _territory_profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=3500,
        data_loss_ppm=0,
        ack_loss_ppm=0,
        max_retries=1,
        ack_bytes=8,
        seed=411,
    )


@dataclass(frozen=True, slots=True)
class _ReadyTerritoryProbe:
    adapter_id: str = "territory-model"
    mode: NodeMode = NodeMode.OPPORTUNISTIC_DTN

    def probe(self) -> BearerObservation:
        return BearerObservation(
            adapter_id=self.adapter_id,
            mode=self.mode,
            available=True,
            ready=True,
            detail="deterministic off-grid lifecycle test",
        )


def test_active_subscription_survives_registry_restart(tmp_path) -> None:
    root = tmp_path / "student-app"
    registry = DNASubscriptionRegistry(root, node_id="student-b")
    subscription = DNATopicSubscription(domains=("social",), intent_codes=(700, 701))
    registry.upsert("school-social", subscription)
    registry.select("school-social")

    restarted = DNASubscriptionRegistry(root, node_id="student-b")
    assert restarted.subscription_ids == ("school-social",)
    assert restarted.active_id == "school-social"
    assert restarted.require_active() == subscription


def test_school_subscription_carry_restart_and_home_forwarding(tmp_path) -> None:
    school = PollicinoNodeRuntime(tmp_path / "school", node_id="student-a")
    mule = PollicinoNodeRuntime(tmp_path / "mule", node_id="student-b")
    home = PollicinoNodeRuntime(tmp_path / "home", node_id="home-gateway")
    mule.transition(NodeMode.CONNECTED_MESH)
    home.transition(NodeMode.OPPORTUNISTIC_DTN)

    mule_subscriptions = DNASubscriptionRegistry(mule.root, node_id=mule.node_id)
    mule_subscriptions.upsert(
        "school-social",
        DNATopicSubscription(domains=("social",), intent_codes=(700,)),
    )
    mule_subscriptions.select("school-social")

    bus = InMemoryLoRaMesherBus()
    school_port = bus.attach(0x3001)
    mule_port = bus.attach(0x3002)
    mule_receiver = LoRaMesherPnf1Receiver(mule_port)
    school_controller = NodeBearerController(
        school,
        (LoRaMesherBearerProbe(_mesh_snapshot),),
    )
    school_adapter = LoRaMesherGovernedBearerAdapter(
        school_port,
        profile=_school_profile(),
        target_addresses={"student-b": 0x3002},
        receivers={0x3002: mule_receiver},
    )
    school_transport = NodeBearerTransport(
        school,
        school_controller,
        {"loramesher": school_adapter},
    )

    wildcard = DNATopicSubscription()
    social = _trace(
        trace_id="social-homework-share",
        domain="social",
        intents=(700,),
        nonce=30,
    )
    travel = _trace(
        trace_id="travel-bus-update",
        domain="travel",
        intents=(17,),
        nonce=31,
    )
    social_publication = publish_governed_trace_if_subscribed(
        school,
        social,
        wildcard,
        coordinate=b"dna/social/homework",
        chunk_size=48,
        created_at_s=1000,
        hop_limit=4,
    )
    travel_publication = publish_governed_trace_if_subscribed(
        school,
        travel,
        wildcard,
        coordinate=b"dna/travel/bus",
        chunk_size=48,
        created_at_s=1000,
        hop_limit=4,
    )
    assert social_publication.manifest is not None
    assert social_publication.bundle is not None
    assert travel_publication.manifest is not None
    assert travel_publication.bundle is not None

    active_school_subscription = mule_subscriptions.require_active()
    rejected = forward_governed_trace_if_subscribed(
        school_transport,
        mule,
        travel_publication.bundle,
        travel_publication.manifest,
        active_school_subscription,
        transfer_id_base=18000,
        max_chunks=64,
        contact_id="school-travel-rejected",
        now_s=1010,
    )
    accepted = forward_governed_trace_if_subscribed(
        school_transport,
        mule,
        social_publication.bundle,
        social_publication.manifest,
        active_school_subscription,
        transfer_id_base=19000,
        max_chunks=64,
        contact_id="school-social-accepted",
        now_s=1010,
    )
    assert not rejected.forwarded
    assert accepted.forwarded
    assert accepted.transfer is not None
    assert accepted.transfer.adapter_id == "loramesher"
    assert mule.complete(social_publication.manifest.fingerprint)
    assert not mule.knows_manifest(travel_publication.manifest.fingerprint)

    school_custody = mule.custody_record(social_publication.bundle.bundle_id)
    assert school_custody is not None
    assert school_custody.hop_count == 1
    assert school_custody.complete

    mule.transition(NodeMode.OPPORTUNISTIC_DTN)
    restarted_mule = PollicinoNodeRuntime(mule.root, node_id="student-b")
    restarted_subscriptions = DNASubscriptionRegistry(
        restarted_mule.root,
        node_id=restarted_mule.node_id,
    )
    assert restarted_mule.mode is NodeMode.OPPORTUNISTIC_DTN
    assert restarted_subscriptions.active_id == "school-social"
    assert restarted_subscriptions.require_active() == active_school_subscription
    assert restarted_mule.complete(social_publication.manifest.fingerprint)
    assert not restarted_mule.knows_manifest(travel_publication.manifest.fingerprint)

    territory_controller = NodeBearerController(
        restarted_mule,
        (_ReadyTerritoryProbe(),),
    )
    territory_adapter = DeterministicGovernedBearerAdapter(
        adapter_id="territory-model",
        mode=NodeMode.OPPORTUNISTIC_DTN,
        profile=_territory_profile(),
    )
    territory_transport = NodeBearerTransport(
        restarted_mule,
        territory_controller,
        {"territory-model": territory_adapter},
    )

    persisted_bundle = restarted_mule.bundle(social_publication.bundle.bundle_id)
    home_subscription = DNATopicSubscription(domains=("social",), intent_codes=(700,))
    home_result = forward_governed_trace_if_subscribed(
        territory_transport,
        home,
        persisted_bundle,
        restarted_mule.manifest(social_publication.manifest.fingerprint),
        home_subscription,
        transfer_id_base=20000,
        max_chunks=64,
        contact_id="territory-social-home",
        now_s=1020,
    )
    assert home_result.forwarded
    assert home_result.transfer is not None
    assert home_result.transfer.adapter_id == "territory-model"
    assert home_result.transfer.exact

    home_custody = home.custody_record(social_publication.bundle.bundle_id)
    assert home_custody is not None
    assert home_custody.hop_count == 2
    assert home_custody.complete
    assert home.complete(social_publication.manifest.fingerprint)
    assert not home.knows_manifest(travel_publication.manifest.fingerprint)

    home.transition(NodeMode.RICH_HOME)
    recovered = dna_trace_from_canonical_json(
        home.reconstruct(social_publication.manifest.fingerprint)
    )
    assert recovered == social
