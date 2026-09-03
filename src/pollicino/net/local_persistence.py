from __future__ import annotations

from enum import Enum
import fcntl
import hashlib
import os
from pathlib import Path
import struct
import tempfile
from typing import Callable, Generic, TypeVar


PERSISTENCE_GENERATIONS = 2
_PREFIX = struct.Struct(">8sBQQ")
_HEADER = struct.Struct(">8sBQQ32s")


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


class PersistentStoreFailStopError(PersistenceError):
    code = "PERSISTENCE_REOPEN_REQUIRED"


class PersistenceUncertainCommitError(PersistentStoreFailStopError):
    code = "PERSISTENCE_UNCERTAIN_COMMIT_REOPEN_REQUIRED"

    def __init__(self, message: str, *, replacement_completed: bool) -> None:
        super().__init__(message)
        self.replacement_completed = replacement_completed


FaultInjector = Callable[[FaultStage], None]
ValueT = TypeVar("ValueT")
PayloadDecoder = Callable[[bytes], ValueT]


def encode_envelope(
    *,
    magic: bytes,
    version: int,
    generation: int,
    payload: bytes,
    max_payload_bytes: int,
) -> bytes:
    if not isinstance(magic, bytes) or len(magic) != 8:
        raise ValueError("persistence magic must contain exactly 8 bytes")
    if type(version) is not int or not 0 <= version <= 255:
        raise ValueError("persistence version must fit one byte")
    if type(generation) is not int or generation < 1:
        raise PersistenceBoundsError("local generation must be a positive integer")
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")
    if len(payload) > max_payload_bytes:
        raise PersistenceBoundsError("payload exceeds persistence bound")
    prefix = _PREFIX.pack(magic, version, generation, len(payload))
    return prefix + hashlib.sha256(prefix + payload).digest() + payload


def decode_envelope(
    data: bytes,
    *,
    magic: bytes,
    version: int,
    max_payload_bytes: int,
) -> tuple[int, bytes]:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if len(data) < _HEADER.size:
        raise PersistenceTruncatedError("persistent snapshot header is truncated")
    actual_magic, actual_version, generation, payload_length, digest = _HEADER.unpack_from(data)
    if actual_magic != magic:
        raise PersistenceCorruptError("invalid persistence magic")
    if actual_version != version:
        raise PersistenceVersionError(f"unsupported persistence version: {actual_version}")
    if payload_length > max_payload_bytes or len(data) > _HEADER.size + max_payload_bytes:
        raise PersistenceBoundsError("declared persistent payload exceeds bound")
    if len(data) != _HEADER.size + payload_length:
        raise PersistenceTruncatedError("persistent snapshot length mismatch")
    payload = data[_HEADER.size :]
    if hashlib.sha256(data[: _PREFIX.size] + payload).digest() != digest:
        raise PersistenceDigestError("persistent snapshot digest mismatch")
    if generation < 1:
        raise PersistenceBoundsError("persistent generation is invalid")
    return generation, payload


def _write_all(fd: int, data: bytes | memoryview) -> None:
    remaining = memoryview(data)
    while remaining:
        written = os.write(fd, remaining)
        if written <= 0:
            raise OSError("short persistence write")
        remaining = remaining[written:]


class DualGenerationSnapshotStore(Generic[ValueT]):
    """POSIX single-writer durable storage for one bounded validated payload."""

    def __init__(
        self,
        directory: Path | str,
        *,
        stem: str,
        magic: bytes,
        version: int,
        max_payload_bytes: int,
        decode_payload: PayloadDecoder[ValueT],
        fault_injector: FaultInjector | None = None,
    ) -> None:
        if not stem or not stem.replace("-", "").isalnum():
            raise ValueError("persistence stem must be a bounded safe identifier")
        if type(max_payload_bytes) is not int or max_payload_bytes < 1:
            raise ValueError("max_payload_bytes must be a positive integer")
        self._directory = Path(directory)
        self._stem = stem
        self._magic = magic
        self._version = version
        self._max_payload_bytes = max_payload_bytes
        self._decode_payload = decode_payload
        self._fault_injector = fault_injector
        self._lock_fd: int | None = None
        self._closed = False
        self._usable = True
        self._generation = 0
        self._payload: bytes | None = None
        self._value: ValueT | None = None
        self._open_status = PersistenceStatus.NO_DURABLE_STATE
        self._last_status = PersistenceStatus.NO_DURABLE_STATE
        self._prepare_directory()
        self._acquire_lock()
        try:
            self._load_authoritative()
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
    def last_status(self) -> PersistenceStatus:
        return self._last_status

    @property
    def usable(self) -> bool:
        return self._usable and not self._closed

    @property
    def payload(self) -> bytes | None:
        self.ensure_usable()
        return self._payload

    @property
    def value(self) -> ValueT | None:
        self.ensure_usable()
        return self._value

    def ensure_usable(self) -> None:
        if self._closed:
            raise PersistentStoreFailStopError("persistent store is closed")
        if not self._usable:
            raise PersistentStoreFailStopError(
                "persistent store is fail-stopped; close and reopen it"
            )

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
        path = self._safe_child(f"{self._stem}.lock")
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(path, flags, 0o600)
            os.fchmod(fd, 0o600)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                os.close(fd)
                raise ConcurrentWriterError("another writer owns this store directory") from exc
        except PersistenceError:
            raise
        except OSError as exc:
            raise PersistenceIOError("cannot acquire persistent store lock") from exc
        self._lock_fd = fd

    def _slot_path(self, slot: int) -> Path:
        return self._safe_child(f"{self._stem}.{slot}.snapshot")

    def _load_authoritative(self) -> None:
        valid: list[tuple[int, bytes, ValueT]] = []
        invalid: list[PersistenceError] = []
        existing = 0
        for slot in range(PERSISTENCE_GENERATIONS):
            path = self._slot_path(slot)
            if not path.exists():
                continue
            existing += 1
            try:
                generation, payload = decode_envelope(
                    path.read_bytes(),
                    magic=self._magic,
                    version=self._version,
                    max_payload_bytes=self._max_payload_bytes,
                )
                valid.append((generation, payload, self._decode_payload(payload)))
            except PersistenceError as exc:
                invalid.append(exc)
            except OSError as exc:
                error = PersistenceIOError("cannot read persistent snapshot")
                error.__cause__ = exc
                invalid.append(error)
        if existing == 0:
            return
        if not valid:
            if len(invalid) == 1:
                raise invalid[0]
            raise PersistenceCorruptError("all durable generations are invalid") from invalid[0]
        highest = max(item[0] for item in valid)
        contenders = [item for item in valid if item[0] == highest]
        if len({item[1] for item in contenders}) > 1:
            raise AmbiguousDurableStateError(
                "two valid snapshots claim one generation with different payloads"
            )
        generation, payload, value = contenders[0]
        self._generation = generation
        self._payload = payload
        self._value = value
        self._open_status = (
            PersistenceStatus.RECOVERED_PREVIOUS_GENERATION
            if invalid
            else PersistenceStatus.LOADED_CURRENT_GENERATION
        )
        self._last_status = self._open_status

    def _inject(self, stage: FaultStage) -> None:
        if self._fault_injector is not None:
            self._fault_injector(stage)

    def commit(self, payload: bytes) -> PersistenceStatus:
        self.ensure_usable()
        value = self._decode_payload(payload)
        generation = self._generation + 1
        encoded = encode_envelope(
            magic=self._magic,
            version=self._version,
            generation=generation,
            payload=payload,
            max_payload_bytes=self._max_payload_bytes,
        )
        target = self._slot_path(generation % PERSISTENCE_GENERATIONS)
        temporary: Path | None = None
        replaced = False
        try:
            self._inject(FaultStage.BEFORE_TEMP_CREATE)
            fd, raw_path = tempfile.mkstemp(
                prefix=f".{self._stem}.", suffix=".tmp", dir=self._directory
            )
            temporary = Path(raw_path)
            try:
                os.fchmod(fd, 0o600)
                midpoint = max(1, len(encoded) // 2)
                _write_all(fd, encoded[:midpoint])
                self._inject(FaultStage.DURING_WRITE)
                _write_all(fd, memoryview(encoded)[midpoint:])
                self._inject(FaultStage.AFTER_WRITE_BEFORE_FILE_FSYNC)
                os.fsync(fd)
            finally:
                os.close(fd)
            self._inject(FaultStage.AFTER_FILE_FSYNC_BEFORE_REPLACE)
            os.replace(temporary, target)
            temporary = None
            replaced = True
            self._inject(FaultStage.AFTER_REPLACE_BEFORE_DIRECTORY_FSYNC)
            directory_fd = os.open(self._directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
            self._inject(FaultStage.AFTER_DIRECTORY_FSYNC_BEFORE_MEMORY_SWAP)
            self._generation = generation
            self._payload = payload
            self._value = value
            self._last_status = PersistenceStatus.PERSIST_COMMITTED
            return self._last_status
        except Exception as exc:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
            if replaced:
                self._usable = False
                raise PersistenceUncertainCommitError(
                    "replacement occurred; reopen to establish durable authority",
                    replacement_completed=True,
                ) from exc
            if isinstance(exc, PersistenceError):
                raise
            raise PersistenceIOError("persistent commit failed before replacement") from exc

    def close(self) -> None:
        fd, self._lock_fd = self._lock_fd, None
        self._closed = True
        if fd is not None:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def __enter__(self) -> DualGenerationSnapshotStore[ValueT]:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
