from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import fcntl
import hashlib
import os
from pathlib import Path
import struct
import tempfile
from typing import Callable, Iterable, Sequence

from .catalog import (
    BoundedReference,
    BoundedReferenceCatalog,
    CatalogBoundsError,
    CatalogLimits,
    MutationResult,
    ReconcileResult,
    reconcile_and_pull as native_reconcile_and_pull,
)


LOCAL_PERSISTENCE_MAGIC = b"PRCP5D2R"
LOCAL_PERSISTENCE_VERSION = 1
LOCAL_PERSISTENCE_FORMAT = "pollicino.local-persistent-reference-catalog.v1"
PERSISTENCE_GENERATIONS = 2
_PREFIX = struct.Struct(">8sBQQ")
_HEADER = struct.Struct(">8sBQQ32s")
_NATIVE_STATE_OVERHEAD_PER_ITEM = 6
_NATIVE_STATE_HEADER_BYTES = 49


class PersistenceStatus(str, Enum):
    NO_DURABLE_STATE = "NO_DURABLE_STATE"
    LOADED_CURRENT_GENERATION = "LOADED_CURRENT_GENERATION"
    RECOVERED_PREVIOUS_GENERATION = "RECOVERED_PREVIOUS_GENERATION"
    PERSIST_COMMITTED = "PERSIST_COMMITTED"


class FaultStage(str, Enum):
    BEFORE_TEMP_CREATE = "BEFORE_TEMP_CREATE"
    DURING_WRITE = "DURING_WRITE"
    AFTER_WRITE_BEFORE_FILE_FSYNC = "AFTER_WRITE_BEFORE_FILE_FSYNC"
    AFTER_FILE_FSYNC_BEFORE_REPLACE = "AFTER_FILE_FSYNC_BEFORE_REPLACE"
    AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC = "AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC"
    AFTER_DIRECTORY_FSYNC_BEFORE_MEMORY_SWAP = "AFTER_DIRECTORY_FSYNC_BEFORE_MEMORY_SWAP"


class PersistenceError(RuntimeError):
    code = "PERSISTENCE_ERROR"


class PersistenceIOError(PersistenceError):
    code = "PERSISTENCE_IO_FAILURE"


class PersistenceCorruptError(PersistenceError):
    code = "PERSISTENCE_CORRUPT"


class PersistenceTruncatedError(PersistenceCorruptError):
    code = "PERSISTENCE_TRUNCATED"


class PersistenceVersionError(PersistenceCorruptError):
    code = "PERSISTENCE_VERSION_UNSUPPORTED"


class PersistenceDigestError(PersistenceCorruptError):
    code = "PERSISTENCE_DIGEST_MISMATCH"


class PersistenceBoundsError(PersistenceCorruptError):
    code = "PERSISTENCE_BOUNDS_VIOLATION"


class AmbiguousDurableStateError(PersistenceCorruptError):
    code = "AMBIGUOUS_DURABLE_STATE"


class ConcurrentWriterError(PersistenceError):
    code = "PERSISTENCE_WRITER_ALREADY_ACTIVE"


class PersistentCatalogFailStopError(PersistenceError):
    code = "PERSISTENCE_REOPEN_REQUIRED"


class PersistenceUncertainCommitError(PersistentCatalogFailStopError):
    code = "PERSISTENCE_UNCERTAIN_COMMIT_REOPEN_REQUIRED"

    def __init__(self, message: str, *, replacement_completed: bool) -> None:
        super().__init__(message)
        self.replacement_completed = replacement_completed


FaultInjector = Callable[[FaultStage], None]


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
    if type(generation) is not int or generation < 1:
        raise PersistenceBoundsError("local generation must be a positive integer")
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")
    if len(payload) > _maximum_native_state_bytes(limits):
        raise PersistenceBoundsError("native catalog payload exceeds persistence bound")
    prefix = _PREFIX.pack(
        LOCAL_PERSISTENCE_MAGIC,
        LOCAL_PERSISTENCE_VERSION,
        generation,
        len(payload),
    )
    digest = hashlib.sha256(prefix + payload).digest()
    return prefix + digest + payload


def _decode_snapshot(data: bytes, limits: CatalogLimits) -> tuple[DurableSnapshot, BoundedReferenceCatalog]:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if len(data) < _HEADER.size:
        raise PersistenceTruncatedError("persistent snapshot header is truncated")
    magic, version, generation, payload_length, digest = _HEADER.unpack_from(data)
    if magic != LOCAL_PERSISTENCE_MAGIC:
        raise PersistenceCorruptError("invalid persistence magic")
    if version != LOCAL_PERSISTENCE_VERSION:
        raise PersistenceVersionError(f"unsupported persistence version: {version}")
    maximum = _maximum_native_state_bytes(limits)
    if payload_length > maximum or len(data) > _HEADER.size + maximum:
        raise PersistenceBoundsError("declared persistent payload exceeds bound")
    if len(data) != _HEADER.size + payload_length:
        raise PersistenceTruncatedError("persistent snapshot length mismatch")
    payload = data[_HEADER.size :]
    prefix = data[: _PREFIX.size]
    if hashlib.sha256(prefix + payload).digest() != digest:
        raise PersistenceDigestError("persistent snapshot digest mismatch")
    if generation < 1:
        raise PersistenceBoundsError("persistent generation is invalid")
    try:
        catalog = BoundedReferenceCatalog.from_canonical_state(payload, limits=limits)
    except CatalogBoundsError as exc:
        raise PersistenceBoundsError("native catalog bounds rejected durable payload") from exc
    except (TypeError, ValueError) as exc:
        raise PersistenceCorruptError("native catalog rejected durable payload") from exc
    return DurableSnapshot(generation, payload, catalog.state_digest), catalog


class PersistentBoundedReferenceCatalog(BoundedReferenceCatalog):
    """Dual-generation durable wrapper preserving native PX3 semantics.

    One process holds an exclusive advisory lock for the instance lifetime.
    Any fault after atomic replacement puts the instance into fail-stop state;
    reopening establishes the durable authority before more operations.
    """

    def __init__(
        self,
        directory: Path | str,
        *,
        limits: CatalogLimits | None = None,
        fault_injector: FaultInjector | None = None,
    ) -> None:
        active_limits = limits if limits is not None else CatalogLimits()
        super().__init__(limits=active_limits)
        self._directory = Path(directory)
        self._fault_injector = fault_injector
        self._lock_fd: int | None = None
        self._usable = True
        self._closed = False
        self._generation = 0
        self._open_status = PersistenceStatus.NO_DURABLE_STATE
        self._last_persistence_status = PersistenceStatus.NO_DURABLE_STATE
        self._prepare_directory()
        self._acquire_lock()
        try:
            snapshot, loaded, status = self._load_authoritative()
            if loaded is not None:
                self._load_into_memory(loaded)
                self._generation = snapshot.generation
            self._open_status = status
            self._last_persistence_status = status
        except BaseException:
            self.close()
            raise

    @property
    def directory(self) -> Path:
        return self._directory

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def open_status(self) -> PersistenceStatus:
        return self._open_status

    @property
    def last_persistence_status(self) -> PersistenceStatus:
        return self._last_persistence_status

    @property
    def usable(self) -> bool:
        return self._usable and not self._closed

    def _prepare_directory(self) -> None:
        try:
            if self._directory.is_symlink():
                raise PersistenceIOError("persistence directory must not be a symlink")
            if self._directory.exists() and not self._directory.is_dir():
                raise PersistenceIOError("persistence path must be a directory")
            self._directory.mkdir(mode=0o700, parents=False, exist_ok=True)
            os.chmod(self._directory, 0o700)
        except PersistenceError:
            raise
        except OSError as exc:
            raise PersistenceIOError("cannot prepare persistence directory") from exc

    def _safe_child(self, name: str) -> Path:
        path = self._directory / name
        if path.is_symlink():
            raise PersistenceIOError("persistence files must not be symlinks")
        return path

    def _acquire_lock(self) -> None:
        lock_path = self._safe_child("catalog.lock")
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(lock_path, flags, 0o600)
            os.fchmod(fd, 0o600)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                os.close(fd)
                raise ConcurrentWriterError("another writer owns this catalog directory") from exc
        except PersistenceError:
            raise
        except OSError as exc:
            raise PersistenceIOError("cannot acquire persistent catalog lock") from exc
        self._lock_fd = fd

    def close(self) -> None:
        fd, self._lock_fd = self._lock_fd, None
        self._closed = True
        if fd is not None:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def __enter__(self) -> PersistentBoundedReferenceCatalog:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def _slot_path(self, slot: int) -> Path:
        return self._safe_child(f"catalog.{slot}.snapshot")

    def _load_authoritative(
        self,
    ) -> tuple[DurableSnapshot, BoundedReferenceCatalog | None, PersistenceStatus]:
        valid: list[tuple[DurableSnapshot, BoundedReferenceCatalog]] = []
        invalid: list[PersistenceError] = []
        existing = 0
        for slot in range(PERSISTENCE_GENERATIONS):
            path = self._slot_path(slot)
            if not path.exists():
                continue
            existing += 1
            try:
                data = path.read_bytes()
                valid.append(_decode_snapshot(data, self.limits))
            except PersistenceError as exc:
                invalid.append(exc)
            except OSError as exc:
                invalid.append(PersistenceIOError("cannot read persistent snapshot"))
                invalid[-1].__cause__ = exc

        if existing == 0:
            empty = DurableSnapshot(0, super().canonical_state(), super().state_digest)
            return empty, None, PersistenceStatus.NO_DURABLE_STATE
        if not valid:
            if len(invalid) == 1:
                raise invalid[0]
            raise PersistenceCorruptError("all durable generations are invalid") from invalid[0]

        by_generation: dict[int, list[tuple[DurableSnapshot, BoundedReferenceCatalog]]] = {}
        for item in valid:
            by_generation.setdefault(item[0].generation, []).append(item)
        highest = max(by_generation)
        contenders = by_generation[highest]
        if len(contenders) > 1:
            payloads = {item[0].payload for item in contenders}
            if len(payloads) > 1:
                raise AmbiguousDurableStateError(
                    "two valid snapshots claim one generation with different payloads"
                )
        chosen = contenders[0]
        status = (
            PersistenceStatus.RECOVERED_PREVIOUS_GENERATION
            if invalid
            else PersistenceStatus.LOADED_CURRENT_GENERATION
        )
        return chosen[0], chosen[1], status

    def _load_into_memory(self, catalog: BoundedReferenceCatalog) -> None:
        offset = 0
        while offset < len(catalog):
            page = catalog.full_reference_list(offset=offset)
            super().add_many(page)
            offset += len(page)

    def _ensure_usable(self) -> None:
        if self._closed:
            raise PersistentCatalogFailStopError("persistent catalog is closed")
        if not self._usable:
            raise PersistentCatalogFailStopError(
                "persistent catalog is fail-stopped; close and reopen it"
            )

    def _inject(self, stage: FaultStage) -> None:
        if self._fault_injector is not None:
            self._fault_injector(stage)

    def _staged_clone(self) -> BoundedReferenceCatalog:
        return BoundedReferenceCatalog.from_canonical_state(
            super().canonical_state(), limits=self.limits
        )

    def _commit(self, candidate: BoundedReferenceCatalog) -> int:
        generation = self._generation + 1
        encoded = _encode_snapshot(generation, candidate.canonical_state(), self.limits)
        slot_path = self._slot_path(generation % PERSISTENCE_GENERATIONS)
        temp_path: Path | None = None
        replaced = False
        try:
            self._inject(FaultStage.BEFORE_TEMP_CREATE)
            fd, raw_path = tempfile.mkstemp(
                prefix=".catalog.snapshot.", suffix=".tmp", dir=self._directory
            )
            temp_path = Path(raw_path)
            try:
                os.fchmod(fd, 0o600)
                midpoint = max(1, len(encoded) // 2)
                first = memoryview(encoded)[:midpoint]
                while first:
                    written = os.write(fd, first)
                    if written <= 0:
                        raise OSError("short persistence write")
                    first = first[written:]
                self._inject(FaultStage.DURING_WRITE)
                view = memoryview(encoded)[midpoint:]
                while view:
                    written = os.write(fd, view)
                    if written <= 0:
                        raise OSError("short persistence write")
                    view = view[written:]
                self._inject(FaultStage.AFTER_WRITE_BEFORE_FILE_FSYNC)
                os.fsync(fd)
            finally:
                os.close(fd)
            self._inject(FaultStage.AFTER_FILE_FSYNC_BEFORE_REPLACE)
            os.replace(temp_path, slot_path)
            temp_path = None
            replaced = True
            self._inject(FaultStage.AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC)
            directory_fd = os.open(self._directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
            self._inject(FaultStage.AFTER_DIRECTORY_FSYNC_BEFORE_MEMORY_SWAP)
            return generation
        except Exception as exc:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
            if replaced:
                self._usable = False
                raise PersistenceUncertainCommitError(
                    "replacement occurred; reopen to establish durable authority",
                    replacement_completed=True,
                ) from exc
            if isinstance(exc, (PersistenceError, CatalogBoundsError)):
                raise
            raise PersistenceIOError("persistent commit failed before replacement") from exc

    def add(self, entry: BoundedReference) -> MutationResult:
        return self.add_many((entry,))[0]

    def add_many(self, entries: Iterable[BoundedReference]) -> tuple[MutationResult, ...]:
        self._ensure_usable()
        pending = tuple(entries)
        candidate = self._staged_clone()
        results = candidate.add_many(pending)
        if not any(result is MutationResult.ADDED for result in results):
            self._last_persistence_status = PersistenceStatus.LOADED_CURRENT_GENERATION
            return results
        generation = self._commit(candidate)
        super().add_many(pending)
        self._generation = generation
        self._last_persistence_status = PersistenceStatus.PERSIST_COMMITTED
        return results

    def remove(self, logical_key: bytes) -> BoundedReference | None:
        self._ensure_usable()
        candidate = self._staged_clone()
        removed = candidate.remove(logical_key)
        if removed is None:
            return None
        generation = self._commit(candidate)
        published = super().remove(logical_key)
        self._generation = generation
        self._last_persistence_status = PersistenceStatus.PERSIST_COMMITTED
        return published

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

    def receiver_known_ids(self, advertised_keys: Sequence[bytes]) -> tuple[bytes, ...]:
        self._ensure_usable()
        return super().receiver_known_ids(advertised_keys)

    def receiver_unknown_ids(self, advertised_keys: Sequence[bytes]) -> tuple[bytes, ...]:
        self._ensure_usable()
        return super().receiver_unknown_ids(advertised_keys)

    def pull_selected(self, selected_keys: Sequence[bytes]) -> tuple[BoundedReference, ...]:
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
    """Use native exact selection and persist its pulled references atomically."""
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
