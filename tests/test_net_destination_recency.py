import hashlib

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bearer import BearerKind, BearerProfile, EvidenceBasis
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.contact_windows import SyntheticContactWindow
from pollicino.net.destination_recency import (
    DestinationRecencyControlProfile,
    DestinationRecencyNodeReferenceMode,
    DestinationRecencyObservation,
    DestinationRecencyStrategy,
    account_destination_recency_control,
)
from pollicino.net.fair_scheduling import BearerSchedulingPolicy, FairnessPolicy
from pollicino.net.routing_baselines import EpidemicStrategy
from pollicino.net.routing_compare import compare_synthetic_routing_strategies
from pollicino.net.scheduling import BundlePriority, ContactSchedulingPolicy, ScheduledBundle
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


OBJECT_BYTES = 64


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
            seed=161,
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


def _build(object_count: int):
    peers = {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in ("a", "x", "b", "d")
    }
    ledger = CustodyLedger()
    bundles = []
    for index in range(object_count):
        digest = hashlib.sha256(f"recency-{index}".encode()).digest()
        payload = (digest * 2)[:OBJECT_BYTES]
        manifest = seed_forwarding_object(
            payload,
            chunk_size=OBJECT_BYTES,
            store=peers["a"].store,
        )
        descriptor = DiscoveryDescriptor(
            object_class=1,
            rendezvous_key=hashlib.sha256(f"recency-{index}".encode()).digest()[:16],
            ttl_seconds=5000,
            hop_limit=16,
            nonce=index + 1,
        )
        bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
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
    return peers, ledger, tuple(bundles), tuple(windows)


def _run(object_count: int):
    peers, ledger, bundles, windows = _build(object_count)
    recency = DestinationRecencyStrategy(
        destination_id="d",
        prior_observations=(
            DestinationRecencyObservation("a", "d", 900),
            DestinationRecencyObservation("b", "d", 940),
        ),
    )
    bearer = _bearer()
    policy = _policy()
    comparison = compare_synthetic_routing_strategies(
        (recency, EpidemicStrategy()),
        bundles,
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers={"lora": bearer},
        scheduling_policies={"lora": policy},
        scheduler_states={},
        destination_ids=("d",),
    )
    return recency, comparison.strategy("destination-recency"), comparison.strategy("epidemic")


def test_destination_recency_matches_useful_path_without_rich_routing_state() -> None:
    recency, simple, epidemic = _run(1)

    assert simple.delivered_bundle_count == epidemic.delivered_bundle_count == 1
    assert simple.used_source_bytes == 2 * OBJECT_BYTES
    assert epidemic.used_source_bytes == 3 * OBJECT_BYTES
    assert simple.windows[0].scheduling is None  # A->X skipped
    assert simple.windows[1].scheduling is not None  # A->B selected
    assert simple.windows[2].scheduling is not None  # B->D direct
    assert recency.last_destination_encounter_s("b") == 1020
    assert recency.quote_entry_count == 2


def test_destination_recency_control_stays_linear_for_many_micro_objects() -> None:
    checkpoints = (1, 2, 5, 10, 20)
    quote_counts = []

    for object_count in checkpoints:
        strategy, simple, epidemic = _run(object_count)
        assert simple.delivered_bundle_count == epidemic.delivered_bundle_count == object_count
        assert simple.used_source_bytes == 2 * object_count * OBJECT_BYTES
        assert epidemic.used_source_bytes == 3 * object_count * OBJECT_BYTES

        indexed = account_destination_recency_control(
            strategy,
            profile=DestinationRecencyControlProfile(
                DestinationRecencyNodeReferenceMode.SHARED_U16_INDEX
            ),
            node_count=4,
        )
        full = account_destination_recency_control(
            strategy,
            profile=DestinationRecencyControlProfile(
                DestinationRecencyNodeReferenceMode.FULL_PSEUDONYM_128
            ),
            node_count=4,
        )
        quote_counts.append(indexed.quote_entry_count)

        # Same useful forwarding pattern as the richer prototype, but the only
        # modeled routing state is one target recency quote per non-destination
        # directed encounter. Both reference encodings remain cheaper than
        # Epidemic on this controlled workload even after control accounting.
        assert simple.total_wire_bytes + indexed.control_wire_bytes < epidemic.total_wire_bytes
        assert simple.total_wire_bytes + full.control_wire_bytes < epidemic.total_wire_bytes

    assert quote_counts == [count + 1 for count in checkpoints]
