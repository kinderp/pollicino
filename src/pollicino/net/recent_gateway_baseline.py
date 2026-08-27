from __future__ import annotations

from dataclasses import dataclass, field
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
class PriorGatewayEncounter:
    peer_id: str
    destination_id: str
    observed_at_s: int

    def __post_init__(self) -> None:
        _require_id("peer_id", self.peer_id)
        _require_id("destination_id", self.destination_id)
        if self.peer_id == self.destination_id:
            raise ValueError("peer_id must differ from destination_id")
        if isinstance(self.observed_at_s, bool) or not isinstance(self.observed_at_s, int) or self.observed_at_s < 0:
            raise ValueError("observed_at_s must be a non-negative integer")


@dataclass(slots=True)
class RecentGatewayEncounterStrategy:
    """Minimal local-history routing baseline for a fixed gateway set.

    Each node remembers only the timestamp of its most recent *direct* encounter
    with a final destination.  During a non-destination encounter, forward to
    the target only when the target's direct-gateway observation is newer than
    the source's.  A target with any direct-gateway history beats a source with
    none. Equal/unknown evidence does not trigger replication.

    The strategy deliberately has no transitivity, route graph, queue model,
    replica gossip, probability model or future topology knowledge. It exists
    as an Occam baseline for use cases where human mobility may make recent
    direct gateway contact informative.
    """

    destination_ids: tuple[str, ...]
    prior_encounters: tuple[PriorGatewayEncounter, ...] = ()
    strategy_id: str = "recent-gateway-encounter"
    _last_gateway: dict[tuple[str, str], int] = field(default_factory=dict, init=False, repr=False)
    _run_ledger: CustodyLedger | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.destination_ids, tuple) or not self.destination_ids:
            raise ValueError("destination_ids must be a non-empty tuple")
        for destination_id in self.destination_ids:
            _require_id("destination_id", destination_id)
        if len(self.destination_ids) != len(set(self.destination_ids)):
            raise ValueError("destination_ids must be unique")
        _require_id("strategy_id", self.strategy_id)
        if not isinstance(self.prior_encounters, tuple) or not all(
            isinstance(item, PriorGatewayEncounter) for item in self.prior_encounters
        ):
            raise TypeError("prior_encounters must contain PriorGatewayEncounter values")
        destination_set = set(self.destination_ids)
        for item in self.prior_encounters:
            if item.destination_id not in destination_set:
                raise ValueError("prior encounter references an unknown destination")

    def _ensure_run(self, ledger: CustodyLedger) -> None:
        if self._run_ledger is ledger:
            return
        self._run_ledger = ledger
        self._last_gateway.clear()
        for item in sorted(
            self.prior_encounters,
            key=lambda value: (value.observed_at_s, value.peer_id, value.destination_id),
        ):
            self._last_gateway[(item.peer_id, item.destination_id)] = item.observed_at_s

    def _observe_direct_destination_contact(
        self,
        source_id: str,
        target_id: str,
        *,
        now_s: int,
    ) -> None:
        destinations = set(self.destination_ids)
        if target_id in destinations and source_id not in destinations:
            self._last_gateway[(source_id, target_id)] = now_s
        if source_id in destinations and target_id not in destinations:
            self._last_gateway[(target_id, source_id)] = now_s

    def latest_gateway_encounter(self, peer_id: str) -> int | None:
        _require_id("peer_id", peer_id)
        values = [
            observed_at_s
            for (candidate_id, _destination_id), observed_at_s in self._last_gateway.items()
            if candidate_id == peer_id
        ]
        return None if not values else max(values)

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
        self._ensure_run(ledger)
        if self.prior_encounters and window.start_s <= max(
            item.observed_at_s for item in self.prior_encounters
        ):
            raise ValueError("prior gateway encounters must precede routing windows")

        # Direct delivery is always allowed. Record the direct contact after the
        # decision so a current encounter with D cannot retroactively influence
        # an earlier forwarding decision.
        if target.peer_id in self.destination_ids:
            selected = tuple(bundles)
            self._observe_direct_destination_contact(
                source.peer_id, target.peer_id, now_s=window.start_s
            )
            return selected

        source_score = self.latest_gateway_encounter(source.peer_id)
        target_score = self.latest_gateway_encounter(target.peer_id)
        self._observe_direct_destination_contact(
            source.peer_id, target.peer_id, now_s=window.start_s
        )

        if target_score is None:
            return ()
        if source_score is None or target_score > source_score:
            return tuple(bundles)
        return ()


@dataclass(frozen=True, slots=True)
class RecentGatewayControlProfile:
    """Research-only byte model for exchanging the minimal recency score.

    For one non-destination encounter, both peers expose one nullable recency
    value. Destination identity is assumed to be scenario/campaign context; it
    is not repeated in each score. Authentication and retransmission are not
    modeled here.
    """

    stream_header_bytes: int = 4
    presence_flag_bytes: int = 1
    timestamp_bytes: int = 8

    def __post_init__(self) -> None:
        for name, value in (
            ("stream_header_bytes", self.stream_header_bytes),
            ("presence_flag_bytes", self.presence_flag_bytes),
            ("timestamp_bytes", self.timestamp_bytes),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

    @property
    def bidirectional_encounter_wire_bytes(self) -> int:
        return self.stream_header_bytes + 2 * (
            self.presence_flag_bytes + self.timestamp_bytes
        )


def recent_gateway_control_wire_bytes(
    *,
    non_destination_encounter_count: int,
    profile: RecentGatewayControlProfile = RecentGatewayControlProfile(),
) -> int:
    if (
        isinstance(non_destination_encounter_count, bool)
        or not isinstance(non_destination_encounter_count, int)
        or non_destination_encounter_count < 0
    ):
        raise ValueError("non_destination_encounter_count must be a non-negative integer")
    if not isinstance(profile, RecentGatewayControlProfile):
        raise TypeError("profile must be RecentGatewayControlProfile")
    return non_destination_encounter_count * profile.bidirectional_encounter_wire_bytes
