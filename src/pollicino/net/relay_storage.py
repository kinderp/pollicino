from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any, Mapping

from .bundle import CustodyLedger, ForwardBundle
from .persistence import DirectoryPollicinoStore, _atomic_write_bytes
from .store import ChunkManifest


RELAY_CATALOG_SCHEMA = "pollicino-relay-storage-catalog-v1"
RELAY_CATALOG_CHECKPOINT_SCHEMA = "pollicino-relay-storage-catalog-checkpoint-v1"


def _require_non_negative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _require_digest(name: str, value: bytes) -> None:
    if not isinstance(value, bytes) or len(value) != 32:
        raise ValueError(f"{name} must be exactly 32 bytes")


def _require_peer_id(value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError("peer_id must be a non-empty string")


@dataclass(frozen=True, slots=True)
class RelayStoragePolicy:
    """Local storage limits for one durable relay.

    ``retention_seconds`` is a local upper bound. Bundle TTL remains the hard
    protocol lifetime, so local retention can shorten but never extend it.
    """

    max_store_bytes: int
    retention_seconds: int

    def __post_init__(self) -> None:
        _require_non_negative_int("max_store_bytes", self.max_store_bytes)
        _require_non_negative_int("retention_seconds", self.retention_seconds)


@dataclass(frozen=True, slots=True)
class RelayBundleRecord:
    bundle_id: bytes
    manifest_fingerprint: bytes
    chunk_digests: tuple[bytes, ...]
    first_seen_s: int
    last_seen_s: int
    retain_until_s: int
    pinned: bool = False

    def __post_init__(self) -> None:
        _require_digest("bundle_id", self.bundle_id)
        _require_digest("manifest_fingerprint", self.manifest_fingerprint)
        if not isinstance(self.chunk_digests, tuple):
            raise TypeError("chunk_digests must be a tuple")
        for digest in self.chunk_digests:
            _require_digest("chunk_digest", digest)
        _require_non_negative_int("first_seen_s", self.first_seen_s)
        _require_non_negative_int("last_seen_s", self.last_seen_s)
        _require_non_negative_int("retain_until_s", self.retain_until_s)
        if self.last_seen_s < self.first_seen_s:
            raise ValueError("last_seen_s cannot precede first_seen_s")
        if not isinstance(self.pinned, bool):
            raise TypeError("pinned must be bool")

    @property
    def referenced_digests(self) -> tuple[bytes, ...]:
        return tuple(dict.fromkeys((self.manifest_fingerprint, *self.chunk_digests)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id.hex(),
            "manifest_fingerprint": self.manifest_fingerprint.hex(),
            "chunk_digests": [digest.hex() for digest in self.chunk_digests],
            "first_seen_s": self.first_seen_s,
            "last_seen_s": self.last_seen_s,
            "retain_until_s": self.retain_until_s,
            "pinned": self.pinned,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> RelayBundleRecord:
        try:
            bundle_id = bytes.fromhex(str(value["bundle_id"]))
            manifest_fingerprint = bytes.fromhex(str(value["manifest_fingerprint"]))
        except (KeyError, ValueError) as exc:
            raise ValueError("invalid relay bundle digest") from exc
        chunks = value.get("chunk_digests")
        if not isinstance(chunks, list):
            raise ValueError("chunk_digests must be a list")
        try:
            chunk_digests = tuple(bytes.fromhex(str(item)) for item in chunks)
        except ValueError as exc:
            raise ValueError("invalid relay chunk digest") from exc
        pinned = value.get("pinned", False)
        if not isinstance(pinned, bool):
            raise ValueError("pinned must be boolean")
        return cls(
            bundle_id=bundle_id,
            manifest_fingerprint=manifest_fingerprint,
            chunk_digests=chunk_digests,
            first_seen_s=int(value["first_seen_s"]),
            last_seen_s=int(value["last_seen_s"]),
            retain_until_s=int(value["retain_until_s"]),
            pinned=pinned,
        )


class RelayStorageCatalog:
    """Persistent local view of which bundles justify keeping store objects."""

    def __init__(self, peer_id: str) -> None:
        _require_peer_id(peer_id)
        self.peer_id = peer_id
        self._records: dict[bytes, RelayBundleRecord] = {}

    def get(self, bundle_id: bytes) -> RelayBundleRecord | None:
        _require_digest("bundle_id", bundle_id)
        return self._records.get(bundle_id)

    @property
    def records(self) -> tuple[RelayBundleRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    def register(
        self,
        bundle: ForwardBundle,
        manifest: ChunkManifest,
        *,
        now_s: int,
        policy: RelayStoragePolicy,
        pinned: bool = False,
    ) -> RelayBundleRecord:
        _require_non_negative_int("now_s", now_s)
        if not isinstance(policy, RelayStoragePolicy):
            raise TypeError("policy must be RelayStoragePolicy")
        if not isinstance(pinned, bool):
            raise TypeError("pinned must be bool")
        if bundle.manifest_fingerprint != manifest.fingerprint:
            raise ValueError("bundle manifest fingerprint mismatch")

        protocol_expiry = bundle.created_at_s + bundle.ttl_seconds
        local_expiry = now_s + policy.retention_seconds
        retain_until = min(protocol_expiry, local_expiry)
        previous = self._records.get(bundle.bundle_id)
        first_seen = now_s if previous is None else min(previous.first_seen_s, now_s)
        record = RelayBundleRecord(
            bundle_id=bundle.bundle_id,
            manifest_fingerprint=manifest.fingerprint,
            chunk_digests=tuple(ref.sha256_digest for ref in manifest.chunks),
            first_seen_s=first_seen,
            last_seen_s=max(now_s, previous.last_seen_s if previous is not None else now_s),
            retain_until_s=retain_until,
            pinned=pinned or (previous.pinned if previous is not None else False),
        )
        if previous is not None and previous.manifest_fingerprint != record.manifest_fingerprint:
            raise ValueError("bundle_id is already bound to a different manifest")
        self._records[record.bundle_id] = record
        return record

    def pin(self, bundle_id: bytes, *, pinned: bool = True) -> RelayBundleRecord:
        if not isinstance(pinned, bool):
            raise TypeError("pinned must be bool")
        record = self.get(bundle_id)
        if record is None:
            raise KeyError("bundle is not present in relay catalog")
        updated = RelayBundleRecord(
            bundle_id=record.bundle_id,
            manifest_fingerprint=record.manifest_fingerprint,
            chunk_digests=record.chunk_digests,
            first_seen_s=record.first_seen_s,
            last_seen_s=record.last_seen_s,
            retain_until_s=record.retain_until_s,
            pinned=pinned,
        )
        self._records[bundle_id] = updated
        return updated

    def remove(self, bundle_id: bytes) -> RelayBundleRecord | None:
        _require_digest("bundle_id", bundle_id)
        return self._records.pop(bundle_id, None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": RELAY_CATALOG_SCHEMA,
            "peer_id": self.peer_id,
            "records": [record.to_dict() for record in self.records],
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> RelayStorageCatalog:
        if value.get("schema") != RELAY_CATALOG_SCHEMA:
            raise ValueError("unsupported relay storage catalog schema")
        peer_id = value.get("peer_id")
        _require_peer_id(peer_id)
        records = value.get("records")
        if not isinstance(records, list):
            raise ValueError("relay catalog records must be a list")
        catalog = cls(peer_id)
        for item in records:
            if not isinstance(item, Mapping):
                raise ValueError("relay catalog record must be an object")
            record = RelayBundleRecord.from_dict(item)
            if record.bundle_id in catalog._records:
                raise ValueError("relay catalog contains duplicate bundle IDs")
            catalog._records[record.bundle_id] = record
        return catalog


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def save_relay_storage_catalog(
    path: str | os.PathLike[str], catalog: RelayStorageCatalog
) -> Path:
    if not isinstance(catalog, RelayStorageCatalog):
        raise TypeError("catalog must be RelayStorageCatalog")
    body = catalog.to_dict()
    envelope = {
        "schema": RELAY_CATALOG_CHECKPOINT_SCHEMA,
        "catalog": body,
        "catalog_sha256": hashlib.sha256(_canonical_bytes(body)).hexdigest(),
    }
    encoded = (
        json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("utf-8")
    destination = Path(path)
    _atomic_write_bytes(destination, encoded)
    return destination


def load_relay_storage_catalog(path: str | os.PathLike[str]) -> RelayStorageCatalog:
    source = Path(path)
    try:
        envelope = json.loads(source.read_bytes())
    except FileNotFoundError as exc:
        raise LookupError("relay storage catalog does not exist") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("relay storage catalog is not valid UTF-8 JSON") from exc
    if not isinstance(envelope, Mapping) or envelope.get("schema") != RELAY_CATALOG_CHECKPOINT_SCHEMA:
        raise ValueError("unsupported relay storage catalog checkpoint")
    body = envelope.get("catalog")
    if not isinstance(body, Mapping):
        raise ValueError("relay storage catalog body must be an object")
    expected = envelope.get("catalog_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError("relay storage catalog checksum is missing or invalid")
    actual = hashlib.sha256(_canonical_bytes(body)).hexdigest()
    if not hmac.compare_digest(actual, expected):
        raise ValueError("relay storage catalog checksum mismatch")
    return RelayStorageCatalog.from_dict(body)


@dataclass(frozen=True, slots=True)
class RelayGCReport:
    now_s: int
    store_bytes_before: int
    store_bytes_after: int
    expired_bundle_ids: tuple[str, ...]
    quota_evicted_bundle_ids: tuple[str, ...]
    removed_object_digests: tuple[str, ...]
    removed_invalid_object_digests: tuple[str, ...]
    active_bundle_count: int
    over_quota_bytes: int

    @property
    def removed_bundle_count(self) -> int:
        return len(self.expired_bundle_ids) + len(self.quota_evicted_bundle_ids)

    @property
    def freed_bytes(self) -> int:
        return self.store_bytes_before - self.store_bytes_after


@dataclass(frozen=True, slots=True)
class _StoreObject:
    digest: bytes
    path: Path
    size_bytes: int
    valid: bool


def _scan_store(store: DirectoryPollicinoStore) -> list[_StoreObject]:
    chunks_dir = store.root / "chunks"
    if not chunks_dir.exists():
        return []
    objects: list[_StoreObject] = []
    for prefix in chunks_dir.iterdir():
        if prefix.is_symlink() or not prefix.is_dir() or len(prefix.name) != 2:
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
            objects.append(
                _StoreObject(
                    digest=digest,
                    path=candidate,
                    size_bytes=candidate.stat().st_size,
                    valid=store.has(digest),
                )
            )
    return objects


def _active_references(catalog: RelayStorageCatalog) -> set[bytes]:
    result: set[bytes] = set()
    for record in catalog.records:
        result.update(record.referenced_digests)
    return result


def _delete_unreferenced(
    store: DirectoryPollicinoStore,
    catalog: RelayStorageCatalog,
    *,
    removed: set[str],
    removed_invalid: set[str],
) -> None:
    references = _active_references(catalog)
    for item in _scan_store(store):
        if item.valid and item.digest in references:
            continue
        try:
            item.path.unlink()
        except FileNotFoundError:
            continue
        encoded = item.digest.hex()
        removed.add(encoded)
        if not item.valid:
            removed_invalid.add(encoded)
        try:
            item.path.parent.rmdir()
        except OSError:
            pass


def _store_bytes(store: DirectoryPollicinoStore) -> int:
    return sum(item.size_bytes for item in _scan_store(store))


def _prune_custody_ledger(
    ledger: CustodyLedger,
    *,
    peer_id: str,
    removed_bundle_ids: set[bytes],
) -> CustodyLedger:
    body = ledger.to_dict()
    removed_hex = {bundle_id.hex() for bundle_id in removed_bundle_ids}
    body["records"] = [
        item
        for item in body["records"]
        if not (item.get("peer_id") == peer_id and item.get("bundle_id") in removed_hex)
    ]
    return CustodyLedger.from_dict(body)


def collect_relay_storage(
    store: DirectoryPollicinoStore,
    catalog: RelayStorageCatalog,
    policy: RelayStoragePolicy,
    *,
    now_s: int,
    ledger: CustodyLedger | None = None,
) -> tuple[RelayGCReport, CustodyLedger | None]:
    """Expire/evict relay bundles and delete only objects no active bundle needs.

    Shared chunks survive as long as at least one active bundle references them.
    Pinned bundles are protected from quota eviction, but never from protocol or
    local retention expiry. If pinned data alone exceed the quota, the report
    exposes ``over_quota_bytes`` instead of silently deleting protected data.

    When a custody ledger is supplied, the returned ledger has local custody
    records removed for bundles that were actually dropped. Processed contact
    IDs are preserved so replayed historical encounters remain idempotent.
    """

    if not isinstance(store, DirectoryPollicinoStore):
        raise TypeError("store must be DirectoryPollicinoStore")
    if not isinstance(catalog, RelayStorageCatalog):
        raise TypeError("catalog must be RelayStorageCatalog")
    if not isinstance(policy, RelayStoragePolicy):
        raise TypeError("policy must be RelayStoragePolicy")
    _require_non_negative_int("now_s", now_s)
    if ledger is not None and not isinstance(ledger, CustodyLedger):
        raise TypeError("ledger must be CustodyLedger or None")

    bytes_before = _store_bytes(store)
    expired: list[bytes] = []
    quota_evicted: list[bytes] = []
    removed_objects: set[str] = set()
    removed_invalid: set[str] = set()

    for record in list(catalog.records):
        if now_s >= record.retain_until_s:
            catalog.remove(record.bundle_id)
            expired.append(record.bundle_id)

    _delete_unreferenced(
        store, catalog, removed=removed_objects, removed_invalid=removed_invalid
    )

    while _store_bytes(store) > policy.max_store_bytes:
        candidates = sorted(
            (record for record in catalog.records if not record.pinned),
            key=lambda record: (record.last_seen_s, record.first_seen_s, record.bundle_id),
        )
        if not candidates:
            break
        victim = candidates[0]
        catalog.remove(victim.bundle_id)
        quota_evicted.append(victim.bundle_id)
        _delete_unreferenced(
            store, catalog, removed=removed_objects, removed_invalid=removed_invalid
        )

    bytes_after = _store_bytes(store)
    removed_bundle_ids = set(expired) | set(quota_evicted)
    updated_ledger = (
        None
        if ledger is None
        else _prune_custody_ledger(
            ledger, peer_id=catalog.peer_id, removed_bundle_ids=removed_bundle_ids
        )
    )
    report = RelayGCReport(
        now_s=now_s,
        store_bytes_before=bytes_before,
        store_bytes_after=bytes_after,
        expired_bundle_ids=tuple(bundle_id.hex() for bundle_id in expired),
        quota_evicted_bundle_ids=tuple(bundle_id.hex() for bundle_id in quota_evicted),
        removed_object_digests=tuple(sorted(removed_objects)),
        removed_invalid_object_digests=tuple(sorted(removed_invalid)),
        active_bundle_count=len(catalog.records),
        over_quota_bytes=max(0, bytes_after - policy.max_store_bytes),
    )
    return report, updated_ledger
