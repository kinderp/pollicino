from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json
from typing import Callable, Mapping


REFERENCE_SCHEMA = "pollicino-portable-reference-v1"
MAX_PROVIDER_ID_BYTES = 64
MAX_LOCATOR_BYTES = 0xFFFF
MAX_LABEL_BYTES = 1024
MAX_METADATA_ENTRIES = 64
MAX_METADATA_KEY_BYTES = 128
MAX_METADATA_VALUE_BYTES = 2048


def _require_utf8(name: str, value: str, *, maximum: int) -> bytes:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    encoded = value.encode("utf-8")
    if len(encoded) > maximum:
        raise ValueError(f"{name} exceeds {maximum} UTF-8 bytes")
    return encoded


@dataclass(frozen=True, slots=True)
class PortableReference:
    """Small application object carried by Pollicino as ordinary EXACT bytes.

    PollicinoNet does not interpret the locator. ``provider_id`` selects a
    resolver only after the object reaches an environment that has one. This
    keeps magnet URIs, HTTP URLs, content IDs, filesystem coordinates and
    future provider-specific references out of the network core.

    The reference itself is exact and content-addressable. Resolving the
    reference may trigger external work, so handlers live outside this object
    and are invoked explicitly by the home/application layer.
    """

    provider_id: str
    locator: bytes
    label: str = ""
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, str) or not self.provider_id:
            raise ValueError("provider_id must be a non-empty string")
        try:
            provider = self.provider_id.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError("provider_id must be ASCII") from exc
        if len(provider) > MAX_PROVIDER_ID_BYTES:
            raise ValueError("provider_id is too long")
        if not isinstance(self.locator, bytes) or not self.locator:
            raise ValueError("locator must be non-empty bytes")
        if len(self.locator) > MAX_LOCATOR_BYTES:
            raise ValueError("locator is too long")
        _require_utf8("label", self.label, maximum=MAX_LABEL_BYTES)
        if not isinstance(self.metadata, tuple):
            raise TypeError("metadata must be a tuple of string pairs")
        if len(self.metadata) > MAX_METADATA_ENTRIES:
            raise ValueError("metadata contains too many entries")

        normalized: list[tuple[str, str]] = []
        seen: set[str] = set()
        for item in self.metadata:
            if (
                not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], str)
                or not isinstance(item[1], str)
            ):
                raise TypeError("metadata must contain (str, str) pairs")
            key, value = item
            if not key:
                raise ValueError("metadata keys must not be empty")
            if key in seen:
                raise ValueError("metadata keys must be unique")
            _require_utf8("metadata key", key, maximum=MAX_METADATA_KEY_BYTES)
            _require_utf8("metadata value", value, maximum=MAX_METADATA_VALUE_BYTES)
            seen.add(key)
            normalized.append((key, value))
        object.__setattr__(self, "metadata", tuple(sorted(normalized)))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": REFERENCE_SCHEMA,
            "provider": self.provider_id,
            "locator_b64": base64.b64encode(self.locator).decode("ascii"),
            "label": self.label,
            "metadata": {key: value for key, value in self.metadata},
        }

    def encode(self) -> bytes:
        return json.dumps(
            self.to_mapping(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

    @property
    def sha256_digest(self) -> bytes:
        return hashlib.sha256(self.encode()).digest()

    @classmethod
    def decode(cls, payload: bytes) -> PortableReference:
        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes")
        try:
            value = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("portable reference is not valid UTF-8 JSON") from exc
        if not isinstance(value, Mapping) or value.get("schema") != REFERENCE_SCHEMA:
            raise ValueError("unsupported portable reference schema")
        provider = value.get("provider")
        label = value.get("label", "")
        locator_b64 = value.get("locator_b64")
        metadata = value.get("metadata", {})
        if not isinstance(provider, str) or not isinstance(label, str):
            raise ValueError("portable reference provider/label is invalid")
        if not isinstance(locator_b64, str):
            raise ValueError("portable reference locator is missing")
        try:
            locator = base64.b64decode(locator_b64, validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise ValueError("portable reference locator is not valid base64") from exc
        if not isinstance(metadata, Mapping):
            raise ValueError("portable reference metadata must be an object")
        pairs: list[tuple[str, str]] = []
        for key, item in metadata.items():
            if not isinstance(key, str) or not isinstance(item, str):
                raise ValueError("portable reference metadata must contain strings")
            pairs.append((key, item))
        return cls(
            provider_id=provider,
            locator=locator,
            label=label,
            metadata=tuple(pairs),
        )


@dataclass(frozen=True, slots=True)
class ReferenceResolutionReceipt:
    provider_id: str
    locator_sha256: str
    accepted: bool
    detail: str


ReferenceHandler = Callable[[PortableReference], str]


class HomeReferenceResolver:
    """Explicit application-layer dispatcher used when rich connectivity exists.

    It deliberately performs no networking itself. Applications register
    provider-specific handlers (for example a local NAS lookup, an HTTP fetch
    queue, or an authorized BitTorrent client adapter) and choose when to invoke
    them. Tests can therefore exercise the complete reference-mule lifecycle
    without hidden Internet access or side effects.
    """

    def __init__(self, handlers: Mapping[str, ReferenceHandler] | None = None) -> None:
        self._handlers: dict[str, ReferenceHandler] = {}
        if handlers is not None:
            for provider_id, handler in handlers.items():
                self.register(provider_id, handler)

    def register(self, provider_id: str, handler: ReferenceHandler) -> None:
        if not isinstance(provider_id, str) or not provider_id:
            raise ValueError("provider_id must be a non-empty string")
        if not callable(handler):
            raise TypeError("reference handler must be callable")
        self._handlers[provider_id] = handler

    def resolve(self, reference: PortableReference) -> ReferenceResolutionReceipt:
        if not isinstance(reference, PortableReference):
            raise TypeError("reference must be PortableReference")
        handler = self._handlers.get(reference.provider_id)
        locator_sha = hashlib.sha256(reference.locator).hexdigest()
        if handler is None:
            return ReferenceResolutionReceipt(
                provider_id=reference.provider_id,
                locator_sha256=locator_sha,
                accepted=False,
                detail="no handler registered",
            )
        detail = handler(reference)
        if not isinstance(detail, str):
            raise TypeError("reference handler must return a string detail")
        return ReferenceResolutionReceipt(
            provider_id=reference.provider_id,
            locator_sha256=locator_sha,
            accepted=True,
            detail=detail,
        )
