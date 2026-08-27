import hashlib

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bearer import BearerKind, BearerProfile, EvidenceBasis
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.contact_windows import SyntheticContactWindow
from pollicino.net.deadline_objectives import (
    ApplicationDeadlineObjective,
    evaluate_application_deadlines,
)
from pollicino.net.destination_interval import (
    DestinationIntervalControlProfile,
    DestinationIntervalNodeReferenceMode,
    DestinationIntervalObservation,
    DestinationIntervalStrategy,
    account_destination_interval_control,
)
from pollicino.net.destination_recency import (
    DestinationRecencyControlProfile,
    DestinationRecencyNodeReferenceMode,
    DestinationRecencyObservation,
    DestinationRecencyStrategy,
    account_destination_recency_control,
)
from pollicino.net.fair_scheduling import BearerSchedulingPolicy, FairnessPolicy
from pollicino.net.rapid_schedule import RapidPriorMeetingObservation, run_rapid_deadline_schedule
from pollicino.net.routing_benchmark import RoutingBenchmarkScenario, run_synthetic_routing_benchmark
from pollicino.net.routing_compare import compare_synthetic_routing_strategies
from pollicino.net.scheduling import BundlePriority, ContactSchedulingPolicy, ScheduledBundle
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


OBJECT_BYTES = 64
DEADLINE_S = 1030


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
            seed=181,
        ),
    )


def _policy() -> BearerSchedulingPolicy:
    return BearerSchedulingPolicy(
        bearer_id="lora",
        contact_policy=ContactSchedulingPolicy(
            max_source_bytes=OBJECT_BYTES,
            max_bundles=8,
            max_chunks_per_bundle=1,
        ),
        fairness_policy=FairnessPolicy(
            starvation_seconds=100,
            max_rescue_bundles=1,
            rescue_chunks_per_bundle=1,
        ),
    )


def _inputs():
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "x", "b", "d")
    }
    ledger = CustodyLedger()
    digest = hashlib.sha256(b"regular-commuter-vs-recent-passby").digest()
    payload = (digest * 2)[:OBJECT_BYTES]
    manifest = seed_forwarding_object(
        payload,
        chunk_size=OBJECT_BYTES,
        store=peers["a"].store,
    )
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"recency-failure",
        ttl_seconds=5000,
        hop_limit=16,
        nonce=20260828,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    seed_bundle_custody(bundle, manifest, origin=peers["a"], ledger=ledger, now_s=1000)
    item = ScheduledBundle(
        bundle=bundle,
        manifest=manifest,
        priority=BundlePriority.NORMAL,
        label="micro-reference",
    )

    # School encounters followed by the afternoon/home side of the mobility cycle.
    # X has a very recent but rare gateway encounter; B's last encounter is older
    # but its historical direct encounters with D are regular.
    windows = (
        SyntheticContactWindow("school-a-x", "a", "x", "lora", 1005, 5, 64, 100),
        SyntheticContactWindow("school-a-b", "a", "b", "lora", 1010, 5, 64, 200),
        SyntheticContactWindow("commuter-b-d", "b", "d", "lora", 1020, 5, 64, 300),
        SyntheticContactWindow("rare-x-d-late", "x", "d", "lora", 1100, 5, 64, 400),
    )
    return peers, ledger, item, windows


def test_recent_rare_contact_can_mislead_destination_recency_while_rapid_meets_deadline() -> None:
    peers, ledger, item, windows = _inputs()
    bearer = _bearer()
    policy = _policy()

    # All recency facts are genuine past direct contacts. A's own contact is
    # newer than B's, so recency refuses A->B. X is newer than A, so it accepts
    # A->X even though X's contact was a one-off event.
    recency = DestinationRecencyStrategy(
        destination_id="d",
        prior_observations=(
            DestinationRecencyObservation("a", "d", 950),
            DestinationRecencyObservation("b", "d", 900),
            DestinationRecencyObservation("x", "d", 990),
        ),
    )
    scenario = RoutingBenchmarkScenario(
        scenario_id="uc-mobility-recent-rare-vs-regular",
        strategies=(recency,),
        bundles=(item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers={"lora": bearer},
        scheduling_policies={"lora": policy},
        scheduler_states={},
        destination_ids=("d",),
        tags=("uc-dna-001", "uc-content-001", "recency-failure-gate"),
    )
    benchmark = run_synthetic_routing_benchmark((scenario,))
    deadline = evaluate_application_deadlines(
        benchmark,
        (scenario,),
        (
            ApplicationDeadlineObjective(
                scenario_id=scenario.scenario_id,
                bundle_id=item.bundle.bundle_id.hex(),
                deadline_s=DEADLINE_S,
            ),
        ),
    )
    recency_report = benchmark.strategy("destination-recency")
    recency_outcome = benchmark.scenario(scenario.scenario_id).comparison.strategy(
        "destination-recency"
    ).outcome_for_label("micro-reference")

    assert recency_report.delivered_bundle_count == 1
    assert recency_outcome.first_delivery_s == 1105
    assert deadline.strategy("destination-recency").delivered_late_count == 1
    recency_windows = benchmark.scenario(scenario.scenario_id).comparison.strategy(
        "destination-recency"
    ).windows
    assert recency_windows[0].scheduling is not None  # recent one-off X selected
    assert recency_windows[1].scheduling is None  # regular B rejected as less recent

    # RAPID sees the same underlying mobility history, but unlike recency it can
    # distinguish a regular B-D process from X's single recent observation.
    rapid = run_rapid_deadline_schedule(
        (item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers={"lora": bearer},
        scheduling_policies={"lora": policy},
        scheduler_states={},
        destination_id="d",
        application_deadlines={item.bundle.bundle_id: DEADLINE_S},
        prior_meetings=(
            # A: known but slow/irregular source path (900 s observed interval).
            RapidPriorMeetingObservation("a", "d", 50, opportunity_bytes_a_to_b=64),
            RapidPriorMeetingObservation("a", "d", 950, opportunity_bytes_a_to_b=64),
            # B: older last contact but regular 100 s direct encounters.
            RapidPriorMeetingObservation("b", "d", 700, opportunity_bytes_a_to_b=64),
            RapidPriorMeetingObservation("b", "d", 800, opportunity_bytes_a_to_b=64),
            RapidPriorMeetingObservation("b", "d", 900, opportunity_bytes_a_to_b=64),
            # X: more recent, but only one observation => no defensible interval estimate.
            RapidPriorMeetingObservation("x", "d", 990, opportunity_bytes_a_to_b=64),
        ),
    )
    rapid_outcome = rapid.routing.outcome_for_label("micro-reference")
    assert rapid_outcome.delivered
    assert rapid_outcome.first_delivery_s == 1025
    assert rapid_outcome.first_delivery_s <= DEADLINE_S

    rapid_by_id = {window.encounter.encounter_id: window for window in rapid.windows}
    assert rapid_by_id["school-a-x"].routing.scheduling is None
    assert rapid_by_id["school-a-b"].routing.scheduling is not None
    assert rapid_by_id["commuter-b-d"].encounter.direct_delivery

    # The simple strategy remains much cheaper in control state; its failure is
    # therefore a usefulness/deadline failure, not a byte-cost defeat.
    full_recency_control = account_destination_recency_control(
        recency,
        profile=DestinationRecencyControlProfile(
            DestinationRecencyNodeReferenceMode.FULL_PSEUDONYM_128
        ),
        node_count=4,
    )
    assert full_recency_control.control_wire_bytes > 0
    assert rapid.control_entry_count_lower_bound > recency.quote_entry_count


def test_mean_destination_interval_is_enough_to_fix_the_recency_failure() -> None:
    peers, ledger, item, windows = _inputs()
    interval = DestinationIntervalStrategy(
        destination_id="d",
        prior_observations=(
            # Same history supplied to RAPID, but this baseline retains only the
            # direct running mean interval per node.
            DestinationIntervalObservation("a", "d", 50),
            DestinationIntervalObservation("a", "d", 950),
            DestinationIntervalObservation("b", "d", 700),
            DestinationIntervalObservation("b", "d", 800),
            DestinationIntervalObservation("b", "d", 900),
            DestinationIntervalObservation("x", "d", 990),
        ),
    )
    report = compare_synthetic_routing_strategies(
        (interval,),
        (item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers={"lora": _bearer()},
        scheduling_policies={"lora": _policy()},
        scheduler_states={},
        destination_ids=("d",),
    ).strategy("destination-interval")

    outcome = report.outcome_for_label("micro-reference")
    assert outcome.delivered
    assert outcome.first_delivery_s == 1025
    assert report.windows[0].scheduling is None  # X has only one sample: unknown interval
    assert report.windows[1].scheduling is not None  # B mean=100 s beats A mean=900 s
    assert report.windows[2].scheduling is not None
    assert interval.mean_interval_seconds("a") == 900.0
    assert interval.mean_interval_seconds("b") == 100.0
    assert interval.mean_interval_seconds("x") is None
    assert interval.interval_sample_count("a") == 1
    assert interval.interval_sample_count("b") >= 2

    # The decision needs the same number of non-destination quotes as recency,
    # not RAPID's richer meeting/replica/queue state.
    full = account_destination_interval_control(
        interval,
        profile=DestinationIntervalControlProfile(
            DestinationIntervalNodeReferenceMode.FULL_PSEUDONYM_128
        ),
        node_count=4,
    )
    indexed = account_destination_interval_control(
        interval,
        profile=DestinationIntervalControlProfile(
            DestinationIntervalNodeReferenceMode.SHARED_U16_INDEX
        ),
        node_count=4,
    )
    assert interval.quote_entry_count == 2
    assert full.quote_entry_count == indexed.quote_entry_count == 2
    assert full.control_wire_bytes == 56
    assert indexed.control_wire_bytes == 104


def test_discriminating_history_is_strictly_past_and_contains_no_future_hint() -> None:
    _peers, _ledger, _item, windows = _inputs()
    first_window = min(window.start_s for window in windows)
    historical_times = (50, 950, 700, 800, 900, 990)
    assert max(historical_times) < first_window
    assert first_window == 1005
