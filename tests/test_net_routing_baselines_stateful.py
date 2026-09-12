import hashlib

import pytest

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bearer import BearerKind, BearerProfile, EvidenceBasis
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.contact_windows import SyntheticContactWindow
from pollicino.net.fair_scheduling import BearerSchedulingPolicy, FairnessPolicy
from pollicino.net.routing_baselines import (
    BinarySprayAndWaitStrategy,
    DirectDeliveryStrategy,
    EpidemicStrategy,
    ProphetStrategy,
)
from pollicino.net.routing_benchmark import (
    RoutingBenchmarkScenario,
    run_synthetic_routing_benchmark,
)
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


def _bundle(origin: ForwardPeer, ledger: CustodyLedger, *, nonce: int = 1) -> ScheduledBundle:
    manifest = seed_forwarding_object(
        _content(f"stateful-{nonce}"), chunk_size=64, store=origin.store
    )
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=f"stateful-{nonce}".encode(),
        ttl_seconds=2000,
        hop_limit=16,
        nonce=nonce,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    seed_bundle_custody(bundle, manifest, origin=origin, ledger=ledger, now_s=1000)
    return ScheduledBundle(
        bundle=bundle,
        manifest=manifest,
        priority=BundlePriority.NORMAL,
        label=f"stateful-{nonce}",
    )


def _bearers():
    return {
        "lora": _bearer("lora", BearerKind.LORA, 81),
        "wifi": _bearer("wifi", BearerKind.WIFI, 82),
    }


def _policies():
    return {
        "lora": _policy("lora"),
        "wifi": _policy("wifi"),
    }


def test_binary_spray_and_wait_preserves_copy_budget_and_wait_phase() -> None:
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "b", "c", "e", "x", "d")
    }
    ledger = CustodyLedger()
    item = _bundle(peers["a"], ledger)
    spray = BinarySprayAndWaitStrategy(("d",), initial_copies=4)

    scenario = RoutingBenchmarkScenario(
        scenario_id="binary-spray",
        strategies=(spray,),
        bundles=(item,),
        peers=peers,
        ledger=ledger,
        windows=(
            SyntheticContactWindow("a-b", "a", "b", "lora", 1001, 5, 64, 100),
            SyntheticContactWindow("a-c", "a", "c", "lora", 1010, 5, 64, 200),
            SyntheticContactWindow("b-e", "b", "e", "lora", 1020, 5, 64, 300),
            SyntheticContactWindow("c-x", "c", "x", "lora", 1030, 5, 64, 400),
            SyntheticContactWindow("c-d", "c", "d", "wifi", 1040, 5, 64, 500),
        ),
        bearers=_bearers(),
        scheduling_policies=_policies(),
        scheduler_states={},
        destination_ids=("d",),
        tags=("spray",),
    )

    report = run_synthetic_routing_benchmark((scenario,))
    result = report.strategy("binary-spray-and-wait")
    windows = report.scenario("binary-spray").comparison.strategy(
        "binary-spray-and-wait"
    ).windows

    assert result.delivered_bundle_count == 1
    assert windows[3].scheduling is None  # c has one token: wait for destination.
    assert windows[4].scheduling is not None
    assert spray.copies_for(item, "a") == 1
    assert spray.copies_for(item, "b") == 1
    assert spray.copies_for(item, "c") == 1
    assert spray.copies_for(item, "e") == 1
    assert spray.reserved_copy_tokens(item) == 0
    assert spray.total_copy_tokens(item) == 4
    assert len(peers["d"].store) == 0  # comparator input isolation


def test_prophet_learns_useful_relay_and_avoids_uninformed_replication() -> None:
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "b", "x", "d")
    }
    ledger = CustodyLedger()
    item = _bundle(peers["a"], ledger, nonce=2)
    spray = BinarySprayAndWaitStrategy(("d",), initial_copies=4)
    prophet = ProphetStrategy(("d",))

    scenario = RoutingBenchmarkScenario(
        scenario_id="prophet-history",
        strategies=(
            DirectDeliveryStrategy(("d",)),
            EpidemicStrategy(),
            spray,
            prophet,
        ),
        bundles=(item,),
        peers=peers,
        ledger=ledger,
        windows=(
            # b learns that d is a frequently relevant destination before b has the bundle.
            SyntheticContactWindow("b-d-history", "b", "d", "wifi", 1001, 5, 64, 100),
            # x has no useful history; epidemic/spray may spend traffic here, PRoPHET should not.
            SyntheticContactWindow("a-x", "a", "x", "lora", 1005, 5, 64, 200),
            SyntheticContactWindow("a-b", "a", "b", "lora", 1010, 5, 64, 300),
            SyntheticContactWindow("b-d-delivery", "b", "d", "wifi", 1020, 5, 64, 400),
        ),
        bearers=_bearers(),
        scheduling_policies=_policies(),
        scheduler_states={},
        destination_ids=("d",),
        tags=("prophet", "paired-baselines"),
    )

    report = run_synthetic_routing_benchmark((scenario,))
    direct = report.strategy("direct-delivery")
    epidemic = report.strategy("epidemic")
    spray_report = report.strategy("binary-spray-and-wait")
    prophet_report = report.strategy("prophet")
    prophet_windows = report.scenario("prophet-history").comparison.strategy("prophet").windows

    assert direct.delivered_bundle_count == 0
    assert epidemic.delivered_bundle_count == 1
    assert spray_report.delivered_bundle_count == 1
    assert prophet_report.delivered_bundle_count == 1
    assert prophet_windows[1].scheduling is None
    assert prophet_windows[2].scheduling is not None
    assert prophet.predictability("b", "d") > prophet.predictability("a", "d")
    assert prophet.encounter_update_count == 4
    assert prophet.transitive_update_count > 0
    assert prophet_report.total_wire_bytes < epidemic.total_wire_bytes
    assert report.evidence_class == "model_synthetic"


def test_stateful_baselines_reset_between_independent_benchmark_runs() -> None:
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "b", "d")
    }
    ledger = CustodyLedger()
    item = _bundle(peers["a"], ledger, nonce=3)
    spray = BinarySprayAndWaitStrategy(("d",), initial_copies=2)
    prophet = ProphetStrategy(("d",))
    scenario = RoutingBenchmarkScenario(
        scenario_id="repeatable-state",
        strategies=(spray, prophet),
        bundles=(item,),
        peers=peers,
        ledger=ledger,
        windows=(
            SyntheticContactWindow("b-d-history", "b", "d", "wifi", 1001, 5, 64, 100),
            SyntheticContactWindow("a-b", "a", "b", "lora", 1010, 5, 64, 200),
            SyntheticContactWindow("b-d", "b", "d", "wifi", 1020, 5, 64, 300),
        ),
        bearers=_bearers(),
        scheduling_policies=_policies(),
        scheduler_states={},
        destination_ids=("d",),
    )

    first = run_synthetic_routing_benchmark((scenario,))
    first_prophet_updates = prophet.encounter_update_count
    second = run_synthetic_routing_benchmark((scenario,))

    assert first.strategy("binary-spray-and-wait").total_wire_bytes == second.strategy(
        "binary-spray-and-wait"
    ).total_wire_bytes
    assert first.strategy("prophet").total_wire_bytes == second.strategy("prophet").total_wire_bytes
    assert prophet.encounter_update_count == first_prophet_updates
    assert spray.total_copy_tokens(item) == 2


def test_stateful_baseline_parameter_validation() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        BinarySprayAndWaitStrategy(("d",), initial_copies=0)
    with pytest.raises(ValueError, match="gamma"):
        ProphetStrategy(("d",), gamma=1.1)
    with pytest.raises(ValueError, match="time_unit_seconds"):
        ProphetStrategy(("d",), time_unit_seconds=0)
