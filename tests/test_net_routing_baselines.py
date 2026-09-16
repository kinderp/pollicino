import hashlib

import pytest

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bearer import BearerKind, BearerProfile, EvidenceBasis
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.contact_windows import SyntheticContactWindow
from pollicino.net.fair_scheduling import (
    BearerSchedulingPolicy,
    FairnessPolicy,
)
from pollicino.net.routing_baselines import DirectDeliveryStrategy, EpidemicStrategy
from pollicino.net.routing_compare import compare_synthetic_routing_strategies
from pollicino.net.scheduling import BundlePriority, ContactSchedulingPolicy, ScheduledBundle
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


def _link(seed: int) -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=seed,
    )


def _bearer(bearer_id: str, kind: BearerKind, seed: int) -> BearerProfile:
    return BearerProfile(
        bearer_id=bearer_id,
        kind=kind,
        evidence_basis=EvidenceBasis.SYNTHETIC,
        link_profile=_link(seed),
    )


def _policy(bearer_id: str) -> BearerSchedulingPolicy:
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


def _content(label: str, size: int = 64) -> bytes:
    digest = hashlib.sha256(label.encode()).digest()
    return (digest * ((size + len(digest) - 1) // len(digest)))[:size]


def _bundle(origin: ForwardPeer, ledger: CustodyLedger) -> ScheduledBundle:
    manifest = seed_forwarding_object(_content("baseline"), chunk_size=64, store=origin.store)
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"routing-baseline",
        ttl_seconds=1000,
        hop_limit=8,
        nonce=1,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    seed_bundle_custody(bundle, manifest, origin=origin, ledger=ledger, now_s=1000)
    return ScheduledBundle(
        bundle=bundle,
        manifest=manifest,
        priority=BundlePriority.NORMAL,
        label="baseline-object",
    )


def _network():
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "x", "d")
    }
    ledger = CustodyLedger()
    item = _bundle(peers["a"], ledger)
    bearers = {
        "lora": _bearer("lora", BearerKind.LORA, 71),
        "wifi": _bearer("wifi", BearerKind.WIFI, 72),
    }
    policies = {
        "lora": _policy("lora"),
        "wifi": _policy("wifi"),
    }
    return peers, ledger, item, bearers, policies


def test_epidemic_relay_delivers_when_direct_delivery_has_no_direct_contact() -> None:
    peers, ledger, item, bearers, policies = _network()
    windows = (
        SyntheticContactWindow("a-x", "a", "x", "lora", 1001, 5, 64, 100),
        SyntheticContactWindow("x-d", "x", "d", "wifi", 1010, 5, 64, 200),
    )

    comparison = compare_synthetic_routing_strategies(
        (DirectDeliveryStrategy(("d",)), EpidemicStrategy()),
        (item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers=bearers,
        scheduling_policies=policies,
        scheduler_states={},
        destination_ids=("d",),
    )

    direct = comparison.strategy("direct-delivery")
    epidemic = comparison.strategy("epidemic")

    assert direct.delivered_bundle_count == 0
    assert direct.total_wire_bytes == 0
    assert epidemic.delivered_bundle_count == 1
    assert epidemic.outcome_for_label("baseline-object").first_delivery_s == 1015
    assert epidemic.total_wire_bytes > 0
    # Comparator isolation: the original destination remains untouched.
    assert len(peers["d"].store) == 0


def test_direct_delivery_avoids_unhelpful_replication_when_direct_contact_exists() -> None:
    peers, ledger, item, bearers, policies = _network()
    windows = (
        SyntheticContactWindow("a-x", "a", "x", "lora", 1001, 5, 64, 300),
        SyntheticContactWindow("a-d", "a", "d", "wifi", 1010, 5, 64, 400),
    )

    comparison = compare_synthetic_routing_strategies(
        (DirectDeliveryStrategy(("d",)), EpidemicStrategy()),
        (item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers=bearers,
        scheduling_policies=policies,
        scheduler_states={},
        destination_ids=("d",),
    )

    direct = comparison.strategy("direct-delivery")
    epidemic = comparison.strategy("epidemic")

    assert direct.delivered_bundle_count == 1
    assert epidemic.delivered_bundle_count == 1
    assert direct.outcome_for_label("baseline-object").first_delivery_s == 1015
    assert epidemic.outcome_for_label("baseline-object").first_delivery_s == 1015
    assert direct.total_wire_bytes < epidemic.total_wire_bytes
    assert direct.skipped_window_count == 1


def test_direct_delivery_requires_unique_non_empty_destinations() -> None:
    with pytest.raises(ValueError, match="non-empty tuple"):
        DirectDeliveryStrategy(())
    with pytest.raises(ValueError, match="unique"):
        DirectDeliveryStrategy(("d", "d"))
