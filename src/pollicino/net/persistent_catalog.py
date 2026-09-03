from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .catalog import (
    BoundedReference,
    BoundedReferenceCatalog,
    CatalogBoundsError,
    CatalogLimits,
    MutationResult,
    ReconcileResult,
    reconcile_and_pull as native_reconcile_and_pull,
)
from .local_persistence import (
    AmbiguousDurableStateError,
    ConcurrentWriterError,
    DualGenerationSnapshotStore,
    FaultInjector,
    FaultStage,
    PERSISTENCE_GENERATIONS,
    PersistenceBoundsError,
    PersistenceCorruptError,
    PersistenceDigestError,
    PersistenceError,
    PersistenceIOError,
    PersistenceStatus,
    PersistenceTruncatedError,
    PersistenceUncertainCommitError,
    PersistenceVersionError,
    PersistentStoreFailStopError,
    _HEADER,
    _PREFIX,
    decode_envelope,
    encode_envelope,
)


LOCAL_PERSISTENCE_MAGIC = b"PRCP5D2R"
LOCAL_PERSISTENCE_VERSION = 1
LOCAL_PERSISTENCE_FORMAT = "pollicino.local-persistent-reference-catalog.v1"
_NATIVE_STATE_OVERHEAD_PER_ITEM = 6
_NATIVE_STATE_HEADER_BYTES = 49


# Compatibility name retained for the exact PX5 public error hierarchy.
PersistentCatalogFailStopError = PersistentStoreFailStopError


@dataclass(frozen=True, slots=True)
class DurableSnapshot:
    generation: int
    payload: bytes
    payload_digest: bytes


def _maximum_native_state_bytes(limits: CatalogLimits) -> int:
    return (
        _NATIVE_STATE_HEADER_BYTES
        + limits.max_catalog_bytes
        + limits.max_catalog_items * _NATIVE_STATE_OVERHEAD_PER_ITEM
    )


def _encode_snapshot(generation: int, payload: bytes, limits: CatalogLimits) -> bytes:
    return encode_envelope(
        magic=LOCAL_PERSISTENCE_MAGIC,
        version=LOCAL_PERSISTENCE_VERSION,
        generation=generation,
        payload=payload,
        max_payload_bytes=_maximum_native_state_bytes(limits),
    )


def _decode_catalog_payload(
    payload: bytes, limits: CatalogLimits
) -> BoundedReferenceCatalog:
    try:
        return BoundedReferenceCatalog.from_canonical_state(payload, limits=limits)
    except CatalogBoundsError as exc:
        raise PersistenceBoundsError(
            "native catalog bounds rejected durable payload"
        ) from exc
    except (TypeError, ValueError) as exc:
        raise PersistenceCorruptError(
            "native catalog rejected durable payload"
        ) from exc


def _decode_snapshot(
    data: bytes, limits: CatalogLimits
) -> tuple[DurableSnapshot, BoundedReferenceCatalog]:
    generation, payload = decode_envelope(
        data,
        magic=LOCAL_PERSISTENCE_MAGIC,
        version=LOCAL_PERSISTENCE_VERSION,
        max_payload_bytes=_maximum_native_state_bytes(limits),
    )
    catalog = _decode_catalog_payload(payload, limits)
    snapshot = DurableSnapshot(generation, payload, catalog.state_digest)
    return snapshot, catalog


class PersistentBoundedReferenceCatalog(BoundedReferenceCatalog):
    """PX3 catalog with shared dual-generation local durability."""

    def __init__(
        self,
        directory: Path | str,
        *,
        limits: CatalogLimits | None = None,
        fault_injector: FaultInjector | None = None,
    ) -> None:
        active_limits = limits if limits is not None else CatalogLimits()
        super().__init__(limits=active_limits)
        self._durable = DualGenerationSnapshotStore[
            BoundedReferenceCatalog
        ](
            directory,
            stem="catalog",
            magic=LOCAL_PERSISTENCE_MAGIC,
            version=LOCAL_PERSISTENCE_VERSION,
            max_payload_bytes=_maximum_native_state_bytes(active_limits),
            decode_payload=lambda payload: _decode_catalog_payload(
                payload, active_limits
            ),
            fault_injector=fault_injector,
        )
        loaded = self._durable.value
        if loaded is not None:
            self._load_into_memory(loaded)

    @property
    def directory(self) -> Path:
        return self._durable.directory

    @property
    def generation(self) -> int:
        return self._durable.generation

    @property
    def open_status(self) -> PersistenceStatus:
        return self._durable.open_status

    @property
    def last_persistence_status(self) -> PersistenceStatus:
        return self._durable.last_status

    @property
    def usable(self) -> bool:
        return self._durable.usable

    def close(self) -> None:
        self._durable.close()

    def __enter__(self) -> PersistentBoundedReferenceCatalog:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _load_into_memory(self, catalog: BoundedReferenceCatalog) -> None:
        offset = 0
        while offset < len(catalog):
            page = catalog.full_reference_list(offset=offset)
            super().add_many(page)
            offset += len(page)

    def _ensure_usable(self) -> None:
        try:
            self._durable.ensure_usable()
        except PersistentStoreFailStopError as exc:
            raise PersistentCatalogFailStopError(str(exc)) from exc

    def _staged_clone(self) -> BoundedReferenceCatalog:
        return BoundedReferenceCatalog.from_canonical_state(
            super().canonical_state(), limits=self.limits
        )

    def add(self, entry: BoundedReference) -> MutationResult:
        return self.add_many((entry,))[0]

    def add_many(
        self, entries: Iterable[BoundedReference]
    ) -> tuple[MutationResult, ...]:
        self._ensure_usable()
        pending = tuple(entries)
        candidate = self._staged_clone()
        results = candidate.add_many(pending)
        if not any(result is MutationResult.ADDED for result in results):
            return results
        self._durable.commit(candidate.canonical_state())
        super().add_many(pending)
        return results

    def remove(self, logical_key: bytes) -> BoundedReference | None:
        self._ensure_usable()
        candidate = self._staged_clone()
        removed = candidate.remove(logical_key)
        if removed is None:
            return None
        self._durable.commit(candidate.canonical_state())
        return super().remove(logical_key)

    def get(self, logical_key: bytes) -> BoundedReference:
        self._ensure_usable()
        return super().get(logical_key)

    def __len__(self) -> int:
        self._ensure_usable()
        return super().__len__()

    def __contains__(self, logical_key: object) -> bool:
        self._ensure_usable()
        return super().__contains__(logical_key)

    @property
    def payload_bytes(self) -> int:
        self._ensure_usable()
        return super().payload_bytes

    def sorted_logical_ids(
        self, *, offset: int = 0, limit: int | None = None
    ) -> tuple[bytes, ...]:
        self._ensure_usable()
        return super().sorted_logical_ids(offset=offset, limit=limit)

    def full_reference_list(
        self, *, offset: int = 0, limit: int | None = None
    ) -> tuple[BoundedReference, ...]:
        self._ensure_usable()
        return super().full_reference_list(offset=offset, limit=limit)

    def receiver_known_ids(
        self, advertised_keys: Sequence[bytes]
    ) -> tuple[bytes, ...]:
        self._ensure_usable()
        return super().receiver_known_ids(advertised_keys)

    def receiver_unknown_ids(
        self, advertised_keys: Sequence[bytes]
    ) -> tuple[bytes, ...]:
        self._ensure_usable()
        return super().receiver_unknown_ids(advertised_keys)

    def pull_selected(
        self, selected_keys: Sequence[bytes]
    ) -> tuple[BoundedReference, ...]:
        self._ensure_usable()
        return super().pull_selected(selected_keys)

    def canonical_state(self) -> bytes:
        self._ensure_usable()
        return super().canonical_state()

    @property
    def state_digest(self) -> bytes:
        self._ensure_usable()
        return super().state_digest


def persist_reconcile_and_pull(
    sender: BoundedReferenceCatalog,
    receiver: PersistentBoundedReferenceCatalog,
    *,
    advertised_keys: Sequence[bytes],
    selected_keys: Sequence[bytes] | None = None,
) -> ReconcileResult:
    if not isinstance(sender, BoundedReferenceCatalog):
        raise TypeError("sender must be BoundedReferenceCatalog")
    if not isinstance(receiver, PersistentBoundedReferenceCatalog):
        raise TypeError("receiver must be PersistentBoundedReferenceCatalog")
    staged_receiver = BoundedReferenceCatalog.from_canonical_state(
        receiver.canonical_state(), limits=receiver.limits
    )
    result = native_reconcile_and_pull(
        sender,
        staged_receiver,
        advertised_keys=advertised_keys,
        selected_keys=selected_keys,
    )
    persisted_results = receiver.add_many(result.pulled_references)
    return ReconcileResult(
        advertised_keys=result.advertised_keys,
        receiver_known_keys=result.receiver_known_keys,
        candidate_keys=result.candidate_keys,
        selected_keys=result.selected_keys,
        pulled_references=result.pulled_references,
        mutation_results=persisted_results,
    )
