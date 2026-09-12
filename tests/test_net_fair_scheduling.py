import hashlib

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bearer import BearerKind, BearerProfile, EvidenceBasis
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.fair_scheduling import (
    BearerSchedulingPolicy,
    FairSchedulerState,
    FairnessPolicy,
    load_fair_scheduler_state,
    save_fair_scheduler_state,
    schedule_fair_bearer_contact,
    schedule_fair_contact_bundles,
)
from pollicino.net.scheduling import BundlePriority, ContactSchedulingPolicy, ScheduledBundle
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


def link_profile(seed: int = 41) -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=seed,
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
    manifest = seed_forwarding_object(
        data_for(label, chunks), chunk_size=64, store=origin.store
    )
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=f"fair-{label}".encode(),
        ttl_seconds=ttl,
        hop_limit=4,
        nonce=nonce,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    seed_bundle_custody(bundle, manifest, origin=origin, ledger=ledger, now_s=1000)
    return ScheduledBundle(bundle=bundle, manifest=manifest, priority=priority, label=label)


def contact_policy(budget: int) -> ContactSchedulingPolicy:
    return ContactSchedulingPolicy(
        max_source_bytes=budget,
        max_bundles=10,
        max_chunks_per_bundle=10,
    )


def fairness() -> FairnessPolicy:
    return FairnessPolicy(
        starvation_seconds=10,
        max_rescue_bundles=1,
        rescue_chunks_per_bundle=1,
    )


def test_starved_bulk_gets_rescue_before_new_emergency() -> None:
    origin = ForwardPeer("origin", PollicinoStore())
    target = ForwardPeer("target", PollicinoStore())
    ledger = CustodyLedger()
    state = FairSchedulerState()

    bulk = make_item(
        "bulk", priority=BundlePriority.BULK, ttl=200, chunks=1,
        origin=origin, ledger=ledger, nonce=1,
    )
    emergency_1 = make_item(
        "emergency-1", priority=BundlePriority.EMERGENCY, ttl=200, chunks=1,
        origin=origin, ledger=ledger, nonce=2,
    )
    emergency_2 = make_item(
        "emergency-2", priority=BundlePriority.EMERGENCY, ttl=200, chunks=1,
        origin=origin, ledger=ledger, nonce=3,
    )

    first = schedule_fair_contact_bundles(
        [bulk, emergency_1],
        source=origin,
        target=target,
        ledger=ledger,
        state=state,
        profile=link_profile(),
        transfer_id_base=100,
        encounter_id="fair-1",
        now_s=1001,
        policy=contact_policy(64),
        fairness=fairness(),
    )
    assert [item.label for item in first.decisions] == ["emergency-1"]
    bulk_record = state.get(bulk.bundle.bundle_id.hex())
    assert bulk_record is not None
    assert bulk_record.eligible_since_s == 1001
    assert bulk_record.deferral_count == 1

    second = schedule_fair_contact_bundles(
        [bulk, emergency_2],
        source=origin,
        target=target,
        ledger=ledger,
        state=state,
        profile=link_profile(),
        transfer_id_base=200,
        encounter_id="fair-2",
        now_s=1012,
        policy=contact_policy(64),
        fairness=fairness(),
    )

    assert [item.label for item in second.decisions] == ["bulk"]
    assert second.rescued_bundle_ids == (bulk.bundle.bundle_id.hex(),)
    assert second.used_source_bytes == 64
    assert state.get(bulk.bundle.bundle_id.hex()).service_count == 1


def test_persistent_wait_age_survives_restart(tmp_path) -> None:
    origin = ForwardPeer("origin", PollicinoStore())
    target = ForwardPeer("target", PollicinoStore())
    ledger = CustodyLedger()
    state = FairSchedulerState()

    bulk = make_item(
        "persistent-bulk", priority=BundlePriority.BULK, ttl=300, chunks=1,
        origin=origin, ledger=ledger, nonce=4,
    )
    emergency_1 = make_item(
        "persistent-emergency-1", priority=BundlePriority.EMERGENCY, ttl=300, chunks=1,
        origin=origin, ledger=ledger, nonce=5,
    )
    emergency_2 = make_item(
        "persistent-emergency-2", priority=BundlePriority.EMERGENCY, ttl=300, chunks=1,
        origin=origin, ledger=ledger, nonce=6,
    )

    schedule_fair_contact_bundles(
        [bulk, emergency_1],
        source=origin,
        target=target,
        ledger=ledger,
        state=state,
        profile=link_profile(),
        transfer_id_base=300,
        encounter_id="persist-fair-1",
        now_s=1001,
        policy=contact_policy(64),
        fairness=fairness(),
    )

    checkpoint = tmp_path / "fair-scheduler.json"
    save_fair_scheduler_state(checkpoint, state)
    restored = load_fair_scheduler_state(checkpoint)
    assert restored.get(bulk.bundle.bundle_id.hex()).eligible_since_s == 1001

    report = schedule_fair_contact_bundles(
        [bulk, emergency_2],
        source=origin,
        target=target,
        ledger=ledger,
        state=restored,
        profile=link_profile(),
        transfer_id_base=400,
        encounter_id="persist-fair-2",
        now_s=1012,
        policy=contact_policy(64),
        fairness=fairness(),
    )
    assert report.decisions[0].label == "persistent-bulk"
    assert report.rescued_bundle_ids == (bulk.bundle.bundle_id.hex(),)


def test_duplicate_encounter_is_zero_wire_and_does_not_age_state() -> None:
    origin = ForwardPeer("origin", PollicinoStore())
    target = ForwardPeer("target", PollicinoStore())
    ledger = CustodyLedger()
    state = FairSchedulerState()
    item = make_item(
        "duplicate", priority=BundlePriority.NORMAL, ttl=100, chunks=2,
        origin=origin, ledger=ledger, nonce=7,
    )

    first = schedule_fair_contact_bundles(
        [item],
        source=origin,
        target=target,
        ledger=ledger,
        state=state,
        profile=link_profile(),
        transfer_id_base=500,
        encounter_id="same-encounter",
        now_s=1001,
        policy=contact_policy(64),
        fairness=fairness(),
    )
    before = state.get(item.bundle.bundle_id.hex())
    duplicate = schedule_fair_contact_bundles(
        [item],
        source=origin,
        target=target,
        ledger=ledger,
        state=state,
        profile=link_profile(),
        transfer_id_base=600,
        encounter_id="same-encounter",
        now_s=1050,
        policy=contact_policy(64),
        fairness=fairness(),
    )
    after = state.get(item.bundle.bundle_id.hex())

    assert first.used_source_bytes == 64
    assert duplicate.duplicate_encounter
    assert duplicate.total_wire_bytes == 0
    assert duplicate.used_source_bytes == 0
    assert after == before


def test_bearer_specific_policies_use_explicit_logical_budgets() -> None:
    origin = ForwardPeer("origin", PollicinoStore())
    lora_target = ForwardPeer("lora-target", PollicinoStore())
    wifi_target = ForwardPeer("wifi-target", PollicinoStore())
    ledger = CustodyLedger()
    item = make_item(
        "multi-bearer", priority=BundlePriority.NORMAL, ttl=200, chunks=3,
        origin=origin, ledger=ledger, nonce=8,
    )

    lora = BearerProfile(
        bearer_id="lab-lora",
        kind=BearerKind.LORA,
        evidence_basis=EvidenceBasis.SYNTHETIC,
        link_profile=link_profile(seed=51),
    )
    wifi = BearerProfile(
        bearer_id="lab-wifi",
        kind=BearerKind.WIFI,
        evidence_basis=EvidenceBasis.SYNTHETIC,
        link_profile=link_profile(seed=52),
    )
    lora_policy = BearerSchedulingPolicy(
        bearer_id="lab-lora",
        contact_policy=contact_policy(64),
        fairness_policy=fairness(),
    )
    wifi_policy = BearerSchedulingPolicy(
        bearer_id="lab-wifi",
        contact_policy=contact_policy(192),
        fairness_policy=fairness(),
    )

    lora_report = schedule_fair_bearer_contact(
        [item],
        source=origin,
        target=lora_target,
        ledger=ledger,
        state=FairSchedulerState(),
        bearer=lora,
        policy=lora_policy,
        transfer_id_base=700,
        encounter_id="lora-contact",
        now_s=1001,
    )
    wifi_report = schedule_fair_bearer_contact(
        [item],
        source=origin,
        target=wifi_target,
        ledger=ledger,
        state=FairSchedulerState(),
        bearer=wifi,
        policy=wifi_policy,
        transfer_id_base=800,
        encounter_id="wifi-contact",
        now_s=1001,
    )

    assert lora_report.kind is BearerKind.LORA
    assert wifi_report.kind is BearerKind.WIFI
    assert lora_report.scheduling.used_source_bytes == 64
    assert wifi_report.scheduling.used_source_bytes == 192
    assert not lora_report.logical_budget_is_measured_capacity
    assert not wifi_report.logical_budget_is_measured_capacity
    assert lora_report.profile_evidence_basis is EvidenceBasis.SYNTHETIC
    assert wifi_report.profile_evidence_basis is EvidenceBasis.SYNTHETIC


def test_measured_profile_does_not_upgrade_policy_budget_to_physical_capacity() -> None:
    origin = ForwardPeer("origin", PollicinoStore())
    target = ForwardPeer("target", PollicinoStore())
    ledger = CustodyLedger()
    item = make_item(
        "measured-profile", priority=BundlePriority.HIGH, ttl=200, chunks=1,
        origin=origin, ledger=ledger, nonce=9,
    )
    measured = BearerProfile(
        bearer_id="measured-lora",
        kind=BearerKind.LORA,
        evidence_basis=EvidenceBasis.MEASURED,
        provenance="HW-006 future checkpoint example",
        link_profile=link_profile(seed=53),
    )
    policy = BearerSchedulingPolicy(
        bearer_id="measured-lora",
        contact_policy=contact_policy(64),
        fairness_policy=fairness(),
    )

    report = schedule_fair_bearer_contact(
        [item],
        source=origin,
        target=target,
        ledger=ledger,
        state=FairSchedulerState(),
        bearer=measured,
        policy=policy,
        transfer_id_base=900,
        encounter_id="measured-profile-contact",
        now_s=1001,
    )

    assert report.profile_evidence_basis is EvidenceBasis.MEASURED
    assert report.profile_provenance == "HW-006 future checkpoint example"
    assert not report.logical_budget_is_measured_capacity
    assert not report.contains_physical_replay
