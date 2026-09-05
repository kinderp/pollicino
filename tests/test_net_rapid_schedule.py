import hashlib

import pytest

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bearer import BearerKind, BearerProfile, EvidenceBasis
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.contact_windows import SyntheticContactWindow
from pollicino.net.fair_scheduling import BearerSchedulingPolicy, FairnessPolicy
from pollicino.net.rapid_control_wire import (
    RapidControlWireProfile,
    RapidNodeReferenceMode,
    account_rapid_control_wire,
    rapid_modeled_total_wire_bytes,
)
from pollicino.net.rapid_schedule import (
    RAPID_DEADLINE_PROTOTYPE_ID,
    RapidPriorMeetingObservation,
    run_rapid_deadline_schedule,
)
from pollicino.net.routing_baselines import EpidemicStrategy
from pollicino.net.routing_compare import compare_synthetic_routing_strategies
from pollicino.net.scheduling import BundlePriority, ContactSchedulingPolicy, ScheduledBundle
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


def _data(label: str, size: int = 64) -> bytes:
    digest = hashlib.sha256(label.encode()).digest()
    return (digest * ((size + 31) // 32))[:size]


def _bundle(origin: ForwardPeer, ledger: CustodyLedger, *, nonce: int = 1) -> ScheduledBundle:
    manifest = seed_forwarding_object(
        _data(f"rapid-schedule-{nonce}"),
        chunk_size=64,
        store=origin.store,
    )
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=hashlib.sha256(f"rapid-schedule-{nonce}".encode()).digest()[:16],
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
        label=f"rapid-schedule-{nonce}",
    )


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
            seed=121,
        ),
    )


def _policy() -> BearerSchedulingPolicy:
    return BearerSchedulingPolicy(
        bearer_id="lora",
        contact_policy=ContactSchedulingPolicy(
            max_source_bytes=64,
            max_bundles=8,
            max_chunks_per_bundle=1,
        ),
        fairness_policy=FairnessPolicy(
            starvation_seconds=100,
            max_rescue_bundles=1,
            rescue_chunks_per_bundle=1,
        ),
    )


def _scenario_inputs():
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "x", "b", "d")
    }
    ledger = CustodyLedger()
    item = _bundle(peers["a"], ledger)
    windows = (
        SyntheticContactWindow("a-x", "a", "x", "lora", 1005, 5, 64, 100),
        SyntheticContactWindow("a-b", "a", "b", "lora", 1010, 5, 64, 200),
        SyntheticContactWindow("b-d", "b", "d", "lora", 1020, 5, 64, 300),
    )
    prior = (
        RapidPriorMeetingObservation("a", "d", 0, opportunity_bytes_a_to_b=64),
        RapidPriorMeetingObservation("b", "d", 0, opportunity_bytes_a_to_b=64),
        RapidPriorMeetingObservation("b", "d", 40, opportunity_bytes_a_to_b=64),
        RapidPriorMeetingObservation("a", "d", 100, opportunity_bytes_a_to_b=64),
    )
    return peers, ledger, item, windows, prior


def _run_rapid():
    peers, ledger, item, windows, prior = _scenario_inputs()
    report = run_rapid_deadline_schedule(
        (item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers={"lora": _bearer()},
        scheduling_policies={"lora": _policy()},
        scheduler_states={},
        destination_id="d",
        application_deadlines={item.bundle.bundle_id: 1030},
        prior_meetings=prior,
    )
    return peers, ledger, item, windows, report


def test_rapid_schedule_uses_learned_relay_and_delivers_on_time() -> None:
    peers, ledger, item, _windows, report = _run_rapid()

    outcome = report.routing.outcome_for_label(item.label)
    assert report.strategy_id == RAPID_DEADLINE_PROTOTYPE_ID
    assert outcome.delivered
    assert outcome.first_delivery_s == 1025
    assert outcome.first_delivery_s <= 1030
    assert report.windows[0].routing.scheduling is None  # uninformed X skipped
    assert report.windows[1].routing.selected_bundle_ids == (
        item.bundle.bundle_id.hex(),
    )
    assert report.windows[2].encounter.direct_delivery
    assert report.control_entry_count_lower_bound > 0
    assert report.total_wire_bytes_excluding_rapid_control > 0

    # Runner clones stores/custody; original experiment inputs remain untouched.
    assert len(peers["x"].store) == 0
    assert len(peers["b"].store) == 0
    assert len(peers["d"].store) == 0
    assert ledger.get(item.bundle.bundle_id, "b") is None
    assert ledger.get(item.bundle.bundle_id, "d") is None


def test_same_scenario_rapid_avoids_one_epidemic_content_replication() -> None:
    peers, ledger, item, windows, rapid = _run_rapid()
    bearers = {"lora": _bearer()}
    policies = {"lora": _policy()}

    epidemic = compare_synthetic_routing_strategies(
        (EpidemicStrategy(),),
        (item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers=bearers,
        scheduling_policies=policies,
        scheduler_states={},
        destination_ids=("d",),
    ).strategy("epidemic")

    assert rapid.routing.delivered_bundle_count == epidemic.delivered_bundle_count == 1
    assert rapid.routing.outcome_for_label(item.label).first_delivery_s == epidemic.outcome_for_label(
        item.label
    ).first_delivery_s == 1025
    assert rapid.routing.used_source_bytes == 128  # A->B + B->D
    assert epidemic.used_source_bytes == 192  # A->X + A->B + B->D
    assert rapid.routing.total_wire_bytes < epidemic.total_wire_bytes
    assert rapid.control_entry_count_lower_bound > 0
    # This remains only a governed-content comparison until the explicit RAPID
    # control accounting below is included.


def test_rapid_control_wire_is_explicit_and_shared_indices_do_not_hide_bootstrap() -> None:
    _peers, _ledger, _item, _windows, rapid = _run_rapid()

    full_profile = RapidControlWireProfile(
        RapidNodeReferenceMode.FULL_PSEUDONYM_128
    )
    indexed_profile = RapidControlWireProfile(
        RapidNodeReferenceMode.SHARED_U16_INDEX
    )
    full = account_rapid_control_wire(rapid, profile=full_profile, node_count=4)
    indexed = account_rapid_control_wire(rapid, profile=indexed_profile, node_count=4)

    assert full.control_wire_bytes > 0
    assert full.bootstrap_wire_bytes == 0
    assert indexed.bootstrap_wire_bytes == 4 + 4 * (2 + 16)
    assert indexed.meeting_wire_bytes < full.meeting_wire_bytes
    assert indexed.replica_wire_bytes < full.replica_wire_bytes
    assert indexed.queue_quote_wire_bytes < full.queue_quote_wire_bytes
    assert (
        full.meeting_entry_count
        + full.replica_entry_count
        + full.delivery_entry_count
        + full.queue_quote_entry_count
        == rapid.control_entry_count_lower_bound
    )
    assert rapid_modeled_total_wire_bytes(rapid, control=full) == (
        rapid.total_wire_bytes_excluding_rapid_control + full.control_wire_bytes
    )
    assert rapid_modeled_total_wire_bytes(rapid, control=indexed) == (
        rapid.total_wire_bytes_excluding_rapid_control + indexed.control_wire_bytes
    )


def test_prior_history_must_precede_first_routing_window() -> None:
    peers, ledger, item, windows, _ = _scenario_inputs()

    with pytest.raises(ValueError, match="precede the first routing window"):
        run_rapid_deadline_schedule(
            (item,),
            peers=peers,
            ledger=ledger,
            windows=windows,
            bearers={"lora": _bearer()},
            scheduling_policies={"lora": _policy()},
            scheduler_states={},
            destination_id="d",
            application_deadlines={item.bundle.bundle_id: 1030},
            prior_meetings=(
                RapidPriorMeetingObservation(
                    "a", "d", 1005, opportunity_bytes_a_to_b=64
                ),
            ),
        )


def test_schedule_rejects_unknown_deadline_bundle() -> None:
    peers, ledger, item, windows, prior = _scenario_inputs()
    with pytest.raises(KeyError, match="unknown bundle"):
        run_rapid_deadline_schedule(
            (item,),
            peers=peers,
            ledger=ledger,
            windows=windows,
            bearers={"lora": _bearer()},
            scheduling_policies={"lora": _policy()},
            scheduler_states={},
            destination_id="d",
            application_deadlines={hashlib.sha256(b"other").digest(): 1030},
            prior_meetings=prior,
        )
