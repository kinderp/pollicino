import hashlib

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bearer import BearerKind, BearerProfile, EvidenceBasis
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.contact_windows import SyntheticContactWindow
from pollicino.net.destination_interval import (
    DestinationIntervalObservation,
    DestinationIntervalStrategy,
)
from pollicino.net.destination_recency import (
    DestinationRecencyObservation,
    DestinationRecencyStrategy,
)
from pollicino.net.fair_scheduling import BearerSchedulingPolicy, FairnessPolicy
from pollicino.net.rapid_schedule import RapidPriorMeetingObservation, run_rapid_deadline_schedule
from pollicino.net.routing_compare import compare_synthetic_routing_strategies
from pollicino.net.scheduling import BundlePriority, ContactSchedulingPolicy, ScheduledBundle
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


OBJECT_BYTES = 64
DEADLINE_S = 1060


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


def _scenario():
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "b", "c", "d")
    }
    ledger = CustodyLedger()
    digest = hashlib.sha256(b"mobility-recency-discriminator").digest()
    payload = (digest * 2)[:OBJECT_BYTES]
    manifest = seed_forwarding_object(payload, chunk_size=OBJECT_BYTES, store=peers["a"].store)
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"recency-failure",
        ttl_seconds=2000,
        hop_limit=16,
        nonce=20260828,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    seed_bundle_custody(bundle, manifest, origin=peers["a"], ledger=ledger, now_s=1000)
    item = ScheduledBundle(
        bundle=bundle,
        manifest=manifest,
        priority=BundlePriority.NORMAL,
        label="time-sensitive-reference",
    )

    # B has the freshest historical direct encounter with D, but its next
    # actual D contact is late. C has an older last encounter, yet a much more
    # regular D-contact process and an on-time future opportunity.
    windows = (
        SyntheticContactWindow("a-b", "a", "b", "lora", 1010, 5, OBJECT_BYTES, 100),
        SyntheticContactWindow("a-c", "a", "c", "lora", 1020, 5, OBJECT_BYTES, 200),
        SyntheticContactWindow("c-d-on-time", "c", "d", "lora", 1040, 5, OBJECT_BYTES, 300),
        SyntheticContactWindow("b-d-late", "b", "d", "lora", 1100, 5, OBJECT_BYTES, 400),
    )
    return peers, ledger, item, windows


def test_destination_recency_can_choose_fresh_but_late_carrier() -> None:
    peers, ledger, item, windows = _scenario()
    recency = DestinationRecencyStrategy(
        destination_id="d",
        prior_observations=(
            DestinationRecencyObservation("a", "d", 970),
            DestinationRecencyObservation("b", "d", 990),
            DestinationRecencyObservation("c", "d", 950),
        ),
    )
    report = compare_synthetic_routing_strategies(
        (recency,),
        (item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers={"lora": _bearer()},
        scheduling_policies={"lora": _policy()},
        scheduler_states={},
        destination_ids=("d",),
    ).strategy("destination-recency")

    outcome = report.outcome_for_label(item.label)
    assert report.windows[0].scheduling is not None  # A->B: 990 > 970
    assert report.windows[1].scheduling is None      # A->C: 950 < 970
    # Direct-delivery policy still offers C->D, but C never received the object,
    # so the governed scheduler has no useful source bytes to send.
    assert report.windows[2].used_source_bytes == 0
    assert outcome.delivered
    assert outcome.first_delivery_s == 1105
    assert outcome.first_delivery_s > DEADLINE_S


def test_destination_interval_recovers_with_only_direct_regularity_state() -> None:
    peers, ledger, item, windows = _scenario()
    interval = DestinationIntervalStrategy(
        destination_id="d",
        prior_observations=(
            DestinationIntervalObservation("a", "d", 0),
            DestinationIntervalObservation("a", "d", 100),
            DestinationIntervalObservation("b", "d", 0),
            DestinationIntervalObservation("b", "d", 200),
            DestinationIntervalObservation("c", "d", 0),
            DestinationIntervalObservation("c", "d", 40),
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

    outcome = report.outcome_for_label(item.label)
    assert report.windows[0].scheduling is None      # B mean 200 > A mean 100
    assert report.windows[1].scheduling is not None  # C mean 40 < A mean 100
    assert outcome.delivered
    assert outcome.first_delivery_s == 1045
    assert outcome.first_delivery_s <= DEADLINE_S


def test_rapid_recovers_via_older_but_faster_regular_carrier() -> None:
    peers, ledger, item, windows = _scenario()

    # Historical observations all precede the routing experiment. A meets D
    # roughly every 100 s, B every 200 s, while C has a much shorter 40 s
    # inter-meeting estimate. Explicit opportunity samples are identical, so
    # the discriminator is encounter timing rather than an invented bearer
    # speed difference.
    prior = (
        RapidPriorMeetingObservation("a", "d", 0, opportunity_bytes_a_to_b=OBJECT_BYTES),
        RapidPriorMeetingObservation("a", "d", 100, opportunity_bytes_a_to_b=OBJECT_BYTES),
        RapidPriorMeetingObservation("b", "d", 0, opportunity_bytes_a_to_b=OBJECT_BYTES),
        RapidPriorMeetingObservation("b", "d", 200, opportunity_bytes_a_to_b=OBJECT_BYTES),
        RapidPriorMeetingObservation("c", "d", 0, opportunity_bytes_a_to_b=OBJECT_BYTES),
        RapidPriorMeetingObservation("c", "d", 40, opportunity_bytes_a_to_b=OBJECT_BYTES),
    )
    report = run_rapid_deadline_schedule(
        (item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers={"lora": _bearer()},
        scheduling_policies={"lora": _policy()},
        scheduler_states={},
        destination_id="d",
        application_deadlines={item.bundle.bundle_id: DEADLINE_S},
        prior_meetings=prior,
    )

    outcome = report.routing.outcome_for_label(item.label)
    assert report.windows[1].routing.scheduling is not None  # A->C receives a copy
    assert report.windows[2].encounter.direct_delivery
    assert outcome.delivered
    assert outcome.first_delivery_s == 1045
    assert outcome.first_delivery_s <= DEADLINE_S


def test_discriminator_promotes_interval_before_rapid() -> None:
    peers, ledger, item, windows = _scenario()
    recency = DestinationRecencyStrategy(
        destination_id="d",
        prior_observations=(
            DestinationRecencyObservation("a", "d", 970),
            DestinationRecencyObservation("b", "d", 990),
            DestinationRecencyObservation("c", "d", 950),
        ),
    )
    interval = DestinationIntervalStrategy(
        destination_id="d",
        prior_observations=(
            DestinationIntervalObservation("a", "d", 0),
            DestinationIntervalObservation("a", "d", 100),
            DestinationIntervalObservation("b", "d", 0),
            DestinationIntervalObservation("b", "d", 200),
            DestinationIntervalObservation("c", "d", 0),
            DestinationIntervalObservation("c", "d", 40),
        ),
    )
    comparison = compare_synthetic_routing_strategies(
        (recency, interval),
        (item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers={"lora": _bearer()},
        scheduling_policies={"lora": _policy()},
        scheduler_states={},
        destination_ids=("d",),
    )
    rapid = run_rapid_deadline_schedule(
        (item,),
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers={"lora": _bearer()},
        scheduling_policies={"lora": _policy()},
        scheduler_states={},
        destination_id="d",
        application_deadlines={item.bundle.bundle_id: DEADLINE_S},
        prior_meetings=(
            RapidPriorMeetingObservation("a", "d", 0, opportunity_bytes_a_to_b=OBJECT_BYTES),
            RapidPriorMeetingObservation("a", "d", 100, opportunity_bytes_a_to_b=OBJECT_BYTES),
            RapidPriorMeetingObservation("b", "d", 0, opportunity_bytes_a_to_b=OBJECT_BYTES),
            RapidPriorMeetingObservation("b", "d", 200, opportunity_bytes_a_to_b=OBJECT_BYTES),
            RapidPriorMeetingObservation("c", "d", 0, opportunity_bytes_a_to_b=OBJECT_BYTES),
            RapidPriorMeetingObservation("c", "d", 40, opportunity_bytes_a_to_b=OBJECT_BYTES),
        ),
    )

    recency_outcome = comparison.strategy("destination-recency").outcome_for_label(item.label)
    interval_outcome = comparison.strategy("destination-interval").outcome_for_label(item.label)
    rapid_outcome = rapid.routing.outcome_for_label(item.label)
    assert recency_outcome.first_delivery_s == 1105
    assert interval_outcome.first_delivery_s == rapid_outcome.first_delivery_s == 1045
    assert recency_outcome.first_delivery_s > DEADLINE_S
    assert interval_outcome.first_delivery_s <= DEADLINE_S
    assert rapid_outcome.first_delivery_s <= DEADLINE_S
    assert rapid.evidence_class == "model_synthetic"
