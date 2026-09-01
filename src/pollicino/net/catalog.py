from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import struct
from typing import Iterable, Sequence


MAX_LOGICAL_KEY_BYTES = 256
MAX_REFERENCE_BYTES = 4096
MAX_CATALOG_ITEMS = 10_000
MAX_CATALOG_BYTES = 16 * 1024 * 1024
MAX_EXCHANGE_ITEMS = 100

LOCAL_STATE_MAGIC = b"PRCS"
LOCAL_STATE_VERSION = 1
_STATE_HEADER = struct.Struct(">4sBIQ32s")
_ENTRY_HEADER = struct.Struct(">HI")


class CatalogBoundsError(ValueError):
    """A local resource or exchange bound would be exceeded."""


class ReferenceConflictError(ValueError):
    """A logical key is already bound to different opaque bytes."""

    def __init__(self, logical_key: bytes) -> None:
        super().__init__("logical key is already bound to a different reference")
        self.logical_key = logical_key


class MutationResult(str, Enum):
    ADDED = "ADDED"
    NOOP_DUPLICATE = "NOOP_DUPLICATE"


@dataclass(frozen=True, slots=True)
class CatalogLimits:
    max_key_bytes: int = MAX_LOGICAL_KEY_BYTES
    max_reference_bytes: int = MAX_REFERENCE_BYTES
    max_catalog_items: int = MAX_CATALOG_ITEMS
    max_catalog_bytes: int = MAX_CATALOG_BYTES
    max_exchange_items: int = MAX_EXCHANGE_ITEMS

    def __post_init__(self) -> None:
        pairs = (
            ("max_key_bytes", self.max_key_bytes, MAX_LOGICAL_KEY_BYTES),
            ("max_reference_bytes", self.max_reference_bytes, MAX_REFERENCE_BYTES),
            ("max_catalog_items", self.max_catalog_items, MAX_CATALOG_ITEMS),
            ("max_catalog_bytes", self.max_catalog_bytes, MAX_CATALOG_BYTES),
            ("max_exchange_items", self.max_exchange_items, MAX_EXCHANGE_ITEMS),
        )
        for name, value, ceiling in pairs:
            if type(value) is not int or not 1 <= value <= ceiling:
                raise CatalogBoundsError(f"{name} must be between 1 and {ceiling}")


def _require_bytes(name: str, value: bytes, *, maximum: int) -> None:
    if not isinstance(value, bytes):
        raise TypeError(f"{name} must be bytes")
    if not value:
        raise CatalogBoundsError(f"{name} must not be empty")
    if len(value) > maximum:
        raise CatalogBoundsError(f"{name} exceeds {maximum} bytes")


@dataclass(frozen=True, slots=True)
class BoundedReference:
    logical_key: bytes
    opaque_reference: bytes

    def __post_init__(self) -> None:
        _require_bytes(
            "logical_key",
            self.logical_key,
            maximum=MAX_LOGICAL_KEY_BYTES,
        )
        _require_bytes(
            "opaque_reference",
            self.opaque_reference,
            maximum=MAX_REFERENCE_BYTES,
        )

    @property
    def payload_bytes(self) -> int:
        return len(self.logical_key) + len(self.opaque_reference)


@dataclass(frozen=True, slots=True)
class ReconcileResult:
    advertised_keys: tuple[bytes, ...]
    receiver_known_keys: tuple[bytes, ...]
    candidate_keys: tuple[bytes, ...]
    selected_keys: tuple[bytes, ...]
    pulled_references: tuple[BoundedReference, ...]
    mutation_results: tuple[MutationResult, ...]


class BoundedReferenceCatalog:
    """Bounded in-memory mapping from caller-owned keys to opaque bytes."""

    def __init__(self, *, limits: CatalogLimits | None = None) -> None:
        self._limits = limits if limits is not None else CatalogLimits()
        if not isinstance(self._limits, CatalogLimits):
            raise TypeError("limits must be CatalogLimits")
        self._entries: dict[bytes, bytes] = {}
        self._payload_bytes = 0

    @property
    def limits(self) -> CatalogLimits:
        return self._limits

    @property
    def payload_bytes(self) -> int:
        return self._payload_bytes

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, logical_key: object) -> bool:
        return logical_key in self._entries

    def _validate_entry(self, entry: BoundedReference) -> None:
        if not isinstance(entry, BoundedReference):
            raise TypeError("entry must be BoundedReference")
        _require_bytes(
            "logical_key",
            entry.logical_key,
            maximum=self._limits.max_key_bytes,
        )
        _require_bytes(
            "opaque_reference",
            entry.opaque_reference,
            maximum=self._limits.max_reference_bytes,
        )

    def add(self, entry: BoundedReference) -> MutationResult:
        return self.add_many((entry,))[0]

    def add_many(
        self,
        entries: Iterable[BoundedReference],
    ) -> tuple[MutationResult, ...]:
        pending = tuple(entries)
        staged = dict(self._entries)
        staged_payload = self._payload_bytes
        results: list[MutationResult] = []

        for entry in pending:
            self._validate_entry(entry)
            previous = staged.get(entry.logical_key)
            if previous is not None:
                if previous != entry.opaque_reference:
                    raise ReferenceConflictError(entry.logical_key)
                results.append(MutationResult.NOOP_DUPLICATE)
                continue

            staged[entry.logical_key] = entry.opaque_reference
            staged_payload += entry.payload_bytes
            results.append(MutationResult.ADDED)

        if len(staged) > self._limits.max_catalog_items:
            raise CatalogBoundsError("catalog item quota exceeded")
        if staged_payload > self._limits.max_catalog_bytes:
            raise CatalogBoundsError("catalog byte quota exceeded")

        self._entries = staged
        self._payload_bytes = staged_payload
        return tuple(results)

    def get(self, logical_key: bytes) -> BoundedReference:
        _require_bytes(
            "logical_key",
            logical_key,
            maximum=self._limits.max_key_bytes,
        )
        try:
            opaque_reference = self._entries[logical_key]
        except KeyError as exc:
            raise LookupError("logical key is not present") from exc
        return BoundedReference(logical_key, opaque_reference)

    def remove(self, logical_key: bytes) -> BoundedReference | None:
        _require_bytes(
            "logical_key",
            logical_key,
            maximum=self._limits.max_key_bytes,
        )
        opaque_reference = self._entries.pop(logical_key, None)
        if opaque_reference is None:
            return None
        entry = BoundedReference(logical_key, opaque_reference)
        self._payload_bytes -= entry.payload_bytes
        return entry

    def _page_bounds(self, offset: int, limit: int | None) -> tuple[int, int]:
        if type(offset) is not int or offset < 0:
            raise ValueError("offset must be a non-negative integer")
        page_limit = self._limits.max_exchange_items if limit is None else limit
        if type(page_limit) is not int or not 1 <= page_limit <= self._limits.max_exchange_items:
            raise CatalogBoundsError(
                f"exchange page must contain at most {self._limits.max_exchange_items} items"
            )
        return offset, offset + page_limit

    def sorted_logical_ids(
        self,
        *,
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[bytes, ...]:
        start, end = self._page_bounds(offset, limit)
        return tuple(sorted(self._entries)[start:end])

    def full_reference_list(
        self,
        *,
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[BoundedReference, ...]:
        keys = self.sorted_logical_ids(offset=offset, limit=limit)
        return tuple(BoundedReference(key, self._entries[key]) for key in keys)

    def _exchange_keys(
        self,
        name: str,
        logical_keys: Sequence[bytes],
    ) -> tuple[bytes, ...]:
        if not isinstance(logical_keys, (tuple, list)):
            raise TypeError(f"{name} must be a tuple or list")
        keys = tuple(logical_keys)
        if len(keys) > self._limits.max_exchange_items:
            raise CatalogBoundsError(
                f"{name} exceeds {self._limits.max_exchange_items} items"
            )
        for key in keys:
            _require_bytes(name, key, maximum=self._limits.max_key_bytes)
        if len(set(keys)) != len(keys):
            raise ValueError(f"{name} contains duplicate keys")
        return tuple(sorted(keys))

    def receiver_known_ids(
        self,
        advertised_keys: Sequence[bytes],
    ) -> tuple[bytes, ...]:
        advertised = self._exchange_keys("advertised_keys", advertised_keys)
        return tuple(key for key in advertised if key in self._entries)

    def receiver_unknown_ids(
        self,
        advertised_keys: Sequence[bytes],
    ) -> tuple[bytes, ...]:
        advertised = self._exchange_keys("advertised_keys", advertised_keys)
        return tuple(key for key in advertised if key not in self._entries)

    def pull_selected(
        self,
        selected_keys: Sequence[bytes],
    ) -> tuple[BoundedReference, ...]:
        selected = self._exchange_keys("selected_keys", selected_keys)
        missing = tuple(key for key in selected if key not in self._entries)
        if missing:
            raise LookupError("one or more selected keys are not present")
        return tuple(BoundedReference(key, self._entries[key]) for key in selected)

    def canonical_state(self) -> bytes:
        body = bytearray()
        for key in sorted(self._entries):
            opaque_reference = self._entries[key]
            body += _ENTRY_HEADER.pack(len(key), len(opaque_reference))
            body += key
            body += opaque_reference
        body_bytes = bytes(body)
        return _STATE_HEADER.pack(
            LOCAL_STATE_MAGIC,
            LOCAL_STATE_VERSION,
            len(self._entries),
            self._payload_bytes,
            hashlib.sha256(body_bytes).digest(),
        ) + body_bytes

    @property
    def state_digest(self) -> bytes:
        return hashlib.sha256(self.canonical_state()).digest()

    @classmethod
    def from_canonical_state(
        cls,
        data: bytes,
        *,
        limits: CatalogLimits | None = None,
    ) -> BoundedReferenceCatalog:
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        active_limits = limits if limits is not None else CatalogLimits()
        if not isinstance(active_limits, CatalogLimits):
            raise TypeError("limits must be CatalogLimits")
        if len(data) < _STATE_HEADER.size:
            raise ValueError("local state is shorter than its header")

        magic, version, item_count, payload_bytes, body_digest = _STATE_HEADER.unpack_from(data)
        if magic != LOCAL_STATE_MAGIC:
            raise ValueError("invalid local state magic")
        if version != LOCAL_STATE_VERSION:
            raise ValueError(f"unsupported local state version: {version}")
        if item_count > active_limits.max_catalog_items:
            raise CatalogBoundsError("declared catalog item quota exceeded")
        if payload_bytes > active_limits.max_catalog_bytes:
            raise CatalogBoundsError("declared catalog byte quota exceeded")
        maximum_encoded = (
            _STATE_HEADER.size
            + active_limits.max_catalog_bytes
            + active_limits.max_catalog_items * _ENTRY_HEADER.size
        )
        if len(data) > maximum_encoded:
            raise CatalogBoundsError("encoded local state exceeds its maximum size")

        body = data[_STATE_HEADER.size :]
        if hashlib.sha256(body).digest() != body_digest:
            raise ValueError("local state body digest mismatch")

        entries: list[BoundedReference] = []
        seen: set[bytes] = set()
        offset = 0
        actual_payload = 0
        for _ in range(item_count):
            if offset + _ENTRY_HEADER.size > len(body):
                raise ValueError("local state entry header is truncated")
            key_len, reference_len = _ENTRY_HEADER.unpack_from(body, offset)
            offset += _ENTRY_HEADER.size
            end = offset + key_len + reference_len
            if end > len(body):
                raise ValueError("local state entry is truncated")
            key = body[offset : offset + key_len]
            opaque_reference = body[offset + key_len : end]
            offset = end
            if key in seen:
                raise ValueError("local state contains duplicate keys")
            seen.add(key)
            entry = BoundedReference(key, opaque_reference)
            if len(key) > active_limits.max_key_bytes:
                raise CatalogBoundsError("logical_key exceeds active limit")
            if len(opaque_reference) > active_limits.max_reference_bytes:
                raise CatalogBoundsError("opaque_reference exceeds active limit")
            entries.append(entry)
            actual_payload += entry.payload_bytes

        if offset != len(body):
            raise ValueError("local state contains trailing data")
        if actual_payload != payload_bytes:
            raise ValueError("local state payload byte count mismatch")

        catalog = cls(limits=active_limits)
        catalog.add_many(entries)
        return catalog


def reconcile_and_pull(
    sender: BoundedReferenceCatalog,
    receiver: BoundedReferenceCatalog,
    *,
    advertised_keys: Sequence[bytes],
    selected_keys: Sequence[bytes] | None = None,
) -> ReconcileResult:
    """Apply one exact, bounded, topology-free reconciliation page."""

    if not isinstance(sender, BoundedReferenceCatalog):
        raise TypeError("sender must be BoundedReferenceCatalog")
    if not isinstance(receiver, BoundedReferenceCatalog):
        raise TypeError("receiver must be BoundedReferenceCatalog")

    advertised = sender._exchange_keys("advertised_keys", advertised_keys)
    missing_sender = tuple(key for key in advertised if key not in sender)
    if missing_sender:
        raise LookupError("an advertised key is not present at the sender")

    known = receiver.receiver_known_ids(advertised)
    candidates = receiver.receiver_unknown_ids(advertised)
    if selected_keys is None:
        selected = candidates
    else:
        selected = sender._exchange_keys("selected_keys", selected_keys)
        if not set(selected).issubset(candidates):
            raise ValueError("selected_keys must be a subset of new candidate keys")

    pulled = sender.pull_selected(selected)
    mutation_results = receiver.add_many(pulled)
    return ReconcileResult(
        advertised_keys=advertised,
        receiver_known_keys=known,
        candidate_keys=candidates,
        selected_keys=selected,
        pulled_references=pulled,
        mutation_results=mutation_results,
    )
