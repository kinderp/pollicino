import hashlib

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bearer import BearerKind, BearerProfile, EvidenceBasis
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.contact_windows import SyntheticContactWindow
from pollicino.net.deadline_objectives import (
    ApplicationDeadlineObjective,
    evaluate_application_deadlines,
)
from pollicino.net.fair_scheduling import BearerSchedulingPolicy, FairnessPolicy
from pollicino.net.rapid_schedule import (
    RapidPriorMeetingObservation,
    run_rapid_deadline_schedule,
)
from pollicino.net.routing_baselines import (
    BinarySprayAndWaitStrategy,
    DirectDeliveryStrategy,
    EpidemicStrategy,
    ProphetStrategy,
)
from pollicino.net.routing_benchmark import RoutingBenchmarkScenario, run_synthetic_routing_benchmark
from pollicino.net.scheduling import BundlePriority, ContactSchedulingPolicy, ScheduledBundle
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


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
            seed=111,
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


def _scenario():
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "b", "x", "d")
    }
    ledger = CustodyLedger()
    digest = hashlib.sha256(b"edu-deadline-resource").digest()
    data = digest * 2
    manifest = seed_forwarding_object(data, chunk_size=64, store=peers["a"].store)
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"edu-deadline",
        ttl_seconds=1000,
        hop_limit=8,
        nonce=20260827,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    seed_bundle_custody(bundle, manifest, origin=peers["a"], ledger=ledger, now_s=1000)
    item = ScheduledBundle(
        bundle=bundle,
        manifest=manifest,
        priority=BundlePriority.NORMAL,
        label="edu-resource",
    )
    spray = BinarySprayAndWaitStrategy(("d",), initial_copies=2)
    prophet = ProphetStrategy(("d",))
    scenario = RoutingBenchmarkScenario(
        scenario_id="edu-deadline-discrimination",
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
            SyntheticContactWindow("b-d-history", "b", "d", "lora", 1001, 5, 64, 100),
            SyntheticContactWindow("a-x", "a", "x", "lora", 1005, 5, 64, 200),
            SyntheticContactWindow("a-b", "a", "b", "lora", 1010, 5, 64, 300),
            SyntheticContactWindow("b-d-on-time", "b", "d", "lora", 1020, 5, 64, 400),
            SyntheticContactWindow("x-d-late", "x", "d", "lora", 1060, 5, 64, 500),
        ),
        bearers={"lora": _bearer()},
        scheduling_policies={"lora": _policy()},
        scheduler_states={},
        destination_ids=("d",),
        tags=("uc-edu-001", "deadline-discrimination"),
    )
    return scenario, item, spray, prophet


def test_deadline_reveals_difference_hidden_by_eventual_delivery() -> None:
    scenario, item, spray, prophet = _scenario()
    benchmark = run_synthetic_routing_benchmark((scenario,))
    deadline = evaluate_application_deadlines(
        benchmark,
        (scenario,),
        (
            ApplicationDeadlineObjective(
                scenario_id=scenario.scenario_id,
                bundle_id=item.bundle.bundle_id.hex(),
                deadline_s=1030,
            ),
        ),
    )

    direct_benchmark = benchmark.strategy("direct-delivery")
    epidemic_benchmark = benchmark.strategy("epidemic")
    spray_benchmark = benchmark.strategy("binary-spray-and-wait")
    prophet_benchmark = benchmark.strategy("prophet")

    assert direct_benchmark.delivered_bundle_count == 0
    assert epidemic_benchmark.delivered_bundle_count == 1
    assert spray_benchmark.delivered_bundle_count == 1
    assert prophet_benchmark.delivered_bundle_count == 1

    assert deadline.strategy("direct-delivery").undelivered_count == 1
    assert deadline.strategy("epidemic").delivered_before_deadline_count == 1
    assert deadline.strategy("binary-spray-and-wait").delivered_late_count == 1
    assert deadline.strategy("prophet").delivered_before_deadline_count == 1

    comparison = benchmark.scenario(scenario.scenario_id).comparison
    assert comparison.strategy("epidemic").outcome_for_label("edu-resource").first_delivery_s == 1025
    assert comparison.strategy("binary-spray-and-wait").outcome_for_label("edu-resource").first_delivery_s == 1065
    assert comparison.strategy("prophet").outcome_for_label("edu-resource").first_delivery_s == 1025

    # Spray spent its only transferable copy on X and then waited at A.
    assert spray.copies_for(item, "a") == 1
    assert spray.copies_for(item, "x") == 1
    assert spray.total_copy_tokens(item) == 2

    # PRoPHET learned B->D history and did not replicate toward uninformed X.
    prophet_windows = comparison.strategy("prophet").windows
    assert prophet_windows[1].scheduling is None
    assert prophet_windows[2].scheduling is not None
    assert prophet.predictability("b", "d") > 0

    assert benchmark.evidence_class == "model_synthetic"
    assert deadline.evidence_class == "model_synthetic"


def test_rapid_one_selection_on_same_edu_scenario_is_on_time_without_x_replica() -> None:
    scenario, item, _spray, _prophet = _scenario()

    # RAPID may use only observations that precede the routing experiment. Two
    # historical B<->D meetings establish an inter-meeting estimate; X receives
    # no such future-looking hint.
    prior = (
        RapidPriorMeetingObservation(
            "b", "d", 0, opportunity_bytes_a_to_b=64
        ),
        RapidPriorMeetingObservation(
            "b", "d", 40, opportunity_bytes_a_to_b=64
        ),
    )
    rapid = run_rapid_deadline_schedule(
        scenario.bundles,
        peers=scenario.peers,
        ledger=scenario.ledger,
        windows=scenario.windows,
        bearers=scenario.bearers,
        scheduling_policies=scenario.scheduling_policies,
        scheduler_states=scenario.scheduler_states,
        destination_id="d",
        application_deadlines={item.bundle.bundle_id: 1030},
        prior_meetings=prior,
    )

    outcome = rapid.routing.outcome_for_label("edu-resource")
    assert outcome.delivered
    assert outcome.first_delivery_s == 1025
    assert outcome.first_delivery_s <= 1030

    by_encounter = {window.encounter.encounter_id: window for window in rapid.windows}
    assert by_encounter["a-x"].routing.scheduling is None
    assert by_encounter["a-b"].routing.selected_bundle_ids == (
        item.bundle.bundle_id.hex(),
    )
    assert by_encounter["b-d-on-time"].encounter.direct_delivery

    epidemic = run_synthetic_routing_benchmark((scenario,)).strategy("epidemic")
    assert rapid.routing.used_source_bytes < epidemic.used_source_bytes
    assert rapid.routing.total_wire_bytes < epidemic.total_wire_bytes
    assert rapid.control_entry_count_lower_bound > 0

    # RAPID control work is still entry-count only. Until it has an explicit
    # encoding, the lower content-transfer bytes are not a complete network-byte
    # superiority claim.
    assert rapid.evidence_class == "model_synthetic"
