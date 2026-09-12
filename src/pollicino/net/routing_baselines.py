from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .bearer import BearerProfile
from .bundle import CustodyLedger
from .contact_windows import SyntheticContactWindow
from .scheduling import ScheduledBundle
from .store_forward import ForwardPeer


def _require_strategy_id(value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError("strategy_id must be a non-empty string")


def _validate_destinations(value: tuple[str, ...]) -> None:
    if not isinstance(value, tuple) or not value:
        raise ValueError("destination_ids must be a non-empty tuple")
    if any(not isinstance(item, str) or not item for item in value):
        raise ValueError("destination_ids must contain non-empty strings")
    if len(value) != len(set(value)):
        raise ValueError("destination_ids must be unique")


@dataclass(frozen=True, slots=True)
class DirectDeliveryStrategy:
    """Forward only when the encountered peer is a final destination.

    This is the simplest DTN baseline: no relay ever receives a copy merely to
    help future delivery. ``destination_ids`` is explicit scenario/application
    knowledge supplied to the strategy; it is not inferred from topology.
    """

    destination_ids: tuple[str, ...]
    strategy_id: str = "direct-delivery"

    def __post_init__(self) -> None:
        _require_strategy_id(self.strategy_id)
        _validate_destinations(self.destination_ids)

    def select_bundles(
        self,
        bundles: Sequence[ScheduledBundle],
        *,
        target: ForwardPeer,
        **_: object,
    ) -> tuple[ScheduledBundle, ...]:
        if target.peer_id not in self.destination_ids:
            return ()
        return tuple(bundles)


@dataclass(frozen=True, slots=True)
class EpidemicStrategy:
    """Replicate every eligible bundle at every encounter.

    This implements the canonical Epidemic *forwarding eligibility* rule inside
    the existing PollicinoNet experiment harness. The underlying governed
    transfer remains Pollicino-specific: it suppresses chunks already present
    at the receiver and accounts PCM1/PNA1/PNB1/PNC1/ACK/retry bytes.

    Therefore this is a routing-behaviour baseline, not a claim to reproduce
    every control packet of the original Epidemic Routing implementation. A
    future protocol-overhead experiment may model an explicit summary-vector
    exchange separately if a research question requires it.
    """

    strategy_id: str = "epidemic"

    def __post_init__(self) -> None:
        _require_strategy_id(self.strategy_id)

    def select_bundles(
        self,
        bundles: Sequence[ScheduledBundle],
        **_: object,
    ) -> tuple[ScheduledBundle, ...]:
        return tuple(bundles)


@dataclass(slots=True)
class _SprayReservation:
    bundle_id: str
    source: ForwardPeer
    target: ForwardPeer
    copies: int
    target_chunk_count_before: int
    started_at_s: int


@dataclass(slots=True)
class BinarySprayAndWaitStrategy:
    """Binary Spray-and-Wait adapted to Pollicino chunked EXACT objects.

    Each seeded bundle starts with ``initial_copies`` logical copy tokens.
    During the spray phase a carrier with n>1 tokens reserves floor(n/2) for
    an encountered non-destination peer and keeps the remainder. Once that
    peer owns a complete verified object, the reserved tokens become active
    there. A carrier with one token enters the wait phase and may forward only
    to a final destination.

    Reservation is needed because Pollicino can transfer one exact object over
    several bounded contacts whereas classic Spray-and-Wait assumes an atomic
    message copy. Reservations never increase the global copy-token budget. If
    a selected contact makes no chunk progress, the reservation is released on
    the next observed encounter.
    """

    destination_ids: tuple[str, ...]
    initial_copies: int = 4
    strategy_id: str = "binary-spray-and-wait"
    _run_ledger: CustodyLedger | None = field(default=None, init=False, repr=False)
    _tokens: dict[tuple[str, str], int] = field(default_factory=dict, init=False, repr=False)
    _reservations: list[_SprayReservation] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        _validate_destinations(self.destination_ids)
        _require_strategy_id(self.strategy_id)
        if isinstance(self.initial_copies, bool) or not isinstance(self.initial_copies, int):
            raise ValueError("initial_copies must be an integer")
        if self.initial_copies < 1:
            raise ValueError("initial_copies must be at least 1")

    @staticmethod
    def _bundle_id(item: ScheduledBundle) -> str:
        return item.bundle.bundle_id.hex()

    @staticmethod
    def _chunk_count(item: ScheduledBundle, peer: ForwardPeer) -> int:
        return sum(
            1 for ref in item.manifest.chunks if peer.store.has(ref.sha256_digest)
        )

    @classmethod
    def _complete(cls, item: ScheduledBundle, peer: ForwardPeer) -> bool:
        return cls._chunk_count(item, peer) == len(item.manifest.chunks)

    def _ensure_run(self, ledger: CustodyLedger) -> None:
        if self._run_ledger is ledger:
            return
        self._run_ledger = ledger
        self._tokens.clear()
        self._reservations.clear()

    def _seed_source_if_needed(
        self,
        item: ScheduledBundle,
        source: ForwardPeer,
        ledger: CustodyLedger,
    ) -> None:
        bundle_id = self._bundle_id(item)
        key = (bundle_id, source.peer_id)
        if key in self._tokens:
            return
        custody = ledger.get(item.bundle.bundle_id, source.peer_id)
        if custody is not None and custody.complete and custody.hop_count == 0:
            self._tokens[key] = self.initial_copies

    def _reconcile_reservations(
        self,
        bundles: Sequence[ScheduledBundle],
        *,
        now_s: int,
    ) -> None:
        by_id = {self._bundle_id(item): item for item in bundles}
        keep: list[_SprayReservation] = []
        for reservation in self._reservations:
            item = by_id.get(reservation.bundle_id)
            if item is None:
                continue
            source_key = (reservation.bundle_id, reservation.source.peer_id)
            target_key = (reservation.bundle_id, reservation.target.peer_id)

            if self._tokens.get(target_key, 0) > 0:
                self._tokens[source_key] = (
                    self._tokens.get(source_key, 0) + reservation.copies
                )
                continue

            current_chunks = self._chunk_count(item, reservation.target)
            if current_chunks == len(item.manifest.chunks):
                self._tokens[target_key] = reservation.copies
                continue

            if (
                now_s > reservation.started_at_s
                and current_chunks == reservation.target_chunk_count_before
            ):
                self._tokens[source_key] = (
                    self._tokens.get(source_key, 0) + reservation.copies
                )
                continue

            keep.append(reservation)
        self._reservations = keep

    def _reservation_for(
        self,
        bundle_id: str,
        source_id: str,
        target_id: str,
    ) -> _SprayReservation | None:
        for reservation in self._reservations:
            if (
                reservation.bundle_id == bundle_id
                and reservation.source.peer_id == source_id
                and reservation.target.peer_id == target_id
            ):
                return reservation
        return None

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
        self._reconcile_reservations(bundles, now_s=window.start_s)
        selected: list[ScheduledBundle] = []

        for item in bundles:
            self._seed_source_if_needed(item, source, ledger)
            bundle_id = self._bundle_id(item)
            source_key = (bundle_id, source.peer_id)
            source_tokens = self._tokens.get(source_key, 0)
            if source_tokens <= 0:
                continue

            if target.peer_id in self.destination_ids:
                selected.append(item)
                continue

            pending = self._reservation_for(
                bundle_id, source.peer_id, target.peer_id
            )
            if pending is not None:
                selected.append(item)
                continue

            target_key = (bundle_id, target.peer_id)
            if self._tokens.get(target_key, 0) > 0 or self._complete(item, target):
                continue
            if source_tokens <= 1:
                continue
            if window.logical_source_byte_budget <= 0:
                continue

            missing_lengths = [
                ref.length
                for ref in item.manifest.chunks
                if source.store.has(ref.sha256_digest)
                and not target.store.has(ref.sha256_digest)
            ]
            if (
                not missing_lengths
                or min(missing_lengths) > window.logical_source_byte_budget
            ):
                continue

            copies = source_tokens // 2
            self._tokens[source_key] = source_tokens - copies
            self._reservations.append(
                _SprayReservation(
                    bundle_id=bundle_id,
                    source=source,
                    target=target,
                    copies=copies,
                    target_chunk_count_before=self._chunk_count(item, target),
                    started_at_s=window.start_s,
                )
            )
            selected.append(item)

        return tuple(selected)

    def copies_for(self, item: ScheduledBundle, peer_id: str) -> int:
        return self._tokens.get((self._bundle_id(item), peer_id), 0)

    def active_copy_tokens(self, item: ScheduledBundle) -> int:
        bundle_id = self._bundle_id(item)
        return sum(
            value
            for (candidate, _peer_id), value in self._tokens.items()
            if candidate == bundle_id
        )

    def reserved_copy_tokens(self, item: ScheduledBundle) -> int:
        bundle_id = self._bundle_id(item)
        return sum(
            reservation.copies
            for reservation in self._reservations
            if reservation.bundle_id == bundle_id
        )

    def total_copy_tokens(self, item: ScheduledBundle) -> int:
        return self.active_copy_tokens(item) + self.reserved_copy_tokens(item)


@dataclass(slots=True)
class ProphetStrategy:
    """RFC-6693-inspired PRoPHET baseline for synthetic comparison.

    The model implements the RFC's three core ideas: direct-encounter increase,
    time aging and transitive predictability. RFC 6693 recommended starting
    parameters are the defaults here. ``p_encounter_max`` is used as a fixed
    encounter scaling value after the first/forgotten encounter; a later
    trace-calibration experiment may replace it with an interval-aware
    encounter function.

    This class models routing knowledge in memory. It does *not* add PRoPHET
    RIB/control exchange bytes to Pollicino TRC, so traffic-cost conclusions
    involving this baseline remain incomplete until routing-control accounting
    is modeled explicitly.
    """

    destination_ids: tuple[str, ...]
    p_encounter_max: float = 0.7
    p_encounter_first: float = 0.5
    p_first_threshold: float = 0.1
    beta: float = 0.9
    gamma: float = 0.999
    delta: float = 0.01
    time_unit_seconds: float = 1.0
    forwarding_margin: float = 0.0
    strategy_id: str = "prophet"
    _run_ledger: CustodyLedger | None = field(default=None, init=False, repr=False)
    _predictability: dict[str, dict[str, float]] = field(
        default_factory=dict, init=False, repr=False
    )
    _last_aged_s: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    encounter_update_count: int = field(default=0, init=False)
    transitive_update_count: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        _validate_destinations(self.destination_ids)
        _require_strategy_id(self.strategy_id)
        for name, value in (
            ("p_encounter_max", self.p_encounter_max),
            ("p_encounter_first", self.p_encounter_first),
            ("p_first_threshold", self.p_first_threshold),
            ("beta", self.beta),
            ("gamma", self.gamma),
            ("delta", self.delta),
            ("forwarding_margin", self.forwarding_margin),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0.0 <= float(value) <= 1.0
            ):
                raise ValueError(f"{name} must be in 0..1")
        if self.delta >= 1.0:
            raise ValueError("delta must be below 1")
        if (
            isinstance(self.time_unit_seconds, bool)
            or not isinstance(self.time_unit_seconds, (int, float))
            or self.time_unit_seconds <= 0
        ):
            raise ValueError("time_unit_seconds must be positive")

    def _ensure_run(self, ledger: CustodyLedger) -> None:
        if self._run_ledger is ledger:
            return
        self._run_ledger = ledger
        self._predictability.clear()
        self._last_aged_s.clear()
        self.encounter_update_count = 0
        self.transitive_update_count = 0

    def _ensure_peer(self, peer_id: str) -> dict[str, float]:
        table = self._predictability.setdefault(peer_id, {})
        table[peer_id] = 1.0
        return table

    def _age(self, peer_id: str, now_s: int) -> None:
        table = self._ensure_peer(peer_id)
        previous = self._last_aged_s.get(peer_id)
        if previous is None:
            self._last_aged_s[peer_id] = now_s
            return
        if now_s < previous:
            raise ValueError("PRoPHET encounter time cannot move backwards")
        elapsed = now_s - previous
        if elapsed == 0:
            return
        k = elapsed / float(self.time_unit_seconds)
        factor = float(self.gamma) ** k
        for destination in tuple(table):
            if destination != peer_id:
                table[destination] *= factor
        table[peer_id] = 1.0
        self._last_aged_s[peer_id] = now_s

    def _direct_update(self, source_id: str, target_id: str) -> None:
        table = self._ensure_peer(source_id)
        old = table.get(target_id, 0.0)
        if old < self.p_first_threshold:
            updated = float(self.p_encounter_first)
        else:
            updated = old + (
                1.0 - self.delta - old
            ) * self.p_encounter_max
        table[target_id] = min(1.0 - self.delta, max(0.0, updated))

    def _encounter(self, source_id: str, target_id: str, now_s: int) -> None:
        self._age(source_id, now_s)
        self._age(target_id, now_s)
        self._direct_update(source_id, target_id)
        self._direct_update(target_id, source_id)

        source_table = self._ensure_peer(source_id)
        target_table = self._ensure_peer(target_id)
        source_snapshot = dict(source_table)
        target_snapshot = dict(target_table)
        source_to_target = source_snapshot.get(target_id, 0.0)
        target_to_source = target_snapshot.get(source_id, 0.0)

        for destination, target_value in target_snapshot.items():
            if destination == source_id:
                continue
            candidate = source_to_target * target_value * self.beta
            if candidate > source_table.get(destination, 0.0):
                source_table[destination] = candidate
                self.transitive_update_count += 1

        for destination, source_value in source_snapshot.items():
            if destination == target_id:
                continue
            candidate = target_to_source * source_value * self.beta
            if candidate > target_table.get(destination, 0.0):
                target_table[destination] = candidate
                self.transitive_update_count += 1

        source_table[source_id] = 1.0
        target_table[target_id] = 1.0
        self.encounter_update_count += 1

    def predictability(self, peer_id: str, destination_id: str) -> float:
        if peer_id == destination_id:
            return 1.0
        return self._predictability.get(peer_id, {}).get(destination_id, 0.0)

    def table_snapshot(self) -> dict[str, dict[str, float]]:
        return {
            peer_id: dict(values)
            for peer_id, values in self._predictability.items()
        }

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
        self._encounter(source.peer_id, target.peer_id, window.start_s)

        if target.peer_id in self.destination_ids:
            return tuple(bundles)

        source_score = max(
            self.predictability(source.peer_id, destination)
            for destination in self.destination_ids
        )
        target_score = max(
            self.predictability(target.peer_id, destination)
            for destination in self.destination_ids
        )
        if target_score > source_score + self.forwarding_margin:
            return tuple(bundles)
        return ()
