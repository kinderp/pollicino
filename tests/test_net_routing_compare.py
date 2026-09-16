import hashlib

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bearer import BearerKind, BearerProfile, EvidenceBasis
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.contact_windows import SyntheticContactWindow
from pollicino.net.fair_scheduling import (
    BearerSchedulingPolicy,
    FairSchedulerState,
    FairnessPolicy,
)
from pollicino.net.routing_compare import (
    EmergencyFloodProgressStrategy,
    FloodAllStrategy,
    GatewayProgressStrategy,
    HoldLargeOnBearerStrategy,
    compare_synthetic_routing_strategies,
)
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


def scheduling_policy(bearer_id: str) -> BearerSchedulingPolicy:
    return BearerSchedulingPolicy(
        bearer_id=bearer_id,
        contact_policy=ContactSchedulingPolicy(
            max_source_bytes=4096,
            max_bundles=16,
            max_chunks_per_bundle=16,
        ),
        fairness_policy=FairnessPolicy(
            starvation_seconds=100,
            max_rescue_bundles=1,
            rescue_chunks_per_bundle=1,
        ),
    )


def content(label: str, chunks: int, size: int = 64) -> bytes:
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
    priority: BundlePriority = BundlePriority.NORMAL,
    chunks: int = 1,
    nonce: int = 1,
    ttl: int = 1000,
) -> ScheduledBundle:
    manifest = seed_forwarding_object(content(label, chunks), chunk_size=64, store=origin.store)
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=f"route-{label}".encode(),
        ttl_seconds=ttl,
        hop_limit=8,
        nonce=nonce,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    seed_bundle_custody(bundle, manifest, origin=origin, ledger=ledger, now_s=1000)
    return ScheduledBundle(bundle=bundle, manifest=manifest, priority=priority, label=label)


def base_bearers():
    return {
        "lora": bearer("lora", BearerKind.LORA, 41),
        "wifi": bearer("wifi", BearerKind.WIFI, 42),
    }


def base_policies():
    return {
        "lora": scheduling_policy("lora"),
        "wifi": scheduling_policy("wifi"),
    }


def test_gateway_progress_delivers_with_less_wire_than_flooding() -> None:
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "x", "b", "d")
    }
    ledger = CustodyLedger()
    item = make_bundle("message", origin=peers["a"], ledger=ledger)
    windows = [
        SyntheticContactWindow("a-x", "a", "x", "lora", 1001, 5, 64, 100),
        SyntheticContactWindow("a-b", "a", "b", "lora", 1010, 5, 64, 200),
        SyntheticContactWindow("b-d", "b", "d", "wifi", 1020, 5, 64, 300),
    ]

    comparison = compare_synthetic_routing_strategies(
        [
            FloodAllStrategy(),
            GatewayProgressStrategy({"a": 3, "x": 4, "b": 2, "d": 0}),
        ],
        [item],
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers=base_bearers(),
        scheduling_policies=base_policies(),
        scheduler_states={},
        destination_ids=["d"],
    )

    flood = comparison.strategy("flood-all")
    progress = comparison.strategy("gateway-progress")
    assert flood.delivered_bundle_count == 1
    assert progress.delivered_bundle_count == 1
    assert progress.total_wire_bytes < flood.total_wire_bytes
    assert progress.used_source_bytes < flood.used_source_bytes
    assert progress.skipped_window_count == 1
    # Strategy runs use cloned state; the comparison does not mutate the input network.
    assert len(peers["d"].store) == 0


def test_emergency_replication_can_survive_a_bad_progress_hint() -> None:
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "x", "d")
    }
    ledger = CustodyLedger()
    emergency = make_bundle(
        "sos",
        origin=peers["a"],
        ledger=ledger,
        priority=BundlePriority.EMERGENCY,
        nonce=2,
    )
    windows = [
        SyntheticContactWindow("a-x", "a", "x", "lora", 1001, 5, 64, 400),
        SyntheticContactWindow("x-d", "x", "d", "wifi", 1010, 5, 64, 500),
    ]
    ranks = {"a": 2, "x": 3, "d": 0}

    comparison = compare_synthetic_routing_strategies(
        [GatewayProgressStrategy(ranks), EmergencyFloodProgressStrategy(ranks)],
        [emergency],
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers=base_bearers(),
        scheduling_policies=base_policies(),
        scheduler_states={},
        destination_ids=["d"],
    )

    progress = comparison.strategy("gateway-progress")
    emergency_flood = comparison.strategy("emergency-flood-progress")
    assert progress.delivered_bundle_count == 0
    assert emergency_flood.delivered_bundle_count == 1
    assert emergency_flood.emergency_delivered_count == 1


def test_holding_large_normal_data_for_wifi_delays_delivery_but_avoids_lora_payload() -> None:
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "d")
    }
    ledger = CustodyLedger()
    large = make_bundle(
        "large-normal",
        origin=peers["a"],
        ledger=ledger,
        chunks=2,
        nonce=3,
    )
    windows = [
        SyntheticContactWindow("early-lora", "a", "d", "lora", 1001, 5, 128, 600),
        SyntheticContactWindow("later-wifi", "a", "d", "wifi", 1010, 5, 128, 700),
    ]

    comparison = compare_synthetic_routing_strategies(
        [
            FloodAllStrategy(),
            HoldLargeOnBearerStrategy(max_object_size_bytes=64),
        ],
        [large],
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers=base_bearers(),
        scheduling_policies=base_policies(),
        scheduler_states={},
        destination_ids=["d"],
    )

    flood = comparison.strategy("flood-all")
    hold = comparison.strategy("hold-large-on-scarce")
    assert flood.outcome_for_label("large-normal").first_delivery_s == 1006
    assert hold.outcome_for_label("large-normal").first_delivery_s == 1015
    flood_lora = next(item for item in flood.bearer_usage if item.bearer_id == "lora")
    hold_lora = next(item for item in hold.bearer_usage if item.bearer_id == "lora")
    assert flood_lora.used_source_bytes == 128
    assert hold_lora.used_source_bytes == 0
    assert hold.delivered_bundle_count == 1
