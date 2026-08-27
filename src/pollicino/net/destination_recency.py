from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

from .bearer import BearerProfile
from .bundle import CustodyLedger
from .contact_windows import SyntheticContactWindow
from .scheduling import ScheduledBundle
from .store_forward import ForwardPeer


def _require_id(name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class DestinationRecencyObservation:
    peer_id: str
    destination_id: str
    observed_at_s: int

    def __post_init__(self) -> None:
        _require_id("peer_id", self.peer_id)
        _require_id("destination_id", self.destination_id)
        if self.peer_id == self.destination_id:
            raise ValueError("recency observation peer must differ from destination")
        if (
            isinstance(self.observed_at_s, bool)
            or not isinstance(self.observed_at_s, int)
            or self.observed_at_s < 0
        ):
            raise ValueError("observed_at_s must be a non-negative integer")


@dataclass(slots=True)
class DestinationRecencyStrategy:
    """Minimal encounter-history baseline: forward toward more recent gateway contact.

    The strategy intentionally knows only one application destination. Each node
    keeps the timestamp of its most recent direct encounter with that destination.
    On a non-destination encounter, the source forwards only when the target's
    timestamp is known and newer than the source's timestamp.

    This is a research baseline for the Use-Case Justification Gate. It does not
    use transitivity, delivery probability, replica-location gossip, queue state
    or future contacts.
    """

    destination_id: str
    prior_observations: tuple[DestinationRecencyObservation, ...] = ()
    strategy_id: str = "destination-recency"
    _run_ledger: CustodyLedger | None = field(default=None, init=False, repr=False)
    _last_seen: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    quote_entry_count: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        _require_id("destination_id", self.destination_id)
        _require_id("strategy_id", self.strategy_id)
        if not isinstance(self.prior_observations, tuple):
            raise TypeError("prior_observations must be a tuple")
        if not all(
            isinstance(item, DestinationRecencyObservation)
            for item in self.prior_observations
        ):
            raise TypeError(
                "prior_observations must contain DestinationRecencyObservation values"
            )
        if any(
            item.destination_id != self.destination_id
            for item in self.prior_observations
        ):
            raise ValueError("all prior observations must target destination_id")

    def _ensure_run(self, ledger: CustodyLedger, *, now_s: int) -> None:
        if self._run_ledger is ledger:
            return
        self._run_ledger = ledger
        self._last_seen.clear()
        self.quote_entry_count = 0
        for observation in self.prior_observations:
            if observation.observed_at_s >= now_s:
                raise ValueError(
                    "destination-recency prior observations must precede the first routing window"
                )
            previous = self._last_seen.get(observation.peer_id)
            if previous is None or observation.observed_at_s > previous:
                self._last_seen[observation.peer_id] = observation.observed_at_s

    def last_destination_encounter_s(self, peer_id: str) -> int | None:
        _require_id("peer_id", peer_id)
        return self._last_seen.get(peer_id)

    def select_bundles(
        self,
        bundles: Sequence[ScheduledBundle],
        *,
        window: SyntheticContactWindow,
        bearer: BearerProfile,
        source: ForwardPeer,
        target: ForwardPeer,
        ledger: CustodyLedger,
    ) -> tuple[ScheduledBundle, ...]:
        del bearer
        self._ensure_run(ledger, now_s=window.start_s)

        if target.peer_id == self.destination_id:
            self._last_seen[source.peer_id] = window.start_s
            return tuple(bundles)

        if source.peer_id == self.destination_id:
            self._last_seen[target.peer_id] = window.start_s
            return ()

        # One directed quote from the target to the source is enough for the
        # source's decision. Unknown is represented explicitly by the future
        # wire model's reserved timestamp value rather than treated as zero-cost.
        self.quote_entry_count += 1
        target_seen = self._last_seen.get(target.peer_id)
        if target_seen is None:
            return ()
        source_seen = self._last_seen.get(source.peer_id)
        if source_seen is None or target_seen > source_seen:
            return tuple(bundles)
        return ()


class DestinationRecencyNodeReferenceMode(str, Enum):
    FULL_PSEUDONYM_128 = "full_pseudonym_128"
    SHARED_U16_INDEX = "shared_u16_index"


@dataclass(frozen=True, slots=True)
class DestinationRecencyControlProfile:
    node_reference_mode: DestinationRecencyNodeReferenceMode
    stream_header_bytes: int = 4
    full_node_id_bytes: int = 16
    shared_index_bytes: int = 2
    timestamp_bytes: int = 8
    dictionary_header_bytes: int = 4

    def __post_init__(self) -> None:
        if not isinstance(
            self.node_reference_mode, DestinationRecencyNodeReferenceMode
        ):
            raise TypeError(
                "node_reference_mode must be DestinationRecencyNodeReferenceMode"
            )
        for name, value in (
            ("stream_header_bytes", self.stream_header_bytes),
            ("full_node_id_bytes", self.full_node_id_bytes),
            ("shared_index_bytes", self.shared_index_bytes),
            ("timestamp_bytes", self.timestamp_bytes),
            ("dictionary_header_bytes", self.dictionary_header_bytes),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

    @property
    def node_reference_bytes(self) -> int:
        if (
            self.node_reference_mode
            is DestinationRecencyNodeReferenceMode.FULL_PSEUDONYM_128
        ):
            return self.full_node_id_bytes
        return self.shared_index_bytes

    @property
    def quote_entry_bytes(self) -> int:
        # Destination reference + u64 last-seen timestamp. A reserved timestamp
        # value represents UNKNOWN so no separate boolean byte is required.
        return self.node_reference_bytes + self.timestamp_bytes

    def bootstrap_bytes(self, *, node_count: int) -> int:
        if isinstance(node_count, bool) or not isinstance(node_count, int) or node_count <= 0:
            raise ValueError("node_count must be a positive integer")
        if (
            self.node_reference_mode
            is DestinationRecencyNodeReferenceMode.FULL_PSEUDONYM_128
        ):
            return 0
        return self.dictionary_header_bytes + node_count * (
            self.shared_index_bytes + self.full_node_id_bytes
        )


@dataclass(frozen=True, slots=True)
class DestinationRecencyControlReport:
    quote_entry_count: int
    quote_wire_bytes: int
    bootstrap_wire_bytes: int
    evidence_class: str = "model_synthetic"

    @property
    def control_wire_bytes(self) -> int:
        return self.quote_wire_bytes + self.bootstrap_wire_bytes


def account_destination_recency_control(
    strategy: DestinationRecencyStrategy,
    *,
    profile: DestinationRecencyControlProfile,
    node_count: int,
) -> DestinationRecencyControlReport:
    """Account the minimal directed recency quote used by each decision."""

    if not isinstance(strategy, DestinationRecencyStrategy):
        raise TypeError("strategy must be DestinationRecencyStrategy")
    if not isinstance(profile, DestinationRecencyControlProfile):
        raise TypeError("profile must be DestinationRecencyControlProfile")
    if isinstance(node_count, bool) or not isinstance(node_count, int) or node_count <= 0:
        raise ValueError("node_count must be a positive integer")
    count = strategy.quote_entry_count
    quote_wire = count * (
        profile.stream_header_bytes + profile.quote_entry_bytes
    )
    return DestinationRecencyControlReport(
        quote_entry_count=count,
        quote_wire_bytes=quote_wire,
        bootstrap_wire_bytes=profile.bootstrap_bytes(node_count=node_count),
    )
