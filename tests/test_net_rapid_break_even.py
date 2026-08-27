import hashlib

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bearer import BearerKind, BearerProfile, EvidenceBasis
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.contact_windows import SyntheticContactWindow
from pollicino.net.fair_scheduling import BearerSchedulingPolicy, FairnessPolicy
from pollicino.net.rapid_break_even import compare_rapid_wire_cost
from pollicino.net.rapid_control_wire import (
    RapidControlWireProfile,
    RapidNodeReferenceMode,
    account_rapid_control_wire,
)
from pollicino.net.rapid_schedule import RapidPriorMeetingObservation, run_rapid_deadline_schedule
from pollicino.net.routing_baselines import EpidemicStrategy
from pollicino.net.routing_compare import compare_synthetic_routing_strategies
from pollicino.net.scheduling import BundlePriority, ContactSchedulingPolicy, ScheduledBundle
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


def _payload(size: int) -> bytes:
    digest = hashlib.sha256(f"rapid-break-even-{size}".encode()).digest()
    return (digest * ((size + 31) // 32))[:size]


def _bearer() -> BearerProfile:
    return BearerProfile(
        bearer_id="lora",
        kind=BearerKind.LORA,
        evidence_basis=EvidenceBasis.SYNTHETIC,
        link_profile=ScarceLinkProfile(
            max_frame_bytes=64,
            bitrate_bps=5000,
            ack_bytes=8,
            max_retries=2,
            seed=141,
        ),
    )


def _policy(size: int) -> BearerSchedulingPolicy:
    return BearerSchedulingPolicy(
        bearer_id="lora",
        contact_policy=ContactSchedulingPolicy(
            max_source_bytes=size,
            max_bundles=8,
            max_chunks_per_bundle=1,
        ),
        fairness_policy=FairnessPolicy(
            starvation_seconds=100,
            max_rescue_bundles=1,
            rescue_chunks_per_bundle=1,
        ),
    )


def _run(size: int):
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "x", "b", "d")
    }
    ledger = CustodyLedger()
    manifest = seed_forwarding_object(
        _payload(size),
        chunk_size=size,
        store=peers["a"].store,
    )
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=hashlib.sha256(f"rapid-be-{size}".encode()).digest()[:16],
        ttl_seconds=2000,
        hop_limit=16,
        nonce=size,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    seed_bundle_custody(bundle, manifest, origin=peers["a"], ledger=ledger, now_s=1000)
    item = ScheduledBundle(
        bundle=bundle,
        manifest=manifest,
        priority=BundlePriority.NORMAL,
        label=f"size-{size}",
    )
    windows = (
        SyntheticContactWindow("a-x", "a", "x", "lora", 1005, 5, size, 100),
        SyntheticContactWindow("a-b", "a", "b", "lora", 1010, 5, size, 200),
        SyntheticContactWindow("b-d", "b", "d", "lora", 1020, 5, size, 300),
    )
    prior = (
        RapidPriorMeetingObservation("a", "d", 0, opportunity_bytes_a_to_b=size),
        RapidPriorMeetingObservation("b", "d", 0, opportunity_bytes_a_to_b=size),
        RapidPriorMeetingObservation("b", "d", 40, opportunity_bytes_a_to_b=size),
        RapidPriorMeetingObservation("a", "d", 100, opportunity_bytes_a_to_b=size),
    )
    bearer = _bearer()
    policy = _policy(size)
    rapid = run_rapid_deadline_schedule(
        (item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers={"lora": bearer},
        scheduling_policies={"lora": policy},
        scheduler_states={},
        destination_id="d",
        application_deadlines={item.bundle.bundle_id: 1030},
        prior_meetings=prior,
    )
    epidemic = compare_synthetic_routing_strategies(
        (EpidemicStrategy(),),
        (item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers={"lora": bearer},
        scheduling_policies={"lora": policy},
        scheduler_states={},
        destination_ids=("d",),
    ).strategy("epidemic")
    return rapid, epidemic


def test_break_even_sweep_preserves_delivery_and_exposes_control_regime() -> None:
    sizes = (16, 32, 64, 128, 256)
    full_deltas = []
    indexed_deltas = []

    for size in sizes:
        rapid, epidemic = _run(size)
        assert rapid.routing.delivered_bundle_count == epidemic.delivered_bundle_count == 1
        assert rapid.routing.outcomes[0].first_delivery_s == epidemic.outcomes[0].first_delivery_s == 1025
        assert rapid.routing.used_source_bytes == 2 * size
        assert epidemic.used_source_bytes == 3 * size

        full_control = account_rapid_control_wire(
            rapid,
            profile=RapidControlWireProfile(RapidNodeReferenceMode.FULL_PSEUDONYM_128),
            node_count=4,
        )
        indexed_control = account_rapid_control_wire(
            rapid,
            profile=RapidControlWireProfile(RapidNodeReferenceMode.SHARED_U16_INDEX),
            node_count=4,
        )
        full = compare_rapid_wire_cost(rapid, baseline=epidemic, control=full_control)
        indexed = compare_rapid_wire_cost(
            rapid, baseline=epidemic, control=indexed_control
        )

        # Smarter routing always avoids one authoritative object replication.
        assert full.governed_transfer_savings_before_control > 0
        assert indexed.governed_transfer_savings_before_control == full.governed_transfer_savings_before_control
        full_deltas.append(full.delta_vs_baseline_bytes)
        indexed_deltas.append(indexed.delta_vs_baseline_bytes)

    # As object size grows, the avoided governed transfer becomes more valuable
    # while this fixed one-bundle control pattern does not grow with payload.
    assert full_deltas == sorted(full_deltas, reverse=True)
    assert indexed_deltas == sorted(indexed_deltas, reverse=True)

    # The smallest regime is intentionally allowed to reject RAPID, while a
    # sufficiently larger object must eventually amortize this control model.
    assert full_deltas[0] > 0
    assert full_deltas[-1] < 0
    assert indexed_deltas[-1] < 0
