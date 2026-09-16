from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Sequence

from .bearer import BearerProfile
from .bundle import CustodyLedger, TransferCallable
from .fair_scheduling import (
    BearerSchedulingPolicy,
    BearerSchedulingReport,
    FairSchedulerState,
    schedule_fair_bearer_contact,
)
from .scheduling import ContactSchedulingPolicy, ScheduledBundle
from .store import reconstruct_from_store
from .store_forward import ForwardPeer


@dataclass(frozen=True, slots=True)
class SyntheticContactWindow:
    """One explicitly synthetic intermittent encounter.

    ``duration_seconds`` describes scenario time only. It is not converted into
    capacity by this layer. ``logical_source_byte_budget`` is an independent
    policy input until a future physical-evidence adapter establishes a measured
    relationship between contact conditions and useful transferable bytes.
    """

    encounter_id: str
    source_id: str
    target_id: str
    bearer_id: str
    start_s: int
    duration_seconds: int
    logical_source_byte_budget: int
    transfer_id_base: int

    def __post_init__(self) -> None:
        for name, value in (
            ("encounter_id", self.encounter_id),
            ("source_id", self.source_id),
            ("target_id", self.target_id),
            ("bearer_id", self.bearer_id),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a non-empty string")
        if self.source_id == self.target_id:
            raise ValueError("source_id and target_id must differ")
        for name, value in (
            ("start_s", self.start_s),
            ("duration_seconds", self.duration_seconds),
            ("logical_source_byte_budget", self.logical_source_byte_budget),
            ("transfer_id_base", self.transfer_id_base),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.transfer_id_base > 0xFFFFFFFF:
            raise ValueError("transfer_id_base must fit in an unsigned 32-bit integer")


@dataclass(frozen=True, slots=True)
class SyntheticWindowReport:
    encounter_id: str
    source_id: str
    target_id: str
    bearer_id: str
    start_s: int
    duration_seconds: int
    logical_source_byte_budget: int
    duration_drives_budget: bool
    scheduling: BearerSchedulingReport

    @property
    def used_source_bytes(self) -> int:
        return self.scheduling.scheduling.used_source_bytes

    @property
    def remaining_source_bytes(self) -> int:
        return self.scheduling.scheduling.remaining_source_bytes

    @property
    def total_wire_bytes(self) -> int:
        return self.scheduling.total_wire_bytes


@dataclass(frozen=True, slots=True)
class BundlePropagationState:
    bundle_id: str
    label: str | None
    complete_peer_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SyntheticNetworkReport:
    windows: tuple[SyntheticWindowReport, ...]
    propagation: tuple[BundlePropagationState, ...]

    @property
    def total_logical_source_byte_budget(self) -> int:
        return sum(item.logical_source_byte_budget for item in self.windows)

    @property
    def used_source_bytes(self) -> int:
        return sum(item.used_source_bytes for item in self.windows)

    @property
    def total_wire_bytes(self) -> int:
        return sum(item.total_wire_bytes for item in self.windows)

    @property
    def utilization(self) -> float:
        total = self.total_logical_source_byte_budget
        return 0.0 if total == 0 else self.used_source_bytes / total

    def propagation_for_label(self, label: str) -> BundlePropagationState:
        for item in self.propagation:
            if item.label == label:
                return item
        raise KeyError(f"bundle label {label!r} is not present in the report")


def _window_policy(
    base: BearerSchedulingPolicy,
    *,
    logical_source_byte_budget: int,
) -> BearerSchedulingPolicy:
    contact = base.contact_policy
    return BearerSchedulingPolicy(
        bearer_id=base.bearer_id,
        contact_policy=ContactSchedulingPolicy(
            max_source_bytes=logical_source_byte_budget,
            max_bundles=contact.max_bundles,
            max_chunks_per_bundle=contact.max_chunks_per_bundle,
            prefer_completion=contact.prefer_completion,
        ),
        fairness_policy=base.fairness_policy,
    )


def _complete_at_peer(item: ScheduledBundle, peer: ForwardPeer) -> bool:
    manifest = item.manifest
    if not peer.store.has(manifest.fingerprint):
        return False
    if not all(peer.store.has(ref.sha256_digest) for ref in manifest.chunks):
        return False
    reconstruct_from_store(manifest, peer.store)
    return True


def run_synthetic_contact_windows(
    bundles: Sequence[ScheduledBundle],
    *,
    peers: Mapping[str, ForwardPeer],
    ledger: CustodyLedger,
    windows: Sequence[SyntheticContactWindow],
    bearers: Mapping[str, BearerProfile],
    scheduling_policies: Mapping[str, BearerSchedulingPolicy],
    scheduler_states: MutableMapping[str, FairSchedulerState],
    transmitters: Mapping[str, TransferCallable] | None = None,
) -> SyntheticNetworkReport:
    """Execute a deterministic multi-relay sequence of synthetic contact windows.

    Scenario duration and logical byte budget remain independent inputs. This
    function is useful for policy development before hardware measurements, but
    its results must not be presented as measured LoRa/BLE/Wi-Fi/Internet
    contact capacity.
    """

    if not isinstance(ledger, CustodyLedger):
        raise TypeError("ledger must be CustodyLedger")
    transmitter_map = {} if transmitters is None else transmitters

    seen_encounters: set[str] = set()
    ordered = sorted(windows, key=lambda item: (item.start_s, item.encounter_id))
    reports: list[SyntheticWindowReport] = []

    for window in ordered:
        if not isinstance(window, SyntheticContactWindow):
            raise TypeError("windows must contain SyntheticContactWindow values")
        if window.encounter_id in seen_encounters:
            raise ValueError("synthetic contact window encounter IDs must be unique")
        seen_encounters.add(window.encounter_id)
        try:
            source = peers[window.source_id]
            target = peers[window.target_id]
        except KeyError as exc:
            raise KeyError(f"contact window references unknown peer: {exc.args[0]}") from exc
        try:
            bearer = bearers[window.bearer_id]
        except KeyError as exc:
            raise KeyError(f"contact window references unknown bearer: {window.bearer_id}") from exc
        try:
            base_policy = scheduling_policies[window.bearer_id]
        except KeyError as exc:
            raise KeyError(
                f"contact window has no scheduling policy for bearer: {window.bearer_id}"
            ) from exc
        state = scheduler_states.get(window.source_id)
        if state is None:
            state = FairSchedulerState()
            scheduler_states[window.source_id] = state

        scheduling = schedule_fair_bearer_contact(
            bundles,
            source=source,
            target=target,
            ledger=ledger,
            state=state,
            bearer=bearer,
            policy=_window_policy(
                base_policy,
                logical_source_byte_budget=window.logical_source_byte_budget,
            ),
            transfer_id_base=window.transfer_id_base,
            encounter_id=window.encounter_id,
            now_s=window.start_s,
            transmitter=transmitter_map.get(window.bearer_id),
        )
        reports.append(
            SyntheticWindowReport(
                encounter_id=window.encounter_id,
                source_id=window.source_id,
                target_id=window.target_id,
                bearer_id=window.bearer_id,
                start_s=window.start_s,
                duration_seconds=window.duration_seconds,
                logical_source_byte_budget=window.logical_source_byte_budget,
                duration_drives_budget=False,
                scheduling=scheduling,
            )
        )

    propagation: list[BundlePropagationState] = []
    for item in bundles:
        if not isinstance(item, ScheduledBundle):
            raise TypeError("bundles must contain ScheduledBundle values")
        complete_peers = tuple(
            peer_id
            for peer_id in sorted(peers)
            if _complete_at_peer(item, peers[peer_id])
        )
        propagation.append(
            BundlePropagationState(
                bundle_id=item.bundle.bundle_id.hex(),
                label=item.label,
                complete_peer_ids=complete_peers,
            )
        )

    return SyntheticNetworkReport(
        windows=tuple(reports),
        propagation=tuple(propagation),
    )
