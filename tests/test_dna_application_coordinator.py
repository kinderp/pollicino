from __future__ import annotations

from dataclasses import dataclass

import pytest

from pollicino.bearer_runtime import BearerObservation, NodeBearerController
from pollicino.bearer_transport import DeterministicGovernedBearerAdapter, NodeBearerTransport
from pollicino.integrations.dna import DNATraceV01, dna_trace_from_canonical_json
from pollicino.integrations.dna_application import DNAApplicationCoordinator
from pollicino.integrations.dna_subscription import DNATopicSubscription
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


def _trace(trace_id: str, *, domain: str, intent: int, nonce: int) -> DNATraceV01:
    return DNATraceV01(
        trace_id=trace_id,
        ephemeral_sender_id="student-ephemeral-003",
        domains=(domain,),
        intent_codes=(intent,),
        rendezvous_capabilities=("lora",),
        issued_at="2026-08-30T08:00:00Z",
        expires_at="2026-08-30T10:00:00Z",
        nonce=nonce,
        authenticator=b"dna-app-coordinator-test",
        coarse_geo_cell="school-cell",
    )


def _registry(
    node: PollicinoNodeRuntime,
    *,
    subscription_id: str,
    subscription: DNATopicSubscription,
) -> DNASubscriptionRegistry:
    registry = DNASubscriptionRegistry(node.root, node_id=node.node_id)
    registry.upsert(subscription_id, subscription)
    registry.select(subscription_id)
    return registry


def _mesh_snapshot() -> LoRaMesherRuntimeSnapshot:
    return LoRaMesherRuntimeSnapshot(
        running=True,
        current_state="NORMAL_OPERATION",
        connected_nodes=1,
        is_synchronized=True,
        ready_to_send=True,
        time_since_last_sync_ms=3,
    )


def _school_profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        data_loss_ppm=0,
        ack_loss_ppm=0,
        max_retries=0,
        ack_bytes=0,
        seed=420,
    )


def _territory_profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=3500,
        data_loss_ppm=0,
        ack_loss_ppm=0,
        max_retries=1,
        ack_bytes=8,
        seed=421,
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
            detail="deterministic off-grid application-coordinator test",
        )


def test_coordinator_fails_closed_without_active_subscription(tmp_path) -> None:
    node = PollicinoNodeRuntime(tmp_path / "node", node_id="student-a")
    registry = DNASubscriptionRegistry(node.root, node_id=node.node_id)
    app = DNAApplicationCoordinator(node, registry)
    trace = _trace("no-active", domain="social", intent=700, nonce=1)

    before_objects = node.known_object_count
    before_bundles = node.known_bundle_count
    with pytest.raises(LookupError, match="no active"):
        app.publish_active(
            trace,
            coordinate=b"dna/no-active",
            chunk_size=48,
            created_at_s=1000,
            hop_limit=4,
        )
    assert node.known_object_count == before_objects
    assert node.known_bundle_count == before_bundles


def test_coordinator_rejects_registry_for_different_node(tmp_path) -> None:
    node = PollicinoNodeRuntime(tmp_path / "node-a", node_id="student-a")
    other_registry = DNASubscriptionRegistry(tmp_path / "other", node_id="student-b")
    with pytest.raises(ValueError, match="different node"):
        DNAApplicationCoordinator(node, other_registry)


def test_coordinator_automates_multi_item_school_carry_home_flow(tmp_path) -> None:
    school = PollicinoNodeRuntime(tmp_path / "school", node_id="student-a")
    mule = PollicinoNodeRuntime(tmp_path / "mule", node_id="student-b")
    home = PollicinoNodeRuntime(tmp_path / "home", node_id="home-gateway")
    mule.transition(NodeMode.CONNECTED_MESH)
    home.transition(NodeMode.OPPORTUNISTIC_DTN)

    school_app = DNAApplicationCoordinator(
        school,
        _registry(
            school,
            subscription_id="publish-all",
            subscription=DNATopicSubscription(),
        ),
    )
    mule_app = DNAApplicationCoordinator(
        mule,
        _registry(
            mule,
            subscription_id="school-social-700",
            subscription=DNATopicSubscription(domains=("social",), intent_codes=(700,)),
        ),
    )
    home_app = DNAApplicationCoordinator(
        home,
        _registry(
            home,
            subscription_id="home-social-700",
            subscription=DNATopicSubscription(domains=("social",), intent_codes=(700,)),
        ),
    )

    bus = InMemoryLoRaMesherBus()
    school_port = bus.attach(0x4001)
    mule_port = bus.attach(0x4002)
    mule_receiver = LoRaMesherPnf1Receiver(mule_port)
    school_controller = NodeBearerController(
        school,
        (LoRaMesherBearerProbe(_mesh_snapshot),),
    )
    school_transport = NodeBearerTransport(
        school,
        school_controller,
        {
            "loramesher": LoRaMesherGovernedBearerAdapter(
                school_port,
                profile=_school_profile(),
                target_addresses={"student-b": 0x4002},
                receivers={0x4002: mule_receiver},
            )
        },
    )

    traces = (
        _trace("social-homework-a", domain="social", intent=700, nonce=10),
        _trace("social-homework-b", domain="social", intent=700, nonce=11),
        _trace("social-other-intent", domain="social", intent=701, nonce=12),
        _trace("travel-bus-update", domain="travel", intent=17, nonce=13),
    )
    publications = []
    for index, trace in enumerate(traces):
        publication = school_app.publish_active(
            trace,
            coordinate=f"dna/coordinator/{index}".encode("ascii"),
            chunk_size=48,
            created_at_s=1000,
            hop_limit=4,
        )
        assert publication.published
        assert publication.manifest is not None
        assert publication.bundle is not None
        publications.append(publication)

    # The first rejected offer must stop before bearer evaluation. The school
    # node therefore remains DISCOVERING until an actually subscribed item is
    # offered to the mule.
    intent_miss = school_app.offer_to(
        mule_app,
        school_transport,
        publications[2].bundle,
        publications[2].manifest,
        transfer_id_base=21000,
        max_chunks=64,
        contact_id="school-social-701-rejected",
        now_s=1010,
    )
    assert not intent_miss.forwarded
    assert intent_miss.decision.reason == "intent_miss"
    assert school.mode is NodeMode.DISCOVERING

    domain_miss = school_app.offer_to(
        mule_app,
        school_transport,
        publications[3].bundle,
        publications[3].manifest,
        transfer_id_base=22000,
        max_chunks=64,
        contact_id="school-travel-rejected",
        now_s=1010,
    )
    assert not domain_miss.forwarded
    assert domain_miss.decision.reason == "domain_miss"
    assert school.mode is NodeMode.DISCOVERING

    accepted_school = []
    for index in (0, 1):
        result = school_app.offer_to(
            mule_app,
            school_transport,
            publications[index].bundle,
            publications[index].manifest,
            transfer_id_base=23000 + index * 1000,
            max_chunks=64,
            contact_id=f"school-social-700-{index}",
            now_s=1010 + index,
        )
        assert result.forwarded
        assert result.transfer is not None
        assert result.transfer.adapter_id == "loramesher"
        assert result.transfer.exact
        accepted_school.append(result)

    assert school.mode is NodeMode.CONNECTED_MESH
    for index in (0, 1):
        manifest = publications[index].manifest
        bundle = publications[index].bundle
        assert mule.complete(manifest.fingerprint)
        custody = mule.custody_record(bundle.bundle_id)
        assert custody is not None
        assert custody.hop_count == 1
        assert custody.complete
    for index in (2, 3):
        assert not mule.knows_manifest(publications[index].manifest.fingerprint)

    # Carry/restart: both network state and the active application subscription
    # survive. Reconstructing the coordinator requires no caller-supplied policy.
    mule.transition(NodeMode.OPPORTUNISTIC_DTN)
    restarted_mule = PollicinoNodeRuntime(mule.root, node_id="student-b")
    restarted_mule_registry = DNASubscriptionRegistry(
        restarted_mule.root,
        node_id=restarted_mule.node_id,
    )
    restarted_mule_app = DNAApplicationCoordinator(
        restarted_mule,
        restarted_mule_registry,
    )
    assert restarted_mule.mode is NodeMode.OPPORTUNISTIC_DTN
    assert restarted_mule_registry.active_id == "school-social-700"

    territory_transport = NodeBearerTransport(
        restarted_mule,
        NodeBearerController(restarted_mule, (_ReadyTerritoryProbe(),)),
        {
            "territory-model": DeterministicGovernedBearerAdapter(
                adapter_id="territory-model",
                mode=NodeMode.OPPORTUNISTIC_DTN,
                profile=_territory_profile(),
            )
        },
    )

    for index in (0, 1):
        original = publications[index]
        persisted_bundle = restarted_mule.bundle(original.bundle.bundle_id)
        persisted_manifest = restarted_mule.manifest(original.manifest.fingerprint)
        result = restarted_mule_app.offer_to(
            home_app,
            territory_transport,
            persisted_bundle,
            persisted_manifest,
            transfer_id_base=25000 + index * 1000,
            max_chunks=64,
            contact_id=f"territory-social-700-{index}",
            now_s=1020 + index,
        )
        assert result.forwarded
        assert result.transfer is not None
        assert result.transfer.adapter_id == "territory-model"
        assert result.transfer.exact

        custody = home.custody_record(original.bundle.bundle_id)
        assert custody is not None
        assert custody.hop_count == 2
        assert custody.complete
        recovered = dna_trace_from_canonical_json(
            home.reconstruct(original.manifest.fingerprint)
        )
        assert recovered == traces[index]

    for index in (2, 3):
        assert not home.knows_manifest(publications[index].manifest.fingerprint)

    home.transition(NodeMode.RICH_HOME)
    assert home.mode is NodeMode.RICH_HOME
