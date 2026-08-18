from __future__ import annotations

from dataclasses import dataclass
import struct

MAGIC = b"PND1"
MAX_KEY_BYTES = 32
MAX_METADATA_BYTES = 64
MAX_AUTH_BYTES = 32

# magic, version, object_class, flags, capability_mask, ttl_seconds,
# hop_limit, key_len, metadata_len, auth_len, nonce
_HEADER = struct.Struct(">4sBBBHIBBBBQ")


def _bounded_int(name: str, value: int, maximum: int) -> None:
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an int")
    if not 0 <= value <= maximum:
        raise ValueError(f"{name} must be between 0 and {maximum}")


def _bounded_bytes(name: str, value: bytes, maximum: int, *, minimum: int = 0) -> None:
    if not isinstance(value, bytes):
        raise TypeError(f"{name} must be bytes")
    if not minimum <= len(value) <= maximum:
        raise ValueError(f"{name} length must be between {minimum} and {maximum} bytes")


@dataclass(frozen=True, slots=True)
class DiscoveryDescriptor:
    """Transport-independent compact rendezvous descriptor.

    The core deliberately assigns no application meaning to ``object_class``,
    ``flags`` or ``metadata``. Integrations may define mappings externally.
    This keeps PollicinoNet usable without DNA, LoRa, or any other application.
    """

    object_class: int
    rendezvous_key: bytes
    ttl_seconds: int
    nonce: int
    capability_mask: int = 0
    flags: int = 0
    hop_limit: int = 0
    metadata: bytes = b""
    authenticator: bytes = b""
    version: int = 1

    def __post_init__(self) -> None:
        _bounded_int("version", self.version, 255)
        if self.version != 1:
            raise ValueError("only DiscoveryDescriptor version 1 is supported")
        _bounded_int("object_class", self.object_class, 255)
        _bounded_int("flags", self.flags, 255)
        _bounded_int("capability_mask", self.capability_mask, 0xFFFF)
        _bounded_int("ttl_seconds", self.ttl_seconds, 0xFFFFFFFF)
        _bounded_int("hop_limit", self.hop_limit, 255)
        _bounded_int("nonce", self.nonce, 0xFFFFFFFFFFFFFFFF)
        _bounded_bytes("rendezvous_key", self.rendezvous_key, MAX_KEY_BYTES, minimum=1)
        _bounded_bytes("metadata", self.metadata, MAX_METADATA_BYTES)
        _bounded_bytes("authenticator", self.authenticator, MAX_AUTH_BYTES)

    def encode(self) -> bytes:
        header = _HEADER.pack(
            MAGIC,
            self.version,
            self.object_class,
            self.flags,
            self.capability_mask,
            self.ttl_seconds,
            self.hop_limit,
            len(self.rendezvous_key),
            len(self.metadata),
            len(self.authenticator),
            self.nonce,
        )
        return header + self.rendezvous_key + self.metadata + self.authenticator

    @classmethod
    def decode(cls, data: bytes) -> DiscoveryDescriptor:
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        if len(data) < _HEADER.size:
            raise ValueError("descriptor is shorter than the PND1 header")

        (
            magic,
            version,
            object_class,
            flags,
            capability_mask,
            ttl_seconds,
            hop_limit,
            key_len,
            metadata_len,
            auth_len,
            nonce,
        ) = _HEADER.unpack_from(data)

        if magic != MAGIC:
            raise ValueError("invalid PollicinoNet discovery magic")
        if key_len == 0 or key_len > MAX_KEY_BYTES:
            raise ValueError("invalid rendezvous key length")
        if metadata_len > MAX_METADATA_BYTES:
            raise ValueError("invalid metadata length")
        if auth_len > MAX_AUTH_BYTES:
            raise ValueError("invalid authenticator length")

        expected = _HEADER.size + key_len + metadata_len + auth_len
        if len(data) != expected:
            raise ValueError(f"descriptor length mismatch: expected {expected}, got {len(data)}")

        cursor = _HEADER.size
        rendezvous_key = data[cursor : cursor + key_len]
        cursor += key_len
        metadata = data[cursor : cursor + metadata_len]
        cursor += metadata_len
        authenticator = data[cursor : cursor + auth_len]

        return cls(
            version=version,
            object_class=object_class,
            flags=flags,
            capability_mask=capability_mask,
            ttl_seconds=ttl_seconds,
            hop_limit=hop_limit,
            nonce=nonce,
            rendezvous_key=rendezvous_key,
            metadata=metadata,
            authenticator=authenticator,
        )

    @property
    def encoded_size(self) -> int:
        return _HEADER.size + len(self.rendezvous_key) + len(self.metadata) + len(self.authenticator)
