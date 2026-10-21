import hashlib

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.scheduling import (
    BundlePriority,
    ContactSchedulingPolicy,
    ScheduledBundle,
    schedule_contact_bundles,
)
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


def profile() -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=29,
    )


def data_for(label: str, chunks: int, size: int = 64) -> bytes:
    pieces = []
    for index in range(chunks):
        digest = hashlib.sha256(f"{label}-{index}".encode()).digest()
        pieces.append((digest * ((size + 31) // 32))[:size])
    return b"".join(pieces)


def make_item(
    label: str,
    *,
    priority: BundlePriority,
    ttl: int,
    chunks: int,
    origin: ForwardPeer,
    ledger: CustodyLedger,
    nonce: int,
) -> ScheduledBundle:
    data = data_for(label, chunks)
    manifest = seed_forwarding_object(data, chunk_size=64, store=origin.store)
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=f"schedule-{label}".encode(),
        ttl_seconds=ttl,
        hop_limit=3,
        nonce=nonce,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    seed_bundle_custody(bundle, manifest, origin=origin, ledger=ledger, now_s=1000)
    return ScheduledBundle(bundle=bundle, manifest=manifest, priority=priority, label=label)


def policy(*, budget: int, bundles: int = 10, chunks: int = 10) -> ContactSchedulingPolicy:
    return ContactSchedulingPolicy(
        max_source_bytes=budget,
        max_bundles=bundles,
        max_chunks_per_bundle=chunks,
    )


def test_emergency_is_sent_before_lower_priority() -> None:
    origin = ForwardPeer("origin", PollicinoStore())
    target = ForwardPeer("target", PollicinoStore())
    ledger = CustodyLedger()
    normal = make_item(
        "normal", priority=BundlePriority.NORMAL, ttl=20, chunks=1,
        origin=origin, ledger=ledger, nonce=1,
    )
    emergency = make_item(
        "emergency", priority=BundlePriority.EMERGENCY, ttl=100, chunks=1,
        origin=origin, ledger=ledger, nonce=2,
    )

    report = schedule_contact_bundles(
        [normal, emergency],
        source=origin,
        target=target,
        ledger=ledger,
        profile=profile(),
        transfer_id_base=100,
        encounter_id="enc-priority",
        now_s=1001,
        policy=policy(budget=64, bundles=1),
    )

    assert [item.label for item in report.decisions] == ["emergency"]
    assert report.used_source_bytes == 64
    assert report.emergency_bundle_count == 1


def test_same_priority_prefers_bundle_closer_to_expiry() -> None:
    origin = ForwardPeer("origin", PollicinoStore())
    target = ForwardPeer("target", PollicinoStore())
    ledger = CustodyLedger()
    later = make_item(
        "later", priority=BundlePriority.HIGH, ttl=100, chunks=1,
        origin=origin, ledger=ledger, nonce=3,
    )
    sooner = make_item(
        "sooner", priority=BundlePriority.HIGH, ttl=10, chunks=1,
        origin=origin, ledger=ledger, nonce=4,
    )

    report = schedule_contact_bundles(
        [later, sooner],
        source=origin,
        target=target,
        ledger=ledger,
        profile=profile(),
        transfer_id_base=200,
        encounter_id="enc-expiry",
        now_s=1001,
        policy=policy(budget=64, bundles=1),
    )

    assert report.decisions[0].label == "sooner"
    assert report.decisions[0].seconds_to_expiry == 9


def test_same_priority_and_expiry_prefers_completable_smaller_object() -> None:
    origin = ForwardPeer("origin", PollicinoStore())
    target = ForwardPeer("target", PollicinoStore())
    ledger = CustodyLedger()
    large = make_item(
        "large", priority=BundlePriority.NORMAL, ttl=100, chunks=3,
        origin=origin, ledger=ledger, nonce=5,
    )
    small = make_item(
        "small", priority=BundlePriority.NORMAL, ttl=100, chunks=1,
        origin=origin, ledger=ledger, nonce=6,
    )

    report = schedule_contact_bundles(
        [large, small],
        source=origin,
        target=target,
        ledger=ledger,
        profile=profile(),
        transfer_id_base=300,
        encounter_id="enc-complete",
        now_s=1001,
        policy=policy(budget=64, bundles=1),
    )

    decision = report.decisions[0]
    assert decision.label == "small"
    assert decision.would_complete_target
    assert decision.selected_source_bytes == 64


def test_scheduler_never_exceeds_logical_source_byte_budget() -> None:
    origin = ForwardPeer("origin", PollicinoStore())
    target = ForwardPeer("target", PollicinoStore())
    ledger = CustodyLedger()
    emergency = make_item(
        "emergency-two", priority=BundlePriority.EMERGENCY, ttl=100, chunks=2,
        origin=origin, ledger=ledger, nonce=7,
    )
    normal = make_item(
        "normal-two", priority=BundlePriority.NORMAL, ttl=100, chunks=2,
        origin=origin, ledger=ledger, nonce=8,
    )

    report = schedule_contact_bundles(
        [normal, emergency],
        source=origin,
        target=target,
        ledger=ledger,
        profile=profile(),
        transfer_id_base=400,
        encounter_id="enc-budget",
        now_s=1001,
        policy=policy(budget=96, bundles=10),
    )

    # With 64-byte chunks only one complete chunk fits. The remaining 32-byte
    # logical budget is left unused rather than overshooting it.
    assert report.used_source_bytes == 64
    assert report.remaining_source_bytes == 32
    assert len(report.decisions) == 1
    assert report.decisions[0].priority is BundlePriority.EMERGENCY


def test_expired_and_non_custodied_bundles_are_skipped_without_wire() -> None:
    origin = ForwardPeer("origin", PollicinoStore())
    target = ForwardPeer("target", PollicinoStore())
    ledger = CustodyLedger()
    expired = make_item(
        "expired", priority=BundlePriority.EMERGENCY, ttl=1, chunks=1,
        origin=origin, ledger=ledger, nonce=9,
    )

    other_origin = ForwardPeer("other", PollicinoStore())
    other_ledger = CustodyLedger()
    no_custody = make_item(
        "no-custody", priority=BundlePriority.HIGH, ttl=100, chunks=1,
        origin=other_origin, ledger=other_ledger, nonce=10,
    )

    report = schedule_contact_bundles(
        [expired, no_custody],
        source=origin,
        target=target,
        ledger=ledger,
        profile=profile(),
        transfer_id_base=500,
        encounter_id="enc-skip",
        now_s=1001,
        policy=policy(budget=128),
    )

    assert report.decisions == ()
    assert expired.bundle.bundle_id.hex() in report.skipped_expired_bundle_ids
    assert no_custody.bundle.bundle_id.hex() in report.skipped_no_custody_bundle_ids
    assert report.total_wire_bytes == 0
