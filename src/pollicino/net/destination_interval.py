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
class DestinationIntervalObservation:
    peer_id: str
    destination_id: str
    observed_at_s: int

    def __post_init__(self) -> None:
        _require_id("peer_id", self.peer_id)
        _require_id("destination_id", self.destination_id)
        if self.peer_id == self.destination_id:
            raise ValueError("interval observation peer must differ from destination")
        if (
            isinstance(self.observed_at_s, bool)
            or not isinstance(self.observed_at_s, int)
            or self.observed_at_s < 0
        ):
            raise ValueError("observed_at_s must be a non-negative integer")


@dataclass(slots=True)
class DestinationIntervalStrategy:
    """Minimal regularity baseline: forward toward shorter direct inter-meeting time.

    This strategy exists specifically because Destination Recency can be misled
    by a very recent one-off destination contact. Each node keeps only its own
    running mean interval between *direct* encounters with one destination.

    On a non-destination encounter, the source forwards only if the target has a
    known mean interval and that interval is shorter than the source's. Unknown
    target regularity is fail-closed. There is no transitivity, route graph,
    replica gossip, queue model, deadline probability or future knowledge.
    """

    destination_id: str
    prior_observations: tuple[DestinationIntervalObservation, ...] = ()
    strategy_id: str = "destination-interval"
    _run_ledger: CustodyLedger | None = field(default=None, init=False, repr=False)
    _last_seen: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    _mean_interval_s: dict[str, float] = field(default_factory=dict, init=False, repr=False)
    _interval_sample_count: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    quote_entry_count: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        _require_id("destination_id", self.destination_id)
        _require_id("strategy_id", self.strategy_id)
        if not isinstance(self.prior_observations, tuple):
            raise TypeError("prior_observations must be a tuple")
        if not all(
            isinstance(item, DestinationIntervalObservation)
            for item in self.prior_observations
        ):
            raise TypeError(
                "prior_observations must contain DestinationIntervalObservation values"
            )
        if any(
            item.destination_id != self.destination_id
            for item in self.prior_observations
        ):
            raise ValueError("all prior observations must target destination_id")

    def _observe(self, peer_id: str, *, now_s: int) -> None:
        previous = self._last_seen.get(peer_id)
        if previous is not None:
            if now_s <= previous:
                raise ValueError("destination encounter times must increase per peer")
            interval = now_s - previous
            previous_count = self._interval_sample_count.get(peer_id, 0)
            previous_mean = self._mean_interval_s.get(peer_id, 0.0)
            count = previous_count + 1
            mean = (
                float(interval)
                if previous_count == 0
                else previous_mean + (interval - previous_mean) / count
            )
            self._interval_sample_count[peer_id] = count
            self._mean_interval_s[peer_id] = float(mean)
        self._last_seen[peer_id] = now_s

    def _ensure_run(self, ledger: CustodyLedger, *, now_s: int) -> None:
        if self._run_ledger is ledger:
            return
        self._run_ledger = ledger
        self._last_seen.clear()
        self._mean_interval_s.clear()
        self._interval_sample_count.clear()
        self.quote_entry_count = 0
        ordered = sorted(
            self.prior_observations,
            key=lambda item: (item.observed_at_s, item.peer_id),
        )
        for observation in ordered:
            if observation.observed_at_s >= now_s:
                raise ValueError(
                    "destination-interval prior observations must precede the first routing window"
                )
            self._observe(observation.peer_id, now_s=observation.observed_at_s)

    def mean_interval_seconds(self, peer_id: str) -> float | None:
        _require_id("peer_id", peer_id)
        return self._mean_interval_s.get(peer_id)

    def interval_sample_count(self, peer_id: str) -> int:
        _require_id("peer_id", peer_id)
        return self._interval_sample_count.get(peer_id, 0)

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
            self._observe(source.peer_id, now_s=window.start_s)
            return tuple(bundles)

        if source.peer_id == self.destination_id:
            self._observe(target.peer_id, now_s=window.start_s)
            return ()

        # One target-authored quote is the only control state required for the
        # forwarding decision. UNKNOWN remains a valid fail-closed value.
        self.quote_entry_count += 1
        target_mean = self._mean_interval_s.get(target.peer_id)
        if target_mean is None:
            return ()
        source_mean = self._mean_interval_s.get(source.peer_id)
        if source_mean is None or target_mean < source_mean:
            return tuple(bundles)
        return ()


class DestinationIntervalNodeReferenceMode(str, Enum):
    FULL_PSEUDONYM_128 = "full_pseudonym_128"
    SHARED_U16_INDEX = "shared_u16_index"


@dataclass(frozen=True, slots=True)
class DestinationIntervalControlProfile:
    node_reference_mode: DestinationIntervalNodeReferenceMode
    stream_header_bytes: int = 4
    full_node_id_bytes: int = 16
    shared_index_bytes: int = 2
    float64_bytes: int = 8
    dictionary_header_bytes: int = 4

    def __post_init__(self) -> None:
        if not isinstance(
            self.node_reference_mode, DestinationIntervalNodeReferenceMode
        ):
            raise TypeError(
                "node_reference_mode must be DestinationIntervalNodeReferenceMode"
            )
        for name, value in (
            ("stream_header_bytes", self.stream_header_bytes),
            ("full_node_id_bytes", self.full_node_id_bytes),
            ("shared_index_bytes", self.shared_index_bytes),
            ("float64_bytes", self.float64_bytes),
            ("dictionary_header_bytes", self.dictionary_header_bytes),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

    @property
    def node_reference_bytes(self) -> int:
        if (
            self.node_reference_mode
            is DestinationIntervalNodeReferenceMode.FULL_PSEUDONYM_128
        ):
            return self.full_node_id_bytes
        return self.shared_index_bytes

    @property
    def quote_entry_bytes(self) -> int:
        # Destination reference + float64 running mean. A reserved float bit
        # pattern can represent UNKNOWN in a future wire format; no extra flag
        # is charged in this research model.
        return self.node_reference_bytes + self.float64_bytes

    def bootstrap_bytes(self, *, node_count: int) -> int:
        if isinstance(node_count, bool) or not isinstance(node_count, int) or node_count <= 0:
            raise ValueError("node_count must be a positive integer")
        if (
            self.node_reference_mode
            is DestinationIntervalNodeReferenceMode.FULL_PSEUDONYM_128
        ):
            return 0
        return self.dictionary_header_bytes + node_count * (
            self.shared_index_bytes + self.full_node_id_bytes
        )


@dataclass(frozen=True, slots=True)
class DestinationIntervalControlReport:
    quote_entry_count: int
    quote_wire_bytes: int
    bootstrap_wire_bytes: int
    evidence_class: str = "model_synthetic"

    @property
    def control_wire_bytes(self) -> int:
        return self.quote_wire_bytes + self.bootstrap_wire_bytes


def account_destination_interval_control(
    strategy: DestinationIntervalStrategy,
    *,
    profile: DestinationIntervalControlProfile,
    node_count: int,
) -> DestinationIntervalControlReport:
    """Account one directed mean-interval quote per non-destination decision."""

    if not isinstance(strategy, DestinationIntervalStrategy):
        raise TypeError("strategy must be DestinationIntervalStrategy")
    if not isinstance(profile, DestinationIntervalControlProfile):
        raise TypeError("profile must be DestinationIntervalControlProfile")
    if isinstance(node_count, bool) or not isinstance(node_count, int) or node_count <= 0:
        raise ValueError("node_count must be a positive integer")

    count = strategy.quote_entry_count
    quote_wire = count * (
        profile.stream_header_bytes + profile.quote_entry_bytes
    )
    return DestinationIntervalControlReport(
        quote_entry_count=count,
        quote_wire_bytes=quote_wire,
        bootstrap_wire_bytes=profile.bootstrap_bytes(node_count=node_count),
    )
