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
    DestinationIntervalObservation,
    DestinationIntervalStrategy,
)
from pollicino.net.fair_scheduling import BearerSchedulingPolicy, FairnessPolicy
from pollicino.net.rapid_schedule import RapidPriorMeetingObservation, run_rapid_deadline_schedule
from pollicino.net.routing_benchmark import RoutingBenchmarkScenario, run_synthetic_routing_benchmark
from pollicino.net.scheduling import BundlePriority, ContactSchedulingPolicy, ScheduledBundle
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


OBJECT_BYTES = 64
CHUNK_BYTES = 16
DEADLINE_S = 1040


def _bearer(bearer_id: str, kind: BearerKind, seed: int) -> BearerProfile:
    return BearerProfile(
        bearer_id=bearer_id,
        kind=kind,
        evidence_basis=EvidenceBasis.SYNTHETIC,
        link_profile=ScarceLinkProfile(
            max_frame_bytes=64,
            bitrate_bps=5000,
            ack_bytes=8,
            max_retries=2,
            seed=seed,
        ),
    )


def _policy(bearer_id: str) -> BearerSchedulingPolicy:
    return BearerSchedulingPolicy(
        bearer_id=bearer_id,
        contact_policy=ContactSchedulingPolicy(
            max_source_bytes=OBJECT_BYTES,
            max_bundles=8,
            max_chunks_per_bundle=4,
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
        for peer_id in ("a", "b", "c", "d")
    }
    ledger = CustodyLedger()
    # Four distinct deterministic 16-byte chunks. Repeating one digest here
    # would let the content-addressed store deduplicate chunks and would no
    # longer test a true four-opportunity transfer.
    payload = b"".join(
        hashlib.sha256(f"capacity-gate-chunk-{index}".encode()).digest()[:CHUNK_BYTES]
        for index in range(4)
    )
    assert len(payload) == OBJECT_BYTES
    manifest = seed_forwarding_object(
        payload,
        chunk_size=CHUNK_BYTES,
        store=peers["a"].store,
    )
    assert len({ref.sha256_digest for ref in manifest.chunks}) == 4
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"capacity-gate",
        ttl_seconds=5000,
        hop_limit=16,
        nonce=20260829,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    seed_bundle_custody(bundle, manifest, origin=peers["a"], ledger=ledger, now_s=1000)
    item = ScheduledBundle(
        bundle=bundle,
        manifest=manifest,
        priority=BundlePriority.NORMAL,
        label="content-reference",
    )

    bearers = {
        "lora": _bearer("lora", BearerKind.LORA, 191),
        "wifi": _bearer("wifi", BearerKind.WIFI, 192),
    }
    policies = {
        "lora": _policy("lora"),
        "wifi": _policy("wifi"),
    }

    windows = (
        # School contacts are rich enough to hand a complete 64-byte object to a relay.
        SyntheticContactWindow("school-a-b", "a", "b", "lora", 1005, 5, 64, 100),
        SyntheticContactWindow("school-a-c", "a", "c", "lora", 1010, 5, 64, 200),
        # B reaches D frequently, but only 16 authoritative source bytes fit per
        # modeled contact, so four distinct 16-byte chunks require four meetings.
        SyntheticContactWindow("b-d-1", "b", "d", "lora", 1020, 5, 16, 300),
        # C reaches D less frequently but through a rich opportunity that can
        # complete the object in one contact.
        SyntheticContactWindow("c-d-rich", "c", "d", "wifi", 1030, 5, 64, 400),
        SyntheticContactWindow("b-d-2", "b", "d", "lora", 1070, 5, 16, 500),
        SyntheticContactWindow("b-d-3", "b", "d", "lora", 1120, 5, 16, 600),
        SyntheticContactWindow("b-d-4", "b", "d", "lora", 1170, 5, 16, 700),
    )
    return peers, ledger, item, windows, bearers, policies


def _interval_strategy() -> DestinationIntervalStrategy:
    return DestinationIntervalStrategy(
        destination_id="d",
        prior_observations=(
            # A itself is middling: two contacts 75 s apart.
            DestinationIntervalObservation("a", "d", 800),
            DestinationIntervalObservation("a", "d", 875),
            # B is the most frequent direct contact: mean interval 50 s.
            DestinationIntervalObservation("b", "d", 800),
            DestinationIntervalObservation("b", "d", 850),
            DestinationIntervalObservation("b", "d", 900),
            # C is less frequent than A: mean interval 100 s, so Interval will
            # not copy A->C even though C's transfer opportunity is much richer.
            DestinationIntervalObservation("c", "d", 800),
            DestinationIntervalObservation("c", "d", 900),
        ),
    )


def test_interval_frequency_alone_misses_deadline_when_contact_capacity_differs() -> None:
    peers, ledger, item, windows, bearers, policies = _inputs()
    interval = _interval_strategy()
    scenario = RoutingBenchmarkScenario(
        scenario_id="uc-content-frequency-vs-opportunity",
        strategies=(interval,),
        bundles=(item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers=bearers,
        scheduling_policies=policies,
        scheduler_states={},
        destination_ids=("d",),
        tags=("uc-content-001", "uc-dna-001", "interval-capacity-gate"),
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
    report = benchmark.scenario(scenario.scenario_id).comparison.strategy(
        "destination-interval"
    )
    outcome = report.outcome_for_label("content-reference")

    assert report.windows[0].scheduling is not None  # B 50 s beats A 75 s.
    assert report.windows[1].scheduling is None  # C 100 s loses to A 75 s.
    assert outcome.delivered
    assert outcome.first_delivery_s == 1175
    assert deadline.strategy("destination-interval").delivered_late_count == 1


def test_rapid_uses_observed_transfer_opportunity_and_reaches_rich_relay_on_time() -> None:
    peers, ledger, item, windows, bearers, policies = _inputs()

    rapid = run_rapid_deadline_schedule(
        (item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers=bearers,
        scheduling_policies=policies,
        scheduler_states={},
        destination_id="d",
        application_deadlines={item.bundle.bundle_id: DEADLINE_S},
        prior_meetings=(
            # A: 75 s direct interval, but thin 16-byte destination opportunity.
            RapidPriorMeetingObservation("a", "d", 800, opportunity_bytes_a_to_b=16),
            RapidPriorMeetingObservation("a", "d", 875, opportunity_bytes_a_to_b=16),
            # B: faster 50 s meetings, also only 16 bytes per opportunity.
            RapidPriorMeetingObservation("b", "d", 800, opportunity_bytes_a_to_b=16),
            RapidPriorMeetingObservation("b", "d", 850, opportunity_bytes_a_to_b=16),
            RapidPriorMeetingObservation("b", "d", 900, opportunity_bytes_a_to_b=16),
            # C: slower 100 s meetings, but 64 bytes per opportunity: one meeting
            # can serve the complete object.
            RapidPriorMeetingObservation("c", "d", 800, opportunity_bytes_a_to_b=64),
            RapidPriorMeetingObservation("c", "d", 900, opportunity_bytes_a_to_b=64),
        ),
    )

    outcome = rapid.routing.outcome_for_label("content-reference")
    assert outcome.delivered
    assert outcome.first_delivery_s == 1035
    assert outcome.first_delivery_s <= DEADLINE_S

    by_id = {window.encounter.encounter_id: window for window in rapid.windows}
    # RAPID may still find B useful, but it must also recognize that C is a
    # useful complete-replica candidate despite C's longer inter-meeting time.
    assert by_id["school-a-c"].routing.scheduling is not None
    assert by_id["c-d-rich"].encounter.direct_delivery


def test_capacity_history_is_explicit_and_not_derived_from_contact_duration() -> None:
    _peers, _ledger, _item, windows, _bearers, _policies = _inputs()
    first_window = min(window.start_s for window in windows)
    assert first_window == 1005
    assert 900 < first_window
    # The synthetic future windows deliberately use equal 5 s durations despite
    # 16-byte and 64-byte logical opportunities. Capacity is explicit input, not
    # duration-derived evidence.
    assert {window.duration_seconds for window in windows} == {5}
