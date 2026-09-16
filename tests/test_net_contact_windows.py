import hashlib

import pytest

from pollicino.net import PollicinoStore, ScarceLinkProfile
from pollicino.net.bearer import BearerKind, BearerProfile, EvidenceBasis
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.contact_windows import (
    SyntheticContactWindow,
    run_synthetic_contact_windows,
)
from pollicino.net.fair_scheduling import (
    BearerSchedulingPolicy,
    FairSchedulerState,
    FairnessPolicy,
)
from pollicino.net.scheduling import BundlePriority, ContactSchedulingPolicy, ScheduledBundle
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


def link_profile(seed: int) -> ScarceLinkProfile:
    return ScarceLinkProfile(
        max_frame_bytes=64,
        bitrate_bps=5000,
        ack_bytes=8,
        max_retries=3,
        seed=seed,
    )


def make_bundle(
    label: str,
    *,
    chunks: int,
    origin: ForwardPeer,
    ledger: CustodyLedger,
    nonce: int,
    priority: BundlePriority = BundlePriority.NORMAL,
) -> ScheduledBundle:
    pieces = []
    for index in range(chunks):
        digest = hashlib.sha256(f"{label}-{index}".encode()).digest()
        pieces.append((digest * 2)[:64])
    data = b"".join(pieces)
    manifest = seed_forwarding_object(data, chunk_size=64, store=origin.store)
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=f"window-{label}".encode(),
        ttl_seconds=1000,
        hop_limit=5,
        nonce=nonce,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    seed_bundle_custody(bundle, manifest, origin=origin, ledger=ledger, now_s=1000)
    return ScheduledBundle(bundle=bundle, manifest=manifest, priority=priority, label=label)


def bearer(bearer_id: str, kind: BearerKind, seed: int) -> BearerProfile:
    return BearerProfile(
        bearer_id=bearer_id,
        kind=kind,
        evidence_basis=EvidenceBasis.SYNTHETIC,
        link_profile=link_profile(seed),
    )


def policy(bearer_id: str) -> BearerSchedulingPolicy:
    # The per-window explicit logical budget overrides max_source_bytes below.
    return BearerSchedulingPolicy(
        bearer_id=bearer_id,
        contact_policy=ContactSchedulingPolicy(
            max_source_bytes=9999,
            max_bundles=10,
            max_chunks_per_bundle=10,
        ),
        fairness_policy=FairnessPolicy(
            starvation_seconds=30,
            max_rescue_bundles=1,
            rescue_chunks_per_bundle=1,
        ),
    )


def test_synthetic_multi_relay_chain_reaches_destination_without_direct_path() -> None:
    peers = {
        name: ForwardPeer(name, PollicinoStore())
        for name in ("A", "B", "C", "D")
    }
    ledger = CustodyLedger()
    item = make_bundle("messina-chain", chunks=2, origin=peers["A"], ledger=ledger, nonce=1)

    bearers = {
        "lora-lab": bearer("lora-lab", BearerKind.LORA, 61),
        "wifi-lab": bearer("wifi-lab", BearerKind.WIFI, 62),
    }
    policies = {
        "lora-lab": policy("lora-lab"),
        "wifi-lab": policy("wifi-lab"),
    }
    windows = [
        SyntheticContactWindow(
            encounter_id="A-B-morning",
            source_id="A",
            target_id="B",
            bearer_id="lora-lab",
            start_s=1001,
            duration_seconds=8,
            logical_source_byte_budget=128,
            transfer_id_base=100,
        ),
        SyntheticContactWindow(
            encounter_id="B-C-noon",
            source_id="B",
            target_id="C",
            bearer_id="lora-lab",
            start_s=1010,
            duration_seconds=30,
            logical_source_byte_budget=128,
            transfer_id_base=200,
        ),
        SyntheticContactWindow(
            encounter_id="C-D-evening",
            source_id="C",
            target_id="D",
            bearer_id="wifi-lab",
            start_s=1020,
            duration_seconds=3,
            logical_source_byte_budget=128,
            transfer_id_base=300,
        ),
    ]
    states: dict[str, FairSchedulerState] = {}

    report = run_synthetic_contact_windows(
        [item],
        peers=peers,
        ledger=ledger,
        windows=windows,
        bearers=bearers,
        scheduling_policies=policies,
        scheduler_states=states,
    )

    propagation = report.propagation_for_label("messina-chain")
    assert propagation.complete_peer_ids == ("A", "B", "C", "D")
    assert all(window.used_source_bytes == 128 for window in report.windows)
    assert all(not window.duration_drives_budget for window in report.windows)
    assert report.total_logical_source_byte_budget == 384
    assert report.used_source_bytes == 384
    assert report.utilization == 1.0
    assert set(states) == {"A", "B", "C"}
    assert all(
        not (window.source_id == "A" and window.target_id == "D")
        for window in report.windows
    )


def test_window_budget_overrides_bearer_base_policy_independently_of_duration() -> None:
    peers = {
        "A": ForwardPeer("A", PollicinoStore()),
        "B": ForwardPeer("B", PollicinoStore()),
        "C": ForwardPeer("C", PollicinoStore()),
    }
    ledger = CustodyLedger()
    first = make_bundle("budget-one", chunks=1, origin=peers["A"], ledger=ledger, nonce=2)
    second = make_bundle("budget-two", chunks=1, origin=peers["A"], ledger=ledger, nonce=3)
    lora = bearer("lora", BearerKind.LORA, 63)

    report = run_synthetic_contact_windows(
        [first, second],
        peers=peers,
        ledger=ledger,
        windows=[
            SyntheticContactWindow(
                encounter_id="short-large-duration",
                source_id="A",
                target_id="B",
                bearer_id="lora",
                start_s=1001,
                duration_seconds=120,
                logical_source_byte_budget=64,
                transfer_id_base=400,
            ),
            SyntheticContactWindow(
                encounter_id="larger-small-duration",
                source_id="A",
                target_id="C",
                bearer_id="lora",
                start_s=1002,
                duration_seconds=1,
                logical_source_byte_budget=128,
                transfer_id_base=500,
            ),
        ],
        bearers={"lora": lora},
        scheduling_policies={"lora": policy("lora")},
        scheduler_states={},
    )

    assert report.windows[0].duration_seconds == 120
    assert report.windows[0].used_source_bytes == 64
    assert report.windows[1].duration_seconds == 1
    assert report.windows[1].used_source_bytes == 128
    assert not report.windows[0].duration_drives_budget
    assert not report.windows[1].duration_drives_budget


def test_duplicate_synthetic_window_ids_are_rejected() -> None:
    peers = {
        "A": ForwardPeer("A", PollicinoStore()),
        "B": ForwardPeer("B", PollicinoStore()),
    }
    ledger = CustodyLedger()
    item = make_bundle("duplicate-window", chunks=1, origin=peers["A"], ledger=ledger, nonce=4)
    lora = bearer("lora", BearerKind.LORA, 64)
    repeated = SyntheticContactWindow(
        encounter_id="same",
        source_id="A",
        target_id="B",
        bearer_id="lora",
        start_s=1001,
        duration_seconds=10,
        logical_source_byte_budget=64,
        transfer_id_base=600,
    )

    with pytest.raises(ValueError, match="encounter IDs must be unique"):
        run_synthetic_contact_windows(
            [item],
            peers=peers,
            ledger=ledger,
            windows=[repeated, repeated],
            bearers={"lora": lora},
            scheduling_policies={"lora": policy("lora")},
            scheduler_states={},
        )
