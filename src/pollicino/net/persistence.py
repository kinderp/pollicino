from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from .session import EXACT_SESSION_SCHEMA, ExactSyncSessionState
from .store import PollicinoStore


SESSION_CHECKPOINT_SCHEMA = "pollicino-exact-session-checkpoint-v1"


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _validate_digest(digest: bytes) -> None:
    if not isinstance(digest, bytes) or len(digest) != 32:
        raise ValueError("chunk digest must be exactly 32 bytes")


def _fsync_directory(path: Path) -> None:
    """Best-effort directory fsync after an atomic rename.

    Some platforms do not support opening directories for fsync. File fsync and
    same-directory ``os.replace`` still provide the core atomicity guarantee;
    directory fsync strengthens crash durability where the platform permits it.
    """

    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        fd = os.open(path, flags)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    if not isinstance(data, bytes):
        raise TypeError("atomic write data must be bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


class DirectoryPollicinoStore(PollicinoStore):
    """Crash-safe content-addressed chunk store rooted in one directory.

    Files are addressed only by SHA-256 and are verified before they are
    advertised as available. A corrupt ordinary file is treated as unavailable
    and may be repaired by a later ``put``. Symlinks are never followed or
    overwritten.
    """

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self._root = Path(root)
        self._chunks_dir = self._root / "chunks"
        self._chunks_dir.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def path_for_digest(self, digest: bytes) -> Path:
        _validate_digest(digest)
        encoded = digest.hex()
        return self._chunks_dir / encoded[:2] / encoded[2:]

    def _read_if_valid(self, digest: bytes) -> bytes | None:
        path = self.path_for_digest(digest)
        if not path.exists():
            return None
        if path.is_symlink() or not path.is_file():
            return None
        content = path.read_bytes()
        if _sha256(content) != digest:
            return None
        return content

    def put(self, content: bytes) -> bytes:
        if not isinstance(content, bytes):
            raise TypeError("content must be bytes")
        digest = _sha256(content)
        path = self.path_for_digest(digest)

        if path.is_symlink():
            raise ValueError("refusing to overwrite a symlink at a chunk address")
        existing = self._read_if_valid(digest)
        if existing is not None:
            if existing != content:
                raise AssertionError("SHA-256 collision detected inside DirectoryPollicinoStore")
            return digest

        _atomic_write_bytes(path, content)
        verified = self._read_if_valid(digest)
        if verified != content:
            raise OSError("atomically written chunk failed post-write verification")
        return digest

    def has(self, digest: bytes) -> bool:
        return self._read_if_valid(digest) is not None

    def get(self, digest: bytes) -> bytes:
        _validate_digest(digest)
        path = self.path_for_digest(digest)
        if not path.exists():
            raise LookupError("chunk is not present in DirectoryPollicinoStore")
        if path.is_symlink() or not path.is_file():
            raise ValueError("chunk address is not a regular file")
        content = path.read_bytes()
        if _sha256(content) != digest:
            raise ValueError("stored chunk failed SHA-256 verification")
        return content

    def __len__(self) -> int:
        count = 0
        if not self._chunks_dir.exists():
            return 0
        for prefix in self._chunks_dir.iterdir():
            if not prefix.is_dir() or prefix.is_symlink() or len(prefix.name) != 2:
                continue
            try:
                int(prefix.name, 16)
            except ValueError:
                continue
            for candidate in prefix.iterdir():
                if candidate.is_symlink() or not candidate.is_file() or len(candidate.name) != 62:
                    continue
                encoded = prefix.name + candidate.name
                try:
                    digest = bytes.fromhex(encoded)
                except ValueError:
                    continue
                if self.has(digest):
                    count += 1
        return count


def _canonical_state_bytes(state_mapping: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(state_mapping),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _validate_checkpoint_state_mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("checkpoint state must be a JSON object")
    if value.get("schema") != EXACT_SESSION_SCHEMA:
        raise ValueError("checkpoint contains an unsupported exact-session schema")

    for name in ("manifest_on_scarce", "manifest_delivered", "completed"):
        if not isinstance(value.get(name), bool):
            raise ValueError(f"checkpoint field {name!r} must be boolean")

    for name in (
        "next_transfer_id",
        "step_count",
        "cumulative_manifest_wire_bytes",
        "cumulative_availability_wire_bytes",
        "cumulative_chunk_wire_bytes",
        "cumulative_retransmissions",
        "cumulative_primary_data_wire_bytes",
        "cumulative_primary_ack_wire_bytes",
        "cumulative_retransmission_data_wire_bytes",
        "cumulative_retransmission_ack_wire_bytes",
        "cumulative_unknown_remote_failure_count",
    ):
        field = value.get(name, 0)
        if isinstance(field, bool) or not isinstance(field, int):
            raise ValueError(f"checkpoint field {name!r} must be an integer")

    fingerprint = value.get("manifest_fingerprint_sha256")
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        raise ValueError("checkpoint manifest fingerprint must be 64 hexadecimal characters")
    try:
        bytes.fromhex(fingerprint)
    except ValueError as exc:
        raise ValueError("checkpoint manifest fingerprint is not hexadecimal") from exc

    wire_accounting = value.get("wire_accounting")
    if wire_accounting is not None and not isinstance(wire_accounting, str):
        raise ValueError("checkpoint wire_accounting must be null or a string")
    return value


def save_exact_session_checkpoint(
    path: str | os.PathLike[str],
    state: ExactSyncSessionState,
) -> Path:
    if not isinstance(state, ExactSyncSessionState):
        raise TypeError("state must be ExactSyncSessionState")
    destination = Path(path)
    state_mapping = state.to_dict()
    canonical = _canonical_state_bytes(state_mapping)
    envelope = {
        "schema": SESSION_CHECKPOINT_SCHEMA,
        "state": state_mapping,
        "state_sha256": hashlib.sha256(canonical).hexdigest(),
    }
    encoded = (
        json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("utf-8")
    _atomic_write_bytes(destination, encoded)
    return destination


def load_exact_session_checkpoint(
    path: str | os.PathLike[str],
) -> ExactSyncSessionState:
    source = Path(path)
    try:
        raw = source.read_bytes()
    except FileNotFoundError as exc:
        raise LookupError("exact-session checkpoint does not exist") from exc
    try:
        envelope = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("exact-session checkpoint is not valid UTF-8 JSON") from exc
    if not isinstance(envelope, Mapping) or envelope.get("schema") != SESSION_CHECKPOINT_SCHEMA:
        raise ValueError("unsupported exact-session checkpoint schema")

    state_mapping = _validate_checkpoint_state_mapping(envelope.get("state"))
    expected = envelope.get("state_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError("exact-session checkpoint checksum is missing or invalid")
    actual = hashlib.sha256(_canonical_state_bytes(state_mapping)).hexdigest()
    if not hmac.compare_digest(actual, expected):
        raise ValueError("exact-session checkpoint checksum mismatch")

    return ExactSyncSessionState.from_dict(state_mapping)
