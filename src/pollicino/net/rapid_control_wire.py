from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .rapid_schedule import RapidScheduleReport


class RapidNodeReferenceMode(str, Enum):
    """Research-only node-reference encodings for RAPID control accounting."""

    FULL_PSEUDONYM_128 = "full_pseudonym_128"
    SHARED_U16_INDEX = "shared_u16_index"


@dataclass(frozen=True, slots=True)
class RapidControlWireProfile:
    """Deterministic research profile for control-plane byte accounting.

    This is not a production protocol and is deliberately kept outside PNB1,
    PNC1 and the frozen H2/PHY formats.  It provides an explicit byte model so
    RAPID's avoided content replication is not compared against free routing
    knowledge.

    ``FULL_PSEUDONYM_128`` uses a self-contained 16-byte pseudonymous node
    reference in every record. ``SHARED_U16_INDEX`` uses a 2-byte index and
    counts one canonical index dictionary representation separately.  The
    latter does *not* claim that distributing that dictionary to every peer is
    free; ``bootstrap_wire_bytes`` is exposed separately for that reason.
    """

    node_reference_mode: RapidNodeReferenceMode
    stream_header_bytes: int = 4
    full_node_id_bytes: int = 16
    shared_index_bytes: int = 2
    bundle_id_bytes: int = 32
    sequence_bytes: int = 4
    timestamp_bytes: int = 8
    boolean_bytes: int = 1
    float64_bytes: int = 8
    sample_count_bytes: int = 4
    meetings_needed_bytes: int = 2
    entry_type_bytes: int = 1
    dictionary_header_bytes: int = 4

    def __post_init__(self) -> None:
        if not isinstance(self.node_reference_mode, RapidNodeReferenceMode):
            raise TypeError("node_reference_mode must be RapidNodeReferenceMode")
        for name, value in (
            ("stream_header_bytes", self.stream_header_bytes),
            ("full_node_id_bytes", self.full_node_id_bytes),
            ("shared_index_bytes", self.shared_index_bytes),
            ("bundle_id_bytes", self.bundle_id_bytes),
            ("sequence_bytes", self.sequence_bytes),
            ("timestamp_bytes", self.timestamp_bytes),
            ("boolean_bytes", self.boolean_bytes),
            ("float64_bytes", self.float64_bytes),
            ("sample_count_bytes", self.sample_count_bytes),
            ("meetings_needed_bytes", self.meetings_needed_bytes),
            ("entry_type_bytes", self.entry_type_bytes),
            ("dictionary_header_bytes", self.dictionary_header_bytes),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

    @property
    def node_reference_bytes(self) -> int:
        if self.node_reference_mode is RapidNodeReferenceMode.FULL_PSEUDONYM_128:
            return self.full_node_id_bytes
        return self.shared_index_bytes

    @property
    def meeting_entry_bytes(self) -> int:
        # node A, node B, mean inter-meeting seconds, sample count, observed-at
        return (
            2 * self.node_reference_bytes
            + self.float64_bytes
            + self.sample_count_bytes
            + self.timestamp_bytes
        )

    @property
    def replica_entry_bytes(self) -> int:
        # type, full bundle ID, carrier, monotonic sequence, present, updated-at
        return (
            self.entry_type_bytes
            + self.bundle_id_bytes
            + self.node_reference_bytes
            + self.sequence_bytes
            + self.boolean_bytes
            + self.timestamp_bytes
        )

    @property
    def delivery_entry_bytes(self) -> int:
        # type, full bundle ID, destination, monotonic sequence, delivered-at
        return (
            self.entry_type_bytes
            + self.bundle_id_bytes
            + self.node_reference_bytes
            + self.sequence_bytes
            + self.timestamp_bytes
        )

    @property
    def queue_quote_entry_bytes(self) -> int:
        # full bundle ID, quoting carrier, explicit meetings-needed estimate
        return (
            self.bundle_id_bytes
            + self.node_reference_bytes
            + self.meetings_needed_bytes
        )

    def bootstrap_bytes(self, *, node_count: int) -> int:
        if isinstance(node_count, bool) or not isinstance(node_count, int) or node_count <= 0:
            raise ValueError("node_count must be a positive integer")
        if self.node_reference_mode is RapidNodeReferenceMode.FULL_PSEUDONYM_128:
            return 0
        # One canonical dictionary representation: header + (u16 index, full ID).
        # Network-wide dissemination/fanout is deliberately not inferred here.
        return self.dictionary_header_bytes + node_count * (
            self.shared_index_bytes + self.full_node_id_bytes
        )


@dataclass(frozen=True, slots=True)
class RapidControlWireBreakdown:
    meeting_wire_bytes: int
    replica_wire_bytes: int
    delivery_wire_bytes: int
    queue_quote_wire_bytes: int
    bootstrap_wire_bytes: int
    stream_count: int
    meeting_entry_count: int
    replica_entry_count: int
    delivery_entry_count: int
    queue_quote_entry_count: int
    evidence_class: str = "model_synthetic"

    def __post_init__(self) -> None:
        for name, value in (
            ("meeting_wire_bytes", self.meeting_wire_bytes),
            ("replica_wire_bytes", self.replica_wire_bytes),
            ("delivery_wire_bytes", self.delivery_wire_bytes),
            ("queue_quote_wire_bytes", self.queue_quote_wire_bytes),
            ("bootstrap_wire_bytes", self.bootstrap_wire_bytes),
            ("stream_count", self.stream_count),
            ("meeting_entry_count", self.meeting_entry_count),
            ("replica_entry_count", self.replica_entry_count),
            ("delivery_entry_count", self.delivery_entry_count),
            ("queue_quote_entry_count", self.queue_quote_entry_count),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

    @property
    def control_wire_bytes(self) -> int:
        return (
            self.meeting_wire_bytes
            + self.replica_wire_bytes
            + self.delivery_wire_bytes
            + self.queue_quote_wire_bytes
            + self.bootstrap_wire_bytes
        )


def _stream_bytes(count: int, *, header: int, entry_bytes: int) -> tuple[int, int]:
    if count <= 0:
        return 0, 0
    return header + count * entry_bytes, 1


def account_rapid_control_wire(
    report: RapidScheduleReport,
    *,
    profile: RapidControlWireProfile,
    node_count: int,
) -> RapidControlWireBreakdown:
    """Convert already-modeled RAPID control work into explicit research bytes.

    Only information already exposed by the encounter reports is counted.  No
    radio airtime, authentication tag, encryption overhead or retransmission is
    invented.  Those remain separate experiments/evidence gates.
    """

    if not isinstance(report, RapidScheduleReport):
        raise TypeError("report must be RapidScheduleReport")
    if not isinstance(profile, RapidControlWireProfile):
        raise TypeError("profile must be RapidControlWireProfile")
    if isinstance(node_count, bool) or not isinstance(node_count, int) or node_count <= 0:
        raise ValueError("node_count must be a positive integer")

    meeting_bytes = 0
    replica_bytes = 0
    delivery_bytes = 0
    queue_bytes = 0
    stream_count = 0
    meeting_entries = 0
    replica_entries = 0
    delivery_entries = 0
    queue_entries = 0

    for window in report.windows:
        meeting = window.encounter.meeting_exchange
        for count in (meeting.left_sent_entry_count, meeting.right_sent_entry_count):
            encoded, streams = _stream_bytes(
                count,
                header=profile.stream_header_bytes,
                entry_bytes=profile.meeting_entry_bytes,
            )
            meeting_bytes += encoded
            stream_count += streams
            meeting_entries += count

        replica = window.encounter.replica_exchange
        for replica_count, delivery_count in (
            (replica.left_sent_replica_count, replica.left_sent_delivery_ack_count),
            (replica.right_sent_replica_count, replica.right_sent_delivery_ack_count),
        ):
            total = replica_count + delivery_count
            if total <= 0:
                continue
            stream_count += 1
            # One shared stream header for tagged replica and delivery entries.
            replica_bytes += profile.stream_header_bytes
            replica_bytes += replica_count * profile.replica_entry_bytes
            delivery_bytes += delivery_count * profile.delivery_entry_bytes
            replica_entries += replica_count
            delivery_entries += delivery_count

        count = window.encounter.candidate_queue_quote_count
        encoded, streams = _stream_bytes(
            count,
            header=profile.stream_header_bytes,
            entry_bytes=profile.queue_quote_entry_bytes,
        )
        queue_bytes += encoded
        stream_count += streams
        queue_entries += count

    # Preserve the pre-existing entry-count oracle.  A mismatch means this
    # accounting forgot or double-counted a modeled control category.
    if (
        meeting_entries
        + replica_entries
        + delivery_entries
        + queue_entries
        != report.control_entry_count_lower_bound
    ):
        raise AssertionError("RAPID control entry accounting does not recompose")

    return RapidControlWireBreakdown(
        meeting_wire_bytes=meeting_bytes,
        replica_wire_bytes=replica_bytes,
        delivery_wire_bytes=delivery_bytes,
        queue_quote_wire_bytes=queue_bytes,
        bootstrap_wire_bytes=profile.bootstrap_bytes(node_count=node_count),
        stream_count=stream_count,
        meeting_entry_count=meeting_entries,
        replica_entry_count=replica_entries,
        delivery_entry_count=delivery_entries,
        queue_quote_entry_count=queue_entries,
    )


def rapid_modeled_total_wire_bytes(
    report: RapidScheduleReport,
    *,
    control: RapidControlWireBreakdown,
) -> int:
    """Governed Pollicino transfer bytes plus explicit RAPID control bytes."""

    if not isinstance(report, RapidScheduleReport):
        raise TypeError("report must be RapidScheduleReport")
    if not isinstance(control, RapidControlWireBreakdown):
        raise TypeError("control must be RapidControlWireBreakdown")
    return report.total_wire_bytes_excluding_rapid_control + control.control_wire_bytes
