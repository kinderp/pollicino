from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
from typing import Mapping, Protocol

from .wire import DiscoveryDescriptor


MANIFEST_MAGIC = b"PNM1"
MANIFEST_VERSION = 1
_MANIFEST_HEADER = struct.Struct(">4sBBQ32sBH")
_SOURCE_HEADER = struct.Struct(">BH")
MAX_MANIFEST_METADATA_BYTES = 0xFFFF
MAX_PROVIDER_ID_BYTES = 0xFF
MAX_LOCATOR_BYTES = 0xFFFF
MAX_SOURCES = 0xFF


def _require_bytes(name: str, value: bytes, *, maximum: int | None = None) -> None:
    if not isinstance(value, bytes):
        raise TypeError(f"{name} must be bytes")
    if maximum is not None and len(value) > maximum:
        raise ValueError(f"{name} exceeds {maximum} bytes")


@dataclass(frozen=True, slots=True)
class RetrievalSource:
    """Provider-independent retrieval hint.

    ``provider_id`` chooses an adapter supplied by the caller. ``locator`` is
    opaque to PollicinoNet core.
    """

    provider_id: str
    locator: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.provider_id, str) or not self.provider_id:
            raise ValueError("provider_id must be a non-empty string")
        try:
            provider_bytes = self.provider_id.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError("provider_id must be ASCII") from exc
        if len(provider_bytes) > MAX_PROVIDER_ID_BYTES:
            raise ValueError("provider_id is too long")
        _require_bytes("locator", self.locator, maximum=MAX_LOCATOR_BYTES)


@dataclass(frozen=True, slots=True)
class ContentManifest:
    """Complete exact-content identity resolved from an opaque coordinate."""

    object_class: int
    size_bytes: int
    sha256_digest: bytes
    sources: tuple[RetrievalSource, ...]
    metadata: bytes = b""
    version: int = MANIFEST_VERSION

    def __post_init__(self) -> None:
        if self.version != MANIFEST_VERSION:
            raise ValueError(f"unsupported manifest version: {self.version}")
        if not isinstance(self.object_class, int) or not 0 <= self.object_class <= 0xFF:
            raise ValueError("object_class must fit in one byte")
        if not isinstance(self.size_bytes, int) or not 0 <= self.size_bytes <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError("size_bytes must fit in an unsigned 64-bit integer")
        _require_bytes("sha256_digest", self.sha256_digest)
        if len(self.sha256_digest) != 32:
            raise ValueError("sha256_digest must be exactly 32 bytes")
        if not isinstance(self.sources, tuple) or not self.sources:
            raise ValueError("sources must be a non-empty tuple")
        if len(self.sources) > MAX_SOURCES:
            raise ValueError(f"sources exceeds {MAX_SOURCES} entries")
        if not all(isinstance(source, RetrievalSource) for source in self.sources):
            raise TypeError("sources must contain RetrievalSource values")
        _require_bytes("metadata", self.metadata, maximum=MAX_MANIFEST_METADATA_BYTES)

    def encode(self) -> bytes:
        body = bytearray(self.metadata)
        for source in self.sources:
            provider = source.provider_id.encode("ascii")
            body += _SOURCE_HEADER.pack(len(provider), len(source.locator))
            body += provider
            body += source.locator

        header = _MANIFEST_HEADER.pack(
            MANIFEST_MAGIC,
            self.version,
            self.object_class,
            self.size_bytes,
            self.sha256_digest,
            len(self.sources),
            len(self.metadata),
        )
        return header + bytes(body)

    @classmethod
    def decode(cls, data: bytes) -> ContentManifest:
        _require_bytes("data", data)
        if len(data) < _MANIFEST_HEADER.size:
            raise ValueError("manifest is shorter than the PNM1 header")

        magic, version, object_class, size_bytes, digest, source_count, metadata_len = _MANIFEST_HEADER.unpack_from(data)
        if magic != MANIFEST_MAGIC:
            raise ValueError("invalid PollicinoNet manifest magic")
        if version != MANIFEST_VERSION:
            raise ValueError(f"unsupported manifest version: {version}")
        if source_count == 0:
            raise ValueError("manifest has no retrieval sources")

        offset = _MANIFEST_HEADER.size
        metadata_end = offset + metadata_len
        if metadata_end > len(data):
            raise ValueError("manifest metadata is truncated")
        metadata = data[offset:metadata_end]
        offset = metadata_end

        sources: list[RetrievalSource] = []
        for _ in range(source_count):
            if offset + _SOURCE_HEADER.size > len(data):
                raise ValueError("manifest source header is truncated")
            provider_len, locator_len = _SOURCE_HEADER.unpack_from(data, offset)
            offset += _SOURCE_HEADER.size
            end = offset + provider_len + locator_len
            if end > len(data):
                raise ValueError("manifest source is truncated")
            provider_bytes = data[offset : offset + provider_len]
            locator = data[offset + provider_len : end]
            offset = end
            try:
                provider_id = provider_bytes.decode("ascii")
            except UnicodeDecodeError as exc:
                raise ValueError("manifest provider_id is not ASCII") from exc
            sources.append(RetrievalSource(provider_id=provider_id, locator=locator))

        if offset != len(data):
            raise ValueError("manifest contains trailing bytes")

        return cls(
            version=version,
            object_class=object_class,
            size_bytes=size_bytes,
            sha256_digest=digest,
            sources=tuple(sources),
            metadata=metadata,
        )


class ManifestResolver(Protocol):
    def resolve(self, coordinate: bytes) -> bytes:
        """Return the encoded PNM1 manifest for an opaque coordinate."""


class ContentProvider(Protocol):
    def fetch(self, locator: bytes) -> bytes:
        """Return bytes identified by a provider-specific opaque locator."""


class InMemoryResolver:
    """Standalone deterministic resolver used by PN experiments and tests."""

    def __init__(self) -> None:
        self._manifests: dict[bytes, bytes] = {}

    def register(self, coordinate: bytes, manifest: ContentManifest) -> None:
        _require_bytes("coordinate", coordinate)
        if not coordinate:
            raise ValueError("coordinate must not be empty")
        encoded = manifest.encode()
        previous = self._manifests.get(coordinate)
        if previous is not None and previous != encoded:
            raise ValueError("coordinate is already bound to a different manifest")
        self._manifests[coordinate] = encoded

    def resolve(self, coordinate: bytes) -> bytes:
        _require_bytes("coordinate", coordinate)
        try:
            return self._manifests[coordinate]
        except KeyError as exc:
            raise LookupError("coordinate was not resolved") from exc


class InMemoryContentProvider:
    """Standalone provider whose locators are arbitrary bytes."""

    def __init__(self) -> None:
        self._objects: dict[bytes, bytes] = {}

    def put(self, locator: bytes, content: bytes) -> None:
        _require_bytes("locator", locator)
        _require_bytes("content", content)
        if not locator:
            raise ValueError("locator must not be empty")
        previous = self._objects.get(locator)
        if previous is not None and previous != content:
            raise ValueError("locator is already bound to different content")
        self._objects[locator] = content

    def fetch(self, locator: bytes) -> bytes:
        _require_bytes("locator", locator)
        try:
            return self._objects[locator]
        except KeyError as exc:
            raise LookupError("content locator was not found") from exc


@dataclass(frozen=True, slots=True)
class RetrievalReport:
    scarce_link_bytes: int
    manifest_bytes: int
    content_bytes: int
    provider_attempts: int
    failed_verification_attempts: int
    selected_provider_id: str
    expected_sha256: str
    reconstructed_sha256: str
    exact: bool


class RetrievalError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        manifest_bytes: int = 0,
        content_bytes: int = 0,
        provider_attempts: int = 0,
        failed_verification_attempts: int = 0,
    ) -> None:
        super().__init__(message)
        self.manifest_bytes = manifest_bytes
        self.content_bytes = content_bytes
        self.provider_attempts = provider_attempts
        self.failed_verification_attempts = failed_verification_attempts


def manifest_for_content(
    content: bytes,
    *,
    object_class: int,
    sources: tuple[RetrievalSource, ...],
    metadata: bytes = b"",
) -> ContentManifest:
    _require_bytes("content", content)
    return ContentManifest(
        object_class=object_class,
        size_bytes=len(content),
        sha256_digest=hashlib.sha256(content).digest(),
        sources=sources,
        metadata=metadata,
    )


def retrieve_exact(
    descriptor: DiscoveryDescriptor,
    *,
    resolver: ManifestResolver,
    providers: Mapping[str, ContentProvider],
) -> tuple[bytes, RetrievalReport]:
    """Resolve an opaque coordinate and retrieve content with full-hash proof.

    The discovery coordinate is never treated as content identity. Exactness is
    established only after the resolved manifest's complete SHA-256 digest and
    declared size both match the retrieved bytes. ``content_bytes`` accounts
    for every provider payload successfully fetched, including hash-invalid
    attempts before a later verified source succeeds.
    """

    descriptor_wire = descriptor.encode()
    manifest_wire = resolver.resolve(descriptor.rendezvous_key)
    manifest = ContentManifest.decode(manifest_wire)

    provider_attempts = 0
    failed_verification_attempts = 0
    retrieved_content_bytes = 0

    for source in manifest.sources:
        provider = providers.get(source.provider_id)
        if provider is None:
            continue
        provider_attempts += 1
        try:
            content = provider.fetch(source.locator)
        except LookupError:
            continue

        retrieved_content_bytes += len(content)
        digest = hashlib.sha256(content).digest()
        if len(content) != manifest.size_bytes or digest != manifest.sha256_digest:
            failed_verification_attempts += 1
            continue

        report = RetrievalReport(
            scarce_link_bytes=len(descriptor_wire),
            manifest_bytes=len(manifest_wire),
            content_bytes=retrieved_content_bytes,
            provider_attempts=provider_attempts,
            failed_verification_attempts=failed_verification_attempts,
            selected_provider_id=source.provider_id,
            expected_sha256=manifest.sha256_digest.hex(),
            reconstructed_sha256=digest.hex(),
            exact=True,
        )
        return content, report

    raise RetrievalError(
        "no retrieval source produced content matching the resolved manifest",
        manifest_bytes=len(manifest_wire),
        content_bytes=retrieved_content_bytes,
        provider_attempts=provider_attempts,
        failed_verification_attempts=failed_verification_attempts,
    )
