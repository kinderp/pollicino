import hashlib

import pytest

from pollicino.net.rapid_replica_control import (
    RapidDeliveryAcknowledgement,
    RapidReplicaAdvertisement,
    RapidReplicaControlState,
    exchange_rapid_replica_metadata,
)


def _bundle(label: str = "bundle") -> bytes:
    return hashlib.sha256(label.encode()).digest()


def test_complete_replica_location_gossips_and_unchanged_delta_goes_quiet() -> None:
    bundle_id = _bundle("replica")
    a = RapidReplicaControlState("a")
    b = RapidReplicaControlState("b")

    a.advertise_local_replica(bundle_id, present=True, now_s=100)
    first = exchange_rapid_replica_metadata(a, b)
    second = exchange_rapid_replica_metadata(a, b)

    assert first.left_sent_replica_count == 1
    assert first.right_sent_replica_count == 0
    assert first.right_learned_replica_count == 1
    assert first.total_sent_entry_count == 1
    assert b.known_replica_carriers(bundle_id) == ("a",)
    assert second.total_sent_entry_count == 0


def test_newer_replica_tombstone_cannot_be_resurrected_by_stale_gossip() -> None:
    bundle_id = _bundle("tombstone")
    origin = RapidReplicaControlState("a")
    fresh = RapidReplicaControlState("b")
    stale = RapidReplicaControlState("s")
    observer = RapidReplicaControlState("c")

    present = origin.advertise_local_replica(bundle_id, present=True, now_s=100)
    assert present.sequence == 1
    exchange_rapid_replica_metadata(origin, fresh)
    exchange_rapid_replica_metadata(fresh, stale)  # stale freezes a seq=1 view.

    removed = origin.advertise_local_replica(bundle_id, present=False, now_s=200)
    assert removed.sequence == 2
    exchange_rapid_replica_metadata(origin, fresh)
    exchange_rapid_replica_metadata(fresh, observer)

    assert observer.known_replica_carriers(bundle_id) == ()
    assert observer.replica_state(bundle_id, "a") == removed

    stale_report = exchange_rapid_replica_metadata(stale, observer)
    assert stale_report.left_sent_replica_count >= 1
    assert stale_report.right_learned_replica_count == 0
    assert observer.replica_state(bundle_id, "a") == removed
    assert observer.known_replica_carriers(bundle_id) == ()


def test_replica_can_be_reacquired_after_tombstone_with_higher_sequence() -> None:
    bundle_id = _bundle("reacquire")
    a = RapidReplicaControlState("a")
    b = RapidReplicaControlState("b")

    first = a.advertise_local_replica(bundle_id, present=True, now_s=100)
    tombstone = a.advertise_local_replica(bundle_id, present=False, now_s=200)
    reacquired = a.advertise_local_replica(bundle_id, present=True, now_s=300)

    assert (first.sequence, tombstone.sequence, reacquired.sequence) == (1, 2, 3)
    exchange_rapid_replica_metadata(a, b)
    assert b.replica_state(bundle_id, "a") == reacquired
    assert b.known_replica_carriers(bundle_id) == ("a",)


def test_delivery_ack_is_monotonic_and_propagates_separately_from_replica_state() -> None:
    bundle_id = _bundle("delivery")
    destination = RapidReplicaControlState("d")
    relay = RapidReplicaControlState("r")
    peer = RapidReplicaControlState("p")

    ack = destination.acknowledge_local_delivery(bundle_id, delivered_at_s=500)
    report = exchange_rapid_replica_metadata(destination, relay)
    exchange_rapid_replica_metadata(relay, peer)

    assert report.left_sent_delivery_ack_count == 1
    assert report.left_sent_replica_count == 0
    assert relay.delivery_ack(bundle_id, "d") == ack
    assert peer.delivery_ack(bundle_id, "d") == ack
    assert peer.delivered_destinations(bundle_id) == ("d",)
    assert peer.known_replica_carriers(bundle_id) == ()

    # Re-observing the same delivery is idempotent; changing the claimed first
    # delivery time is not silently accepted.
    assert destination.acknowledge_local_delivery(bundle_id, delivered_at_s=500) == ack
    with pytest.raises(ValueError, match="different time"):
        destination.acknowledge_local_delivery(bundle_id, delivered_at_s=501)


def test_bootstrap_can_send_duplicate_shared_facts_but_next_exchange_is_zero() -> None:
    bundle_id = _bundle("bootstrap")
    a = RapidReplicaControlState("a")
    b = RapidReplicaControlState("b")

    a.advertise_local_replica(bundle_id, present=True, now_s=100)
    b.advertise_local_replica(bundle_id, present=True, now_s=100)

    first = exchange_rapid_replica_metadata(a, b)
    second = exchange_rapid_replica_metadata(a, b)

    assert first.total_sent_entry_count == 2
    assert first.total_learned_entry_count == 2
    assert a.known_replica_carriers(bundle_id) == ("a", "b")
    assert b.known_replica_carriers(bundle_id) == ("a", "b")
    assert second.total_sent_entry_count == 0


def test_conflicting_same_sequence_metadata_fails_closed() -> None:
    bundle_id = _bundle("conflict")
    state = RapidReplicaControlState("observer")

    original = RapidReplicaAdvertisement(
        bundle_id=bundle_id,
        carrier_id="a",
        sequence=1,
        present=True,
        updated_at_s=100,
    )
    conflict = RapidReplicaAdvertisement(
        bundle_id=bundle_id,
        carrier_id="a",
        sequence=1,
        present=False,
        updated_at_s=100,
    )
    assert state._learn_replica(original)
    with pytest.raises(ValueError, match="conflicting replica"):
        state._learn_replica(conflict)

    ack = RapidDeliveryAcknowledgement(
        bundle_id=bundle_id,
        destination_id="d",
        sequence=1,
        delivered_at_s=200,
    )
    conflicting_ack = RapidDeliveryAcknowledgement(
        bundle_id=bundle_id,
        destination_id="d",
        sequence=1,
        delivered_at_s=201,
    )
    assert state._learn_delivery(ack)
    with pytest.raises(ValueError, match="conflicting delivery"):
        state._learn_delivery(conflicting_ack)


def test_replica_control_validation_fails_closed() -> None:
    bundle_id = _bundle("validation")
    a = RapidReplicaControlState("a")

    with pytest.raises(ValueError, match="32 bytes"):
        a.advertise_local_replica(b"short", present=True, now_s=1)
    with pytest.raises(ValueError, match="backwards"):
        a.advertise_local_replica(bundle_id, present=True, now_s=100)
        a.advertise_local_replica(bundle_id, present=False, now_s=99)
    with pytest.raises(ValueError, match="distinct"):
        exchange_rapid_replica_metadata(a, a)
