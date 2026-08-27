import hashlib

import pytest

from pollicino.net import PollicinoStore
from pollicino.net.bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from pollicino.net.contact_windows import SyntheticContactWindow
from pollicino.net.rapid_encounter import (
    RapidEncounterPrototypeState,
    evaluate_rapid_encounter,
)
from pollicino.net.scheduling import BundlePriority, ScheduledBundle
from pollicino.net.store_forward import ForwardPeer, seed_forwarding_object
from pollicino.net.wire import DiscoveryDescriptor


def _data(label: str, size: int) -> bytes:
    digest = hashlib.sha256(label.encode()).digest()
    return (digest * ((size + len(digest) - 1) // len(digest)))[:size]


def _bundle(
    label: str,
    *,
    size: int,
    origin: ForwardPeer,
    ledger: CustodyLedger,
    nonce: int,
) -> ScheduledBundle:
    manifest = seed_forwarding_object(
        _data(label, size),
        chunk_size=64,
        store=origin.store,
    )
    descriptor = DiscoveryDescriptor(
        object_class=1,
        rendezvous_key=hashlib.sha256(f"rapid-encounter-{label}".encode()).digest()[:16],
        ttl_seconds=2000,
        hop_limit=16,
        nonce=nonce,
    )
    bundle = ForwardBundle.from_descriptor(manifest, descriptor, created_at_s=1000)
    seed_bundle_custody(bundle, manifest, origin=origin, ledger=ledger, now_s=1000)
    return ScheduledBundle(
        bundle=bundle,
        manifest=manifest,
        priority=BundlePriority.NORMAL,
        label=label,
    )


def _peers(*peer_ids: str) -> dict[str, ForwardPeer]:
    return {
        peer_id: ForwardPeer(peer_id, PollicinoStore())
        for peer_id in peer_ids
    }


def _seed_destination_history(
    state: RapidEncounterPrototypeState,
    *,
    carrier_id: str,
    destination_id: str,
    interval_s: int,
    opportunity_bytes: int,
) -> None:
    state.observe_prior_meeting(
        carrier_id,
        destination_id,
        now_s=0,
        opportunity_bytes_a_to_b=opportunity_bytes,
    )
    state.observe_prior_meeting(
        carrier_id,
        destination_id,
        now_s=interval_s,
        opportunity_bytes_a_to_b=opportunity_bytes,
    )


def test_non_destination_encounter_selects_best_deadline_utility_per_byte() -> None:
    peers = _peers("a", "b", "d")
    ledger = CustodyLedger()
    small = _bundle(
        "small",
        size=64,
        origin=peers["a"],
        ledger=ledger,
        nonce=1,
    )
    large = _bundle(
        "large",
        size=128,
        origin=peers["a"],
        ledger=ledger,
        nonce=2,
    )
    state = RapidEncounterPrototypeState()

    _seed_destination_history(
        state,
        carrier_id="a",
        destination_id="d",
        interval_s=100,
        opportunity_bytes=64,
    )
    _seed_destination_history(
        state,
        carrier_id="b",
        destination_id="d",
        interval_s=40,
        opportunity_bytes=64,
    )

    window = SyntheticContactWindow(
        "a-b", "a", "b", "lora", 1100, 10, 128, 100
    )
    before_target_items = len(peers["b"].store)
    report = evaluate_rapid_encounter(
        state,
        (small, large),
        source=peers["a"],
        target=peers["b"],
        ledger=ledger,
        window=window,
        destination_ids=("d",),
        application_deadlines={
            small.bundle.bundle_id: 1160,
            large.bundle.bundle_id: 1200,
        },
    )

    assert not report.direct_delivery
    assert report.selected_bundle_id == small.bundle.bundle_id
    assert len(report.inferences) == 2
    assert report.candidate_queue_quote_count == 2
    assert report.control_entry_count_lower_bound > 0
    assert all(item.knowledge_complete for item in report.inferences)
    assert len(peers["b"].store) == before_target_items == 0
    assert ledger.get(small.bundle.bundle_id, "b") is None
    assert ledger.get(large.bundle.bundle_id, "b") is None


def test_missing_candidate_history_blocks_optimistic_selection() -> None:
    peers = _peers("a", "b", "d")
    ledger = CustodyLedger()
    item = _bundle(
        "unknown-candidate",
        size=64,
        origin=peers["a"],
        ledger=ledger,
        nonce=3,
    )
    state = RapidEncounterPrototypeState()
    _seed_destination_history(
        state,
        carrier_id="a",
        destination_id="d",
        interval_s=100,
        opportunity_bytes=64,
    )

    report = evaluate_rapid_encounter(
        state,
        (item,),
        source=peers["a"],
        target=peers["b"],
        ledger=ledger,
        window=SyntheticContactWindow(
            "a-b-no-history", "a", "b", "lora", 1100, 10, 64, 200
        ),
        destination_ids=("d",),
        application_deadlines={item.bundle.bundle_id: 1200},
    )

    assert not report.direct_delivery
    assert report.selected_bundle_id is None
    assert report.candidate_queue_quote_count == 0
    assert len(report.inferences) == 1
    inference = report.inferences[0]
    assert "b" in inference.missing_meeting_carriers
    assert "b" in inference.missing_queue_carriers
    assert inference.utility is None


def test_direct_destination_encounter_bypasses_rapid_replication_ranking() -> None:
    peers = _peers("a", "d")
    ledger = CustodyLedger()
    first = _bundle("direct-one", size=64, origin=peers["a"], ledger=ledger, nonce=4)
    second = _bundle("direct-two", size=128, origin=peers["a"], ledger=ledger, nonce=5)
    state = RapidEncounterPrototypeState()
    _seed_destination_history(
        state,
        carrier_id="a",
        destination_id="d",
        interval_s=100,
        opportunity_bytes=128,
    )

    report = evaluate_rapid_encounter(
        state,
        (first, second),
        source=peers["a"],
        target=peers["d"],
        ledger=ledger,
        window=SyntheticContactWindow(
            "a-d-direct", "a", "d", "lora", 1100, 10, 128, 300
        ),
        destination_ids=("d",),
        application_deadlines={
            first.bundle.bundle_id: 1200,
            second.bundle.bundle_id: 1200,
        },
    )

    assert report.direct_delivery
    assert set(report.direct_bundle_ids) == {
        first.bundle.bundle_id,
        second.bundle.bundle_id,
    }
    assert report.selection is None
    assert report.inferences == ()
    assert report.candidate_queue_quote_count == 0
    assert len(peers["d"].store) == 0


def test_non_destination_does_not_rank_full_replica_that_cannot_fit_contact_budget() -> None:
    peers = _peers("a", "b", "d")
    ledger = CustodyLedger()
    item = _bundle(
        "too-large-for-contact",
        size=128,
        origin=peers["a"],
        ledger=ledger,
        nonce=6,
    )
    state = RapidEncounterPrototypeState()
    _seed_destination_history(
        state,
        carrier_id="a",
        destination_id="d",
        interval_s=100,
        opportunity_bytes=128,
    )
    _seed_destination_history(
        state,
        carrier_id="b",
        destination_id="d",
        interval_s=40,
        opportunity_bytes=128,
    )

    report = evaluate_rapid_encounter(
        state,
        (item,),
        source=peers["a"],
        target=peers["b"],
        ledger=ledger,
        window=SyntheticContactWindow(
            "a-b-too-small", "a", "b", "lora", 1100, 10, 64, 400
        ),
        destination_ids=("d",),
        application_deadlines={item.bundle.bundle_id: 1300},
    )

    assert report.selected_bundle_id is None
    assert report.inferences == ()


def test_encounter_prototype_requires_exactly_one_destination() -> None:
    peers = _peers("a", "b", "d", "e")
    ledger = CustodyLedger()
    item = _bundle("validation", size=64, origin=peers["a"], ledger=ledger, nonce=7)
    state = RapidEncounterPrototypeState()
    window = SyntheticContactWindow(
        "a-b-validation", "a", "b", "lora", 1100, 10, 64, 500
    )

    with pytest.raises(ValueError, match="exactly one destination"):
        evaluate_rapid_encounter(
            state,
            (item,),
            source=peers["a"],
            target=peers["b"],
            ledger=ledger,
            window=window,
            destination_ids=("d", "e"),
            application_deadlines={item.bundle.bundle_id: 1200},
        )

    with pytest.raises(ValueError, match="match the synthetic contact window"):
        evaluate_rapid_encounter(
            state,
            (item,),
            source=peers["b"],
            target=peers["a"],
            ledger=ledger,
            window=window,
            destination_ids=("d",),
            application_deadlines={item.bundle.bundle_id: 1200},
        )
