import hashlib

from pollicino.net import PollicinoStore
from pollicino.net.destination_queue_service import (
    estimate_destination_queue_service,
    queue_service_prefers_target,
)
from pollicino.net.destination_service import (
    DestinationServiceObservation,
    DestinationServiceStrategy,
)
from pollicino.net.rapid_deadline_utility import (
    RapidReplicaEstimate,
    rapid_deadline_marginal_utility,
)
from pollicino.net.rapid_queue_inference import (
    RapidQueueEntry,
    estimate_queue_service_meetings,
)
from pollicino.net.scheduling import BundlePriority, ScheduledBundle
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.wire import DiscoveryDescriptor


OBJECT_BYTES = 64
OPPORTUNITY_BYTES = 64
MEAN_INTERVAL_S = 50.0
DEADLINE_REMAINING_S = 120.0


def _bundle() -> ScheduledBundle:
    origin = ForwardPeer("a", PollicinoStore())
    ledger = CustodyLedger()
    payload = hashlib.sha256(b"queue-target").digest() * 2
    manifest = seed_forwarding_object(
        payload[:OBJECT_BYTES],
        chunk_size=OBJECT_BYTES,
        store=origin.store,
    )
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=b"queue-target",
        ttl_seconds=1000,
        hop_limit=8,
        nonce=2026082801,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    seed_bundle_custody(bundle, manifest, origin=origin, ledger=ledger, now_s=1000)
    return ScheduledBundle(
        bundle=bundle,
        manifest=manifest,
        priority=BundlePriority.NORMAL,
        label="queue-sensitive-reference",
    )


def _service_strategy() -> DestinationServiceStrategy:
    return DestinationServiceStrategy(
        destination_id="d",
        prior_observations=(
            # A and C are deliberately indistinguishable to Destination Service:
            # both have 50 s direct inter-meeting interval and 64 B mean useful
            # destination opportunity.
            DestinationServiceObservation("a", "d", 0, OPPORTUNITY_BYTES),
            DestinationServiceObservation("a", "d", 50, OPPORTUNITY_BYTES),
            DestinationServiceObservation("c", "d", 0, OPPORTUNITY_BYTES),
            DestinationServiceObservation("c", "d", 50, OPPORTUNITY_BYTES),
        ),
    )


def test_destination_service_cannot_distinguish_equal_service_with_different_backlog() -> None:
    item = _bundle()
    service = _service_strategy()

    # Prime the research strategy state using its explicit historical observations.
    # The public service_seconds() view is enough for this discriminator; no
    # future contact schedule is supplied as oracle knowledge.
    ledger = CustodyLedger()
    service._ensure_run(ledger, now_s=1000)  # research-only white-box gate test

    source_service = service.service_seconds(item, "a")
    candidate_service = service.service_seconds(item, "c")
    assert source_service == candidate_service == MEAN_INTERVAL_S

    # DestinationServiceStrategy forwards only on strictly smaller service time;
    # equal interval/opportunity therefore provides no reason to prefer C.
    assert not (candidate_service < source_service)


def test_explicit_queue_backlog_makes_equal_service_carriers_materially_different() -> None:
    item = _bundle()
    target_id = item.bundle.bundle_id

    # A has four 64-byte objects ahead of the target; C has an empty queue ahead.
    a_queue = tuple(
        RapidQueueEntry(hashlib.sha256(f"ahead-{i}".encode()).digest(), OBJECT_BYTES)
        for i in range(4)
    ) + (RapidQueueEntry(target_id, OBJECT_BYTES),)
    c_queue = (RapidQueueEntry(target_id, OBJECT_BYTES),)

    a_estimate = estimate_queue_service_meetings(
        a_queue,
        bundle_id=target_id,
        expected_transfer_bytes_per_meeting=OPPORTUNITY_BYTES,
    )
    c_estimate = estimate_queue_service_meetings(
        c_queue,
        bundle_id=target_id,
        expected_transfer_bytes_per_meeting=OPPORTUNITY_BYTES,
    )

    assert a_estimate.bytes_ahead == 4 * OBJECT_BYTES
    assert a_estimate.meetings_needed == 5
    assert c_estimate.bytes_ahead == 0
    assert c_estimate.meetings_needed == 1

    existing = RapidReplicaEstimate(
        carrier_id="a",
        mean_direct_meeting_seconds=MEAN_INTERVAL_S,
        meetings_needed=a_estimate.meetings_needed,
    )
    candidate = RapidReplicaEstimate(
        carrier_id="c",
        mean_direct_meeting_seconds=MEAN_INTERVAL_S,
        meetings_needed=c_estimate.meetings_needed,
    )
    utility = rapid_deadline_marginal_utility(
        remaining_useful_seconds=DEADLINE_REMAINING_S,
        existing_replicas=(existing,),
        candidate_replica=candidate,
        transfer_bytes=OBJECT_BYTES,
    )

    assert utility.marginal_utility > 0
    assert utility.marginal_utility_per_byte > 0
    assert utility.probability_after > utility.probability_before


def test_minimal_queue_aware_service_baseline_captures_same_discriminator() -> None:
    source = estimate_destination_queue_service(
        mean_interval_seconds=MEAN_INTERVAL_S,
        mean_opportunity_bytes=OPPORTUNITY_BYTES,
        bytes_ahead=4 * OBJECT_BYTES,
        object_bytes=OBJECT_BYTES,
    )
    target = estimate_destination_queue_service(
        mean_interval_seconds=MEAN_INTERVAL_S,
        mean_opportunity_bytes=OPPORTUNITY_BYTES,
        bytes_ahead=0,
        object_bytes=OBJECT_BYTES,
    )

    assert source.meetings_needed == 5
    assert source.service_seconds == 250.0
    assert target.meetings_needed == 1
    assert target.service_seconds == 50.0
    assert queue_service_prefers_target(source=source, target=target)


def test_queue_backlog_is_the_only_discriminator_in_this_gate() -> None:
    item = _bundle()
    service = _service_strategy()
    ledger = CustodyLedger()
    service._ensure_run(ledger, now_s=1000)  # research-only white-box gate test

    assert service.mean_interval_seconds("a") == service.mean_interval_seconds("c") == MEAN_INTERVAL_S
    assert service.mean_opportunity_bytes("a") == service.mean_opportunity_bytes("c") == OPPORTUNITY_BYTES
    assert service.service_seconds(item, "a") == service.service_seconds(item, "c")

    # No bearer label, contact duration, recency advantage or future window is
    # used to distinguish A and C. Only explicit bytes-ahead changes the queue
    # service estimate.
