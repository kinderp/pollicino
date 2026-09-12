from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Sequence

from .bearer import BearerProfile
from .bundle import CustodyLedger
from .contact_windows import SyntheticContactWindow
from .scheduling import ScheduledBundle
from .store_forward import ForwardPeer


def _require_id(name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _require_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class DestinationServiceObservation:
    """One explicit direct destination contact and its useful byte opportunity."""

    peer_id: str
    destination_id: str
    observed_at_s: int
    opportunity_bytes: int

    def __post_init__(self) -> None:
        _require_id("peer_id", self.peer_id)
        _require_id("destination_id", self.destination_id)
        if self.peer_id == self.destination_id:
            raise ValueError("service observation peer must differ from destination")
        if (
            isinstance(self.observed_at_s, bool)
            or not isinstance(self.observed_at_s, int)
            or self.observed_at_s < 0
        ):
            raise ValueError("observed_at_s must be a non-negative integer")
        _require_positive_int("opportunity_bytes", self.opportunity_bytes)


@dataclass(slots=True)
class DestinationServiceStrategy:
    """Minimal frequency x opportunity routing baseline for one destination.

    For each node, keep only:
    - the running mean direct inter-meeting interval with the destination;
    - the running mean *explicitly observed* useful bytes in those source->destination
      opportunities.

    For a bundle of size S, estimate:

        service_seconds = mean_interval_seconds * ceil(S / mean_opportunity_bytes)

    and forward only when the encountered target has a smaller estimate than the
    current source. Unknown target state fails closed.

    This intentionally ignores phase/time-to-next-contact, route transitivity,
    replica gossip, bytes ahead in a queue, delivery probability and future
    contacts. It exists as the simplest control after Destination Interval fails
    on heterogeneous transfer opportunities.
    """

    destination_id: str
    prior_observations: tuple[DestinationServiceObservation, ...] = ()
    strategy_id: str = "destination-service"
    _run_ledger: CustodyLedger | None = field(default=None, init=False, repr=False)
    _last_seen: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    _mean_interval_s: dict[str, float] = field(default_factory=dict, init=False, repr=False)
    _interval_sample_count: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    _mean_opportunity_bytes: dict[str, float] = field(default_factory=dict, init=False, repr=False)
    _opportunity_sample_count: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    quote_entry_count: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        _require_id("destination_id", self.destination_id)
        _require_id("strategy_id", self.strategy_id)
        if not isinstance(self.prior_observations, tuple):
            raise TypeError("prior_observations must be a tuple")
        if not all(
            isinstance(item, DestinationServiceObservation)
            for item in self.prior_observations
        ):
            raise TypeError(
                "prior_observations must contain DestinationServiceObservation values"
            )
        if any(
            item.destination_id != self.destination_id
            for item in self.prior_observations
        ):
            raise ValueError("all prior observations must target destination_id")

    def _observe_interval(self, peer_id: str, *, now_s: int) -> None:
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

    def _observe_opportunity(self, peer_id: str, *, opportunity_bytes: int) -> None:
        _require_positive_int("opportunity_bytes", opportunity_bytes)
        previous_count = self._opportunity_sample_count.get(peer_id, 0)
        previous_mean = self._mean_opportunity_bytes.get(peer_id, 0.0)
        count = previous_count + 1
        mean = (
            float(opportunity_bytes)
            if previous_count == 0
            else previous_mean + (opportunity_bytes - previous_mean) / count
        )
        self._opportunity_sample_count[peer_id] = count
        self._mean_opportunity_bytes[peer_id] = float(mean)

    def _observe_destination_contact(
        self,
        peer_id: str,
        *,
        now_s: int,
        opportunity_bytes: int | None,
    ) -> None:
        self._observe_interval(peer_id, now_s=now_s)
        if opportunity_bytes is not None:
            self._observe_opportunity(peer_id, opportunity_bytes=opportunity_bytes)

    def _ensure_run(self, ledger: CustodyLedger, *, now_s: int) -> None:
        if self._run_ledger is ledger:
            return
        self._run_ledger = ledger
        self._last_seen.clear()
        self._mean_interval_s.clear()
        self._interval_sample_count.clear()
        self._mean_opportunity_bytes.clear()
        self._opportunity_sample_count.clear()
        self.quote_entry_count = 0
        for observation in sorted(
            self.prior_observations,
            key=lambda item: (item.observed_at_s, item.peer_id),
        ):
            if observation.observed_at_s >= now_s:
                raise ValueError(
                    "destination-service prior observations must precede the first routing window"
                )
            self._observe_destination_contact(
                observation.peer_id,
                now_s=observation.observed_at_s,
                opportunity_bytes=observation.opportunity_bytes,
            )

    def mean_interval_seconds(self, peer_id: str) -> float | None:
        _require_id("peer_id", peer_id)
        return self._mean_interval_s.get(peer_id)

    def mean_opportunity_bytes(self, peer_id: str) -> float | None:
        _require_id("peer_id", peer_id)
        return self._mean_opportunity_bytes.get(peer_id)

    def service_seconds(self, item: ScheduledBundle, peer_id: str) -> float | None:
        if not isinstance(item, ScheduledBundle):
            raise TypeError("item must be ScheduledBundle")
        _require_id("peer_id", peer_id)
        interval = self._mean_interval_s.get(peer_id)
        opportunity = self._mean_opportunity_bytes.get(peer_id)
        if interval is None or opportunity is None or opportunity <= 0:
            return None
        meetings_needed = max(1, math.ceil(item.manifest.object_size / opportunity))
        return float(interval) * meetings_needed

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
            # The synthetic window's logical byte budget is explicit source->D
            # opportunity evidence. It is not derived from duration or bearer kind.
            self._observe_destination_contact(
                source.peer_id,
                now_s=window.start_s,
                opportunity_bytes=window.logical_source_byte_budget,
            )
            return tuple(bundles)

        if source.peer_id == self.destination_id:
            # Encounter timing is symmetric, but this D->target window does not
            # tell us target->D useful byte opportunity; update timing only.
            self._observe_destination_contact(
                target.peer_id,
                now_s=window.start_s,
                opportunity_bytes=None,
            )
            return ()

        self.quote_entry_count += 1
        selected: list[ScheduledBundle] = []
        for item in bundles:
            target_service = self.service_seconds(item, target.peer_id)
            if target_service is None:
                continue
            source_service = self.service_seconds(item, source.peer_id)
            if source_service is None or target_service < source_service:
                selected.append(item)
        return tuple(selected)


class DestinationServiceNodeReferenceMode(str, Enum):
    FULL_PSEUDONYM_128 = "full_pseudonym_128"
    SHARED_U16_INDEX = "shared_u16_index"


@dataclass(frozen=True, slots=True)
class DestinationServiceControlProfile:
    node_reference_mode: DestinationServiceNodeReferenceMode
    stream_header_bytes: int = 4
    full_node_id_bytes: int = 16
    shared_index_bytes: int = 2
    float64_bytes: int = 8
    dictionary_header_bytes: int = 4

    def __post_init__(self) -> None:
        if not isinstance(
            self.node_reference_mode, DestinationServiceNodeReferenceMode
        ):
            raise TypeError(
                "node_reference_mode must be DestinationServiceNodeReferenceMode"
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
            is DestinationServiceNodeReferenceMode.FULL_PSEUDONYM_128
        ):
            return self.full_node_id_bytes
        return self.shared_index_bytes

    @property
    def quote_entry_bytes(self) -> int:
        # Target reference + mean interval + mean useful opportunity.
        return self.node_reference_bytes + 2 * self.float64_bytes

    def bootstrap_bytes(self, *, node_count: int) -> int:
        if isinstance(node_count, bool) or not isinstance(node_count, int) or node_count <= 0:
            raise ValueError("node_count must be a positive integer")
        if (
            self.node_reference_mode
            is DestinationServiceNodeReferenceMode.FULL_PSEUDONYM_128
        ):
            return 0
        return self.dictionary_header_bytes + node_count * (
            self.shared_index_bytes + self.full_node_id_bytes
        )


@dataclass(frozen=True, slots=True)
class DestinationServiceControlReport:
    quote_entry_count: int
    quote_wire_bytes: int
    bootstrap_wire_bytes: int
    evidence_class: str = "model_synthetic"

    @property
    def control_wire_bytes(self) -> int:
        return self.quote_wire_bytes + self.bootstrap_wire_bytes


def account_destination_service_control(
    strategy: DestinationServiceStrategy,
    *,
    profile: DestinationServiceControlProfile,
    node_count: int,
) -> DestinationServiceControlReport:
    """Account one directed interval+opportunity quote per non-D encounter."""

    if not isinstance(strategy, DestinationServiceStrategy):
        raise TypeError("strategy must be DestinationServiceStrategy")
    if not isinstance(profile, DestinationServiceControlProfile):
        raise TypeError("profile must be DestinationServiceControlProfile")
    if isinstance(node_count, bool) or not isinstance(node_count, int) or node_count <= 0:
        raise ValueError("node_count must be a positive integer")

    count = strategy.quote_entry_count
    quote_wire = count * (
        profile.stream_header_bytes + profile.quote_entry_bytes
    )
    return DestinationServiceControlReport(
        quote_entry_count=count,
        quote_wire_bytes=quote_wire,
        bootstrap_wire_bytes=profile.bootstrap_bytes(node_count=node_count),
    )
