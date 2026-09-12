import hashlib

import pytest

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bearer import BearerKind, BearerProfile, EvidenceBasis
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.contact_windows import SyntheticContactWindow
from pollicino.net.fair_scheduling import BearerSchedulingPolicy, FairnessPolicy
from pollicino.net.routing_benchmark import (
    RoutingBenchmarkScenario,
    run_synthetic_routing_benchmark,
)
from pollicino.net.routing_compare import FloodAllStrategy, GatewayProgressStrategy
from pollicino.net.scheduling import BundlePriority, ContactSchedulingPolicy, ScheduledBundle
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


def link(seed: int) -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=seed,
    )


def bearer(bearer_id: str, kind: BearerKind, seed: int) -> BearerProfile:
    return BearerProfile(
        bearer_id=bearer_id,
        kind=kind,
        evidence_basis=EvidenceBasis.SYNTHETIC,
        link_profile=link(seed),
    )


def scheduling_policy(
    bearer_id: str,
    *,
    max_source_bytes: int = 4096,
    max_bundles: int = 16,
    starvation_seconds: int = 100,
) -> BearerSchedulingPolicy:
    return BearerSchedulingPolicy(
        bearer_id=bearer_id,
        contact_policy=ContactSchedulingPolicy(
            max_source_bytes=max_source_bytes,
            max_bundles=max_bundles,
            max_chunks_per_bundle=16,
        ),
        fairness_policy=FairnessPolicy(
            starvation_seconds=starvation_seconds,
            max_rescue_bundles=1,
            rescue_chunks_per_bundle=1,
        ),
    )


def content(label: str, chunks: int = 1, size: int = 64) -> bytes:
    pieces = []
    for index in range(chunks):
        digest = hashlib.sha256(f"{label}-{index}".encode()).digest()
        pieces.append((digest * ((size + 31) // 32))[:size])
    return b"".join(pieces)


def make_bundle(
    label: str,
    *,
    origin: ForwardPeer,
    ledger: CustodyLedger,
    priority: BundlePriority,
    nonce: int,
) -> ScheduledBundle:
    manifest = seed_forwarding_object(content(label), chunk_size=64, store=origin.store)
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=f"benchmark-{label}".encode(),
        ttl_seconds=1000,
        hop_limit=8,
        nonce=nonce,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    seed_bundle_custody(bundle, manifest, origin=origin, ledger=ledger, now_s=1000)
    return ScheduledBundle(bundle=bundle, manifest=manifest, priority=priority, label=label)


def bearers():
    return {
        "lora": bearer("lora", BearerKind.LORA, 51),
        "wifi": bearer("wifi", BearerKind.WIFI, 52),
    }


def policies():
    return {
        "lora": scheduling_policy("lora"),
        "wifi": scheduling_policy("wifi"),
    }


def successful_progress_scenario() -> RoutingBenchmarkScenario:
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "x", "b", "d")
    }
    ledger = CustodyLedger()
    item = make_bundle(
        "normal-success",
        origin=peers["a"],
        ledger=ledger,
        priority=BundlePriority.NORMAL,
        nonce=1,
    )
    ranks = {"a": 3, "x": 4, "b": 2, "d": 0}
    return RoutingBenchmarkScenario(
        scenario_id="progress-works",
        strategies=(FloodAllStrategy(), GatewayProgressStrategy(ranks)),
        bundles=(item,),
        peers=peers,
        ledger=ledger,
        windows=(
            SyntheticContactWindow("a-x", "a", "x", "lora", 1001, 5, 64, 100),
            SyntheticContactWindow("a-b", "a", "b", "lora", 1010, 5, 64, 200),
            SyntheticContactWindow("b-d", "b", "d", "wifi", 1020, 5, 64, 300),
        ),
        bearers=bearers(),
        scheduling_policies=policies(),
        scheduler_states={},
        destination_ids=("d",),
        tags=("chain", "normal"),
    )


def misleading_progress_scenario() -> RoutingBenchmarkScenario:
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "x", "d")
    }
    ledger = CustodyLedger()
    item = make_bundle(
        "emergency-detour",
        origin=peers["a"],
        ledger=ledger,
        priority=BundlePriority.EMERGENCY,
        nonce=2,
    )
    ranks = {"a": 2, "x": 3, "d": 0}
    return RoutingBenchmarkScenario(
        scenario_id="progress-misleads",
        strategies=(FloodAllStrategy(), GatewayProgressStrategy(ranks)),
        bundles=(item,),
        peers=peers,
        ledger=ledger,
        windows=(
            SyntheticContactWindow("a-x", "a", "x", "lora", 1001, 5, 64, 400),
            SyntheticContactWindow("x-d", "x", "d", "wifi", 1010, 5, 64, 500),
        ),
        bearers=bearers(),
        scheduling_policies=policies(),
        scheduler_states={},
        destination_ids=("d",),
        tags=("detour", "emergency"),
    )


def test_benchmark_aggregates_delivery_latency_and_bearer_tradeoffs() -> None:
    first = successful_progress_scenario()
    second = misleading_progress_scenario()

    report = run_synthetic_routing_benchmark((first, second))
    flood = report.strategy("flood-all")
    progress = report.strategy("gateway-progress")

    assert report.evidence_class == "model_synthetic"
    assert flood.scenario_count == 2
    assert flood.bundle_opportunity_count == 2
    assert flood.delivered_bundle_count == 2
    assert flood.delivery_rate == 1.0
    assert flood.emergency_opportunity_count == 1
    assert flood.emergency_delivered_count == 1
    assert flood.emergency_delivery_rate == 1.0
    assert flood.delivery_latency_samples_s == (15, 25)
    assert flood.mean_delivery_latency_s == 20.0
    assert flood.median_delivery_latency_s == 20.0

    assert progress.delivered_bundle_count == 1
    assert progress.delivery_rate == 0.5
    assert progress.emergency_delivery_rate == 0.0
    assert progress.delivery_latency_samples_s == (25,)
    assert progress.mean_delivery_latency_s == 25.0
    assert progress.total_wire_bytes < flood.total_wire_bytes

    # Classic DTN transmission-count style metrics and byte-exact Pollicino TRC
    # accounting are both exposed. No classified category may overlap another.
    assert flood.forwarding_decision_count == 5
    assert flood.transferred_chunk_count == 5
    assert progress.forwarding_decision_count == 2
    assert progress.transferred_chunk_count == 2
    assert progress.forwarding_decision_count < flood.forwarding_decision_count
    assert flood.payload_primary_wire_bytes > 0
    assert flood.protocol_metadata_primary_wire_bytes > 0
    assert flood.primary_ack_wire_bytes > 0
    assert flood.classified_wire_bytes == flood.total_wire_bytes
    assert progress.classified_wire_bytes == progress.total_wire_bytes

    flood_lora = next(item for item in flood.bearer_usage if item.bearer_id == "lora")
    progress_lora = next(item for item in progress.bearer_usage if item.bearer_id == "lora")
    assert flood_lora.scenario_count == 2
    assert flood_lora.used_source_bytes > progress_lora.used_source_bytes
    assert flood_lora.forwarding_decision_count > progress_lora.forwarding_decision_count
    assert flood_lora.classified_wire_bytes == flood_lora.total_wire_bytes
    assert progress_lora.classified_wire_bytes == progress_lora.total_wire_bytes

    assert report.scenario("progress-works").tags == ("chain", "normal")
    # Every comparison clones network state; benchmark execution must not mutate inputs.
    assert len(first.peers["d"].store) == 0
    assert len(second.peers["d"].store) == 0


def test_benchmark_aggregates_real_fairness_rescue_events() -> None:
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "d")
    }
    ledger = CustodyLedger()
    high = make_bundle(
        "high-first",
        origin=peers["a"],
        ledger=ledger,
        priority=BundlePriority.HIGH,
        nonce=10,
    )
    normal = make_bundle(
        "normal-starved",
        origin=peers["a"],
        ledger=ledger,
        priority=BundlePriority.NORMAL,
        nonce=11,
    )
    lora = bearer("lora", BearerKind.LORA, 53)
    scenario = RoutingBenchmarkScenario(
        scenario_id="fairness-rescue",
        strategies=(FloodAllStrategy(),),
        bundles=(high, normal),
        peers=peers,
        ledger=ledger,
        windows=(
            SyntheticContactWindow("first", "a", "d", "lora", 1001, 5, 64, 600),
            SyntheticContactWindow("second", "a", "d", "lora", 1201, 5, 64, 700),
        ),
        bearers={"lora": lora},
        scheduling_policies={
            "lora": scheduling_policy(
                "lora",
                max_source_bytes=64,
                max_bundles=1,
                starvation_seconds=100,
            )
        },
        scheduler_states={},
        destination_ids=("d",),
    )

    report = run_synthetic_routing_benchmark((scenario,))
    flood = report.strategy("flood-all")
    lora_usage = flood.bearer_usage[0]

    assert flood.delivered_bundle_count == 2
    assert flood.forwarding_decision_count == 2
    assert flood.transferred_chunk_count == 2
    assert flood.fairness_rescue_count == 1
    assert lora_usage.fairness_rescue_count == 1
    assert flood.classified_wire_bytes == flood.total_wire_bytes


def test_benchmark_requires_same_strategy_ids_in_every_scenario() -> None:
    first = successful_progress_scenario()
    second = misleading_progress_scenario()
    incompatible = RoutingBenchmarkScenario(
        scenario_id="incompatible",
        strategies=(FloodAllStrategy(),),
        bundles=second.bundles,
        peers=second.peers,
        ledger=second.ledger,
        windows=second.windows,
        bearers=second.bearers,
        scheduling_policies=second.scheduling_policies,
        scheduler_states=second.scheduler_states,
        destination_ids=second.destination_ids,
    )

    with pytest.raises(ValueError, match="same unique strategy IDs"):
        run_synthetic_routing_benchmark((first, incompatible))
