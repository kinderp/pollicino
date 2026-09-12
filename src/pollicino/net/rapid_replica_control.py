from __future__ import annotations

from dataclasses import dataclass, field


def _require_id(name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _require_bundle_id(value: bytes) -> None:
    if not isinstance(value, bytes) or len(value) != 32:
        raise ValueError("bundle_id must be exactly 32 bytes")


def _require_sequence(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("sequence must be a positive integer")


def _require_timestamp(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class RapidReplicaAdvertisement:
    """Carrier-authored state of one complete, verified RAPID replica.

    ``present=False`` is a tombstone. Sequence numbers are monotonic for the
    `(bundle_id, carrier_id)` authority key, so stale gossip cannot resurrect a
    replica after a newer deletion has been observed.

    Authenticity is intentionally not implemented here; this is a synthetic
    control-state model, not a production security format.
    """

    bundle_id: bytes
    carrier_id: str
    sequence: int
    present: bool
    updated_at_s: int

    def __post_init__(self) -> None:
        _require_bundle_id(self.bundle_id)
        _require_id("carrier_id", self.carrier_id)
        _require_sequence(self.sequence)
        if not isinstance(self.present, bool):
            raise TypeError("present must be bool")
        _require_timestamp("updated_at_s", self.updated_at_s)

    @property
    def key(self) -> tuple[bytes, str]:
        return self.bundle_id, self.carrier_id


@dataclass(frozen=True, slots=True)
class RapidDeliveryAcknowledgement:
    """Final-destination-authored monotonic delivery fact.

    This is distinct from link ACKs, PNF1 frame ACKs and PNC1 custody receipts.
    Once emitted for a bundle/destination pair it is never retracted.
    """

    bundle_id: bytes
    destination_id: str
    sequence: int
    delivered_at_s: int

    def __post_init__(self) -> None:
        _require_bundle_id(self.bundle_id)
        _require_id("destination_id", self.destination_id)
        _require_sequence(self.sequence)
        _require_timestamp("delivered_at_s", self.delivered_at_s)

    @property
    def key(self) -> tuple[bytes, str]:
        return self.bundle_id, self.destination_id


@dataclass(frozen=True, slots=True)
class RapidReplicaMetadataExchangeReport:
    left_id: str
    right_id: str
    left_sent_replica_count: int
    right_sent_replica_count: int
    left_sent_delivery_ack_count: int
    right_sent_delivery_ack_count: int
    left_learned_replica_count: int
    right_learned_replica_count: int
    left_learned_delivery_ack_count: int
    right_learned_delivery_ack_count: int

    @property
    def left_sent_entry_count(self) -> int:
        return self.left_sent_replica_count + self.left_sent_delivery_ack_count

    @property
    def right_sent_entry_count(self) -> int:
        return self.right_sent_replica_count + self.right_sent_delivery_ack_count

    @property
    def total_sent_entry_count(self) -> int:
        return self.left_sent_entry_count + self.right_sent_entry_count

    @property
    def total_learned_entry_count(self) -> int:
        return (
            self.left_learned_replica_count
            + self.right_learned_replica_count
            + self.left_learned_delivery_ack_count
            + self.right_learned_delivery_ack_count
        )


_MetadataKey = tuple[str, bytes, str]


@dataclass(slots=True)
class RapidReplicaControlState:
    """Delta-gossiped replica-location and end-delivery knowledge.

    Replica facts are authoritative only when authored by ``carrier_id``.
    Delivery acknowledgements are authoritative only when authored by
    ``destination_id``. The model assumes that authority relationship but does
    not yet attach cryptographic authentication.

    Changed-entry counts are observable control work. No wire-byte cost is
    inferred until an explicit control encoding is designed and benchmarked.
    """

    node_id: str
    _replicas: dict[tuple[bytes, str], RapidReplicaAdvertisement] = field(
        default_factory=dict, init=False, repr=False
    )
    _deliveries: dict[tuple[bytes, str], RapidDeliveryAcknowledgement] = field(
        default_factory=dict, init=False, repr=False
    )
    _local_replica_sequence: dict[bytes, int] = field(
        default_factory=dict, init=False, repr=False
    )
    _local_delivery_sequence: dict[bytes, int] = field(
        default_factory=dict, init=False, repr=False
    )
    _generation: int = field(default=0, init=False, repr=False)
    _entry_generation: dict[_MetadataKey, int] = field(
        default_factory=dict, init=False, repr=False
    )
    _last_sent_generation: dict[str, int] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        _require_id("node_id", self.node_id)

    @property
    def replica_advertisements(self) -> tuple[RapidReplicaAdvertisement, ...]:
        return tuple(
            self._replicas[key]
            for key in sorted(self._replicas, key=lambda item: (item[0].hex(), item[1]))
        )

    @property
    def delivery_acknowledgements(self) -> tuple[RapidDeliveryAcknowledgement, ...]:
        return tuple(
            self._deliveries[key]
            for key in sorted(self._deliveries, key=lambda item: (item[0].hex(), item[1]))
        )

    def _touch(self, key: _MetadataKey) -> None:
        self._generation += 1
        self._entry_generation[key] = self._generation

    def advertise_local_replica(
        self,
        bundle_id: bytes,
        *,
        present: bool,
        now_s: int,
    ) -> RapidReplicaAdvertisement:
        """Publish this node's complete-replica state for one bundle.

        Re-publishing the same state is a no-op and returns the current fact.
        A state transition increments the carrier-authored sequence.
        """

        _require_bundle_id(bundle_id)
        if not isinstance(present, bool):
            raise TypeError("present must be bool")
        _require_timestamp("now_s", now_s)
        key = (bundle_id, self.node_id)
        previous = self._replicas.get(key)
        if previous is not None:
            if now_s < previous.updated_at_s:
                raise ValueError("local replica update time cannot move backwards")
            if previous.present is present:
                return previous

        sequence = self._local_replica_sequence.get(bundle_id, 0) + 1
        self._local_replica_sequence[bundle_id] = sequence
        advertisement = RapidReplicaAdvertisement(
            bundle_id=bundle_id,
            carrier_id=self.node_id,
            sequence=sequence,
            present=present,
            updated_at_s=now_s,
        )
        self._replicas[key] = advertisement
        self._touch(("replica", bundle_id, self.node_id))
        return advertisement

    def acknowledge_local_delivery(
        self,
        bundle_id: bytes,
        *,
        delivered_at_s: int,
    ) -> RapidDeliveryAcknowledgement:
        """Publish final delivery by this node, exactly once per bundle."""

        _require_bundle_id(bundle_id)
        _require_timestamp("delivered_at_s", delivered_at_s)
        key = (bundle_id, self.node_id)
        previous = self._deliveries.get(key)
        if previous is not None:
            if previous.delivered_at_s != delivered_at_s:
                raise ValueError(
                    "local delivery acknowledgement already exists with a different time"
                )
            return previous

        sequence = self._local_delivery_sequence.get(bundle_id, 0) + 1
        self._local_delivery_sequence[bundle_id] = sequence
        acknowledgement = RapidDeliveryAcknowledgement(
            bundle_id=bundle_id,
            destination_id=self.node_id,
            sequence=sequence,
            delivered_at_s=delivered_at_s,
        )
        self._deliveries[key] = acknowledgement
        self._touch(("delivery", bundle_id, self.node_id))
        return acknowledgement

    def replica_state(
        self,
        bundle_id: bytes,
        carrier_id: str,
    ) -> RapidReplicaAdvertisement | None:
        _require_bundle_id(bundle_id)
        _require_id("carrier_id", carrier_id)
        return self._replicas.get((bundle_id, carrier_id))

    def delivery_ack(
        self,
        bundle_id: bytes,
        destination_id: str,
    ) -> RapidDeliveryAcknowledgement | None:
        _require_bundle_id(bundle_id)
        _require_id("destination_id", destination_id)
        return self._deliveries.get((bundle_id, destination_id))

    def known_replica_carriers(self, bundle_id: bytes) -> tuple[str, ...]:
        """Return carriers currently believed to hold a complete replica."""

        _require_bundle_id(bundle_id)
        return tuple(
            sorted(
                advertisement.carrier_id
                for advertisement in self._replicas.values()
                if advertisement.bundle_id == bundle_id and advertisement.present
            )
        )

    def delivered_destinations(self, bundle_id: bytes) -> tuple[str, ...]:
        _require_bundle_id(bundle_id)
        return tuple(
            sorted(
                acknowledgement.destination_id
                for acknowledgement in self._deliveries.values()
                if acknowledgement.bundle_id == bundle_id
            )
        )

    def _learn_replica(self, value: RapidReplicaAdvertisement) -> bool:
        if not isinstance(value, RapidReplicaAdvertisement):
            raise TypeError("replica metadata must contain RapidReplicaAdvertisement values")
        previous = self._replicas.get(value.key)
        if previous is not None:
            if value.sequence < previous.sequence:
                return False
            if value.sequence == previous.sequence:
                if value != previous:
                    raise ValueError(
                        "conflicting replica advertisements share the same authority sequence"
                    )
                return False
        self._replicas[value.key] = value
        self._touch(("replica", value.bundle_id, value.carrier_id))
        return True

    def _learn_delivery(self, value: RapidDeliveryAcknowledgement) -> bool:
        if not isinstance(value, RapidDeliveryAcknowledgement):
            raise TypeError(
                "delivery metadata must contain RapidDeliveryAcknowledgement values"
            )
        previous = self._deliveries.get(value.key)
        if previous is not None:
            if value.sequence < previous.sequence:
                return False
            if value.sequence == previous.sequence:
                if value != previous:
                    raise ValueError(
                        "conflicting delivery acknowledgements share the same authority sequence"
                    )
                return False
        self._deliveries[value.key] = value
        self._touch(("delivery", value.bundle_id, value.destination_id))
        return True

    def _delta_for(
        self,
        peer_id: str,
    ) -> tuple[
        tuple[RapidReplicaAdvertisement, ...],
        tuple[RapidDeliveryAcknowledgement, ...],
    ]:
        _require_id("peer_id", peer_id)
        watermark = self._last_sent_generation.get(peer_id, 0)
        replicas = tuple(
            self._replicas[(bundle_id, authority_id)]
            for kind, bundle_id, authority_id in sorted(
                self._entry_generation,
                key=lambda item: (item[0], item[1].hex(), item[2]),
            )
            if kind == "replica"
            and self._entry_generation[(kind, bundle_id, authority_id)] > watermark
        )
        deliveries = tuple(
            self._deliveries[(bundle_id, authority_id)]
            for kind, bundle_id, authority_id in sorted(
                self._entry_generation,
                key=lambda item: (item[0], item[1].hex(), item[2]),
            )
            if kind == "delivery"
            and self._entry_generation[(kind, bundle_id, authority_id)] > watermark
        )
        return replicas, deliveries

    def _mark_synchronized_with(self, peer_id: str) -> None:
        _require_id("peer_id", peer_id)
        self._last_sent_generation[peer_id] = self._generation


def exchange_rapid_replica_metadata(
    left: RapidReplicaControlState,
    right: RapidReplicaControlState,
) -> RapidReplicaMetadataExchangeReport:
    """Exchange changed replica/delivery facts without inventing wire bytes."""

    if not isinstance(left, RapidReplicaControlState) or not isinstance(
        right, RapidReplicaControlState
    ):
        raise TypeError("left and right must be RapidReplicaControlState values")
    if left.node_id == right.node_id:
        raise ValueError("metadata exchange requires two distinct nodes")

    left_replicas, left_deliveries = left._delta_for(right.node_id)
    right_replicas, right_deliveries = right._delta_for(left.node_id)

    left_learned_replicas = sum(right._learn_replica(item) for item in left_replicas)
    left_learned_deliveries = sum(
        right._learn_delivery(item) for item in left_deliveries
    )
    right_learned_replicas = sum(left._learn_replica(item) for item in right_replicas)
    right_learned_deliveries = sum(
        left._learn_delivery(item) for item in right_deliveries
    )

    # The variable names above describe the origin of the transmitted delta.
    # Report fields describe the receiver that learned each delta, so map them
    # explicitly rather than relying on incidental left/right naming.
    report = RapidReplicaMetadataExchangeReport(
        left_id=left.node_id,
        right_id=right.node_id,
        left_sent_replica_count=len(left_replicas),
        right_sent_replica_count=len(right_replicas),
        left_sent_delivery_ack_count=len(left_deliveries),
        right_sent_delivery_ack_count=len(right_deliveries),
        left_learned_replica_count=right_learned_replicas,
        right_learned_replica_count=left_learned_replicas,
        left_learned_delivery_ack_count=right_learned_deliveries,
        right_learned_delivery_ack_count=left_learned_deliveries,
    )

    # Both peers now know all entries sent in either direction; learned gossip
    # should not be echoed straight back unless a newer authority sequence is
    # observed later.
    left._mark_synchronized_with(right.node_id)
    right._mark_synchronized_with(left.node_id)
    return report
