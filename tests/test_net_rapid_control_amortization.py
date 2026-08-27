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
from pollicino.net.rapid_shared_quote_accounting import (
    account_shared_opportunity_quotes,
    meetings_needed_from_shared_opportunity_quote,
    rapid_modeled_total_with_shared_opportunity_quotes,
)
from pollicino.net.routing_baselines import EpidemicStrategy
from pollicino.net.routing_compare import compare_synthetic_routing_strategies
from pollicino.net.scheduling import BundlePriority, ContactSchedulingPolicy, ScheduledBundle
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


OBJECT_BYTES = 64


def _payload(index: int) -> bytes:
    digest = hashlib.sha256(f"rapid-amortization-{index}".encode()).digest()
    return (digest * 2)[:OBJECT_BYTES]


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
            seed=151,
        ),
    )


def _policy() -> BearerSchedulingPolicy:
    return BearerSchedulingPolicy(
        bearer_id="lora",
        contact_policy=ContactSchedulingPolicy(
            max_source_bytes=OBJECT_BYTES,
            max_bundles=64,
            max_chunks_per_bundle=1,
        ),
        fairness_policy=FairnessPolicy(
            starvation_seconds=100,
            max_rescue_bundles=1,
            rescue_chunks_per_bundle=1,
        ),
    )


def _run(object_count: int):
    if object_count <= 0:
        raise ValueError("object_count must be positive")
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "x", "b", "d")
    }
    ledger = CustodyLedger()
    bundles = []
    for index in range(object_count):
        manifest = seed_forwarding_object(
            _payload(index),
            chunk_size=OBJECT_BYTES,
            store=peers["a"].store,
        )
        descriptor = DiscoveryDescriptor(
            object_class=1,
            rendezvous_key=hashlib.sha256(
                f"rapid-amortization-{index}".encode()
            ).digest()[:16],
            ttl_seconds=5000,
            hop_limit=16,
            nonce=index + 1,
        )
        bundle = ForwardBundle.from_descriptor(
            manifest,
            descriptor,
            created_at_s=1000,
        )
        seed_bundle_custody(
            bundle,
            manifest,
            origin=peers["a"],
            ledger=ledger,
            now_s=1000,
        )
        bundles.append(
            ScheduledBundle(
                bundle=bundle,
                manifest=manifest,
                priority=BundlePriority.NORMAL,
                label=f"micro-{index:02d}",
            )
        )

    windows = [
        # One initial unhelpful relay opportunity. Epidemic can spend enough
        # logical budget to replicate every object to X; RAPID must decide from
        # one shared encounter/control context whether X is useful.
        SyntheticContactWindow(
            "a-x-initial",
            "a",
            "x",
            "lora",
            1005,
            5,
            object_count * OBJECT_BYTES,
            100,
        )
    ]
    for index in range(object_count):
        base = 1010 + index * 20
        windows.extend(
            (
                SyntheticContactWindow(
                    f"a-b-{index:02d}",
                    "a",
                    "b",
                    "lora",
                    base,
                    5,
                    OBJECT_BYTES,
                    200 + index * 2,
                ),
                SyntheticContactWindow(
                    f"b-d-{index:02d}",
                    "b",
                    "d",
                    "lora",
                    base + 10,
                    5,
                    OBJECT_BYTES,
                    201 + index * 2,
                ),
            )
        )

    # Genuine observations before the routing experiment. B reaches D more
    # frequently than A; both carrier estimates are present so inference cannot
    # inflate B's value by pretending the existing A replica is useless.
    prior = (
        RapidPriorMeetingObservation(
            "a", "d", 800, opportunity_bytes_a_to_b=OBJECT_BYTES
        ),
        RapidPriorMeetingObservation(
            "a", "d", 900, opportunity_bytes_a_to_b=OBJECT_BYTES
        ),
        RapidPriorMeetingObservation(
            "b", "d", 900, opportunity_bytes_a_to_b=OBJECT_BYTES
        ),
        RapidPriorMeetingObservation(
            "b", "d", 940, opportunity_bytes_a_to_b=OBJECT_BYTES
        ),
    )
    deadlines = {item.bundle.bundle_id: 2000 for item in bundles}
    bearer = _bearer()
    policy = _policy()

    rapid = run_rapid_deadline_schedule(
        tuple(bundles),
        peers=peers,
        ledger=ledger,
        windows=tuple(windows),
        bearers={"lora": bearer},
        scheduling_policies={"lora": policy},
        scheduler_states={},
        destination_id="d",
        application_deadlines=deadlines,
        prior_meetings=prior,
    )
    epidemic = compare_synthetic_routing_strategies(
        (EpidemicStrategy(),),
        tuple(bundles),
        peers=peers,
        ledger=ledger,
        windows=tuple(windows),
        bearers={"lora": bearer},
        scheduling_policies={"lora": policy},
        scheduler_states={},
        destination_ids=("d",),
    ).strategy("epidemic")
    return rapid, epidemic


def test_multi_object_control_amortization_keeps_shared_bootstrap_visible() -> None:
    checkpoints = (1, 2, 5, 10, 20)
    indexed_bootstrap = []
    indexed_deltas = []
    queue_entries = []

    for object_count in checkpoints:
        rapid, epidemic = _run(object_count)
        assert rapid.routing.delivered_bundle_count == object_count
        assert epidemic.delivered_bundle_count == object_count
        assert rapid.routing.used_source_bytes == 2 * object_count * OBJECT_BYTES
        assert epidemic.used_source_bytes == 3 * object_count * OBJECT_BYTES

        indexed_control = account_rapid_control_wire(
            rapid,
            profile=RapidControlWireProfile(
                RapidNodeReferenceMode.SHARED_U16_INDEX
            ),
            node_count=4,
        )
        full_control = account_rapid_control_wire(
            rapid,
            profile=RapidControlWireProfile(
                RapidNodeReferenceMode.FULL_PSEUDONYM_128
            ),
            node_count=4,
        )
        indexed = compare_rapid_wire_cost(
            rapid,
            baseline=epidemic,
            control=indexed_control,
        )
        full = compare_rapid_wire_cost(
            rapid,
            baseline=epidemic,
            control=full_control,
        )

        # Shared-index bootstrap is campaign state: object count must not silently
        # multiply its one canonical representation.
        indexed_bootstrap.append(indexed_control.bootstrap_wire_bytes)
        assert full_control.bootstrap_wire_bytes == 0
        assert indexed.governed_transfer_savings_before_control == (
            epidemic.total_wire_bytes - rapid.total_wire_bytes_excluding_rapid_control
        )
        assert full.governed_transfer_savings_before_control == indexed.governed_transfer_savings_before_control
        indexed_deltas.append(indexed.delta_vs_baseline_bytes)
        queue_entries.append(indexed_control.queue_quote_entry_count)

    assert indexed_bootstrap == [76] * len(checkpoints)
    # The current one-selection prototype evaluates every still-eligible object
    # on each A->B encounter. This is deliberately observed rather than hidden:
    # per-object queue/control work may grow faster than the shared bootstrap.
    assert queue_entries == sorted(queue_entries)
    assert queue_entries[-1] > checkpoints[-1]
    # This experiment maps the regime; it does not require RAPID to win at every
    # object count. A sign change is a result, not a test failure.
    assert len(indexed_deltas) == len(checkpoints)


def test_shared_opportunity_quote_replaces_triangular_per_bundle_quotes() -> None:
    checkpoints = (1, 2, 5, 10, 20)
    current_entries = []
    shared_entries = []

    for object_count in checkpoints:
        rapid, epidemic = _run(object_count)
        profile = RapidControlWireProfile(
            RapidNodeReferenceMode.SHARED_U16_INDEX
        )
        shared = account_shared_opportunity_quotes(
            rapid,
            profile=profile,
            node_count=4,
        )
        current_entries.append(shared.original_queue_quote_entry_count)
        shared_entries.append(shared.shared_queue_quote_entry_count)

        # In this controlled micro-object workload every candidate object is 64 B
        # and B's explicitly observed B->D opportunity mean remains 64 B. One
        # shared opportunity quote is therefore sufficient to reproduce the
        # current isolated-service meetings-needed value for every candidate.
        expected_meetings = meetings_needed_from_shared_opportunity_quote(
            OBJECT_BYTES,
            mean_opportunity_bytes=OBJECT_BYTES,
        )
        assert expected_meetings == 1
        for window in rapid.windows:
            if window.encounter.candidate_queue_quote_count <= 0:
                continue
            for inference in window.encounter.inferences:
                if inference.candidate_replica_estimate is not None:
                    assert inference.candidate_replica_estimate.meetings_needed == expected_meetings

        # Only the quote representation changes. Governed Pollicino transfer
        # bytes and the routing/delivery result are exactly the same.
        assert rapid.routing.delivered_bundle_count == epidemic.delivered_bundle_count == object_count
        assert rapid_modeled_total_with_shared_opportunity_quotes(
            rapid,
            control=shared,
        ) == (
            rapid.total_wire_bytes_excluding_rapid_control
            + shared.modeled_control_wire_bytes
        )

    assert current_entries == [count * (count + 1) // 2 for count in checkpoints]
    assert shared_entries == list(checkpoints)
