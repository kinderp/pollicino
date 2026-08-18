from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import struct

from .link import ScarceLinkProfile, transmit_exact


CHUNK_MANIFEST_MAGIC = b"PCM1"
CHUNK_MANIFEST_VERSION = 1
AVAILABILITY_MAGIC = b"PNA1"
AVAILABILITY_VERSION = 1
_CHUNK_MANIFEST_HEADER = struct.Struct(">4sBIQ32sH")
_CHUNK_ENTRY = struct.Struct(">I32s")
_AVAILABILITY_HEADER = struct.Struct(">4sB32sH")
_CHUNK_PACKET_HEADER = struct.Struct(">H")
MAX_CHUNKS = 0xFFFF


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


@dataclass(frozen=True, slots=True)
class ChunkRef:
    length: int
    sha256_digest: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.length, int) or not 0 <= self.length <= 0xFFFFFFFF:
            raise ValueError("chunk length must fit in an unsigned 32-bit integer")
        if not isinstance(self.sha256_digest, bytes) or len(self.sha256_digest) != 32:
            raise ValueError("chunk sha256_digest must be exactly 32 bytes")


@dataclass(frozen=True, slots=True)
class ChunkManifest:
    chunk_size: int
    object_size: int
    object_sha256: bytes
    chunks: tuple[ChunkRef, ...]
    version: int = CHUNK_MANIFEST_VERSION

    def __post_init__(self) -> None:
        if self.version != CHUNK_MANIFEST_VERSION:
            raise ValueError(f"unsupported chunk manifest version: {self.version}")
        if not isinstance(self.chunk_size, int) or not 1 <= self.chunk_size <= 0xFFFFFFFF:
            raise ValueError("chunk_size must be a positive unsigned 32-bit integer")
        if not isinstance(self.object_size, int) or not 0 <= self.object_size <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError("object_size must fit in an unsigned 64-bit integer")
        if not isinstance(self.object_sha256, bytes) or len(self.object_sha256) != 32:
            raise ValueError("object_sha256 must be exactly 32 bytes")
        if not isinstance(self.chunks, tuple) or not self.chunks:
            raise ValueError("chunks must be a non-empty tuple")
        if len(self.chunks) > MAX_CHUNKS:
            raise ValueError(f"chunk count exceeds {MAX_CHUNKS}")
        if not all(isinstance(chunk, ChunkRef) for chunk in self.chunks):
            raise TypeError("chunks must contain ChunkRef values")
        if sum(chunk.length for chunk in self.chunks) != self.object_size:
            raise ValueError("chunk lengths do not sum to object_size")
        if any(chunk.length > self.chunk_size for chunk in self.chunks):
            raise ValueError("chunk length exceeds chunk_size")
        if any(chunk.length != self.chunk_size for chunk in self.chunks[:-1]):
            raise ValueError("only the final chunk may be shorter than chunk_size")

    def encode(self) -> bytes:
        body = bytearray()
        for chunk in self.chunks:
            body += _CHUNK_ENTRY.pack(chunk.length, chunk.sha256_digest)
        return _CHUNK_MANIFEST_HEADER.pack(
            CHUNK_MANIFEST_MAGIC,
            self.version,
            self.chunk_size,
            self.object_size,
            self.object_sha256,
            len(self.chunks),
        ) + bytes(body)

    @classmethod
    def decode(cls, data: bytes) -> ChunkManifest:
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        if len(data) < _CHUNK_MANIFEST_HEADER.size:
            raise ValueError("chunk manifest is shorter than the PCM1 header")
        magic, version, chunk_size, object_size, object_sha, chunk_count = _CHUNK_MANIFEST_HEADER.unpack_from(data)
        if magic != CHUNK_MANIFEST_MAGIC:
            raise ValueError("invalid chunk manifest magic")
        if version != CHUNK_MANIFEST_VERSION:
            raise ValueError(f"unsupported chunk manifest version: {version}")
        if chunk_count == 0:
            raise ValueError("chunk manifest has no chunks")
        expected = _CHUNK_MANIFEST_HEADER.size + chunk_count * _CHUNK_ENTRY.size
        if len(data) != expected:
            raise ValueError(f"chunk manifest length mismatch: expected {expected}, got {len(data)}")
        chunks = []
        offset = _CHUNK_MANIFEST_HEADER.size
        for _ in range(chunk_count):
            length, digest = _CHUNK_ENTRY.unpack_from(data, offset)
            chunks.append(ChunkRef(length=length, sha256_digest=digest))
            offset += _CHUNK_ENTRY.size
        return cls(
            version=version,
            chunk_size=chunk_size,
            object_size=object_size,
            object_sha256=object_sha,
            chunks=tuple(chunks),
        )

    @property
    def fingerprint(self) -> bytes:
        return _sha256(self.encode())


@dataclass(frozen=True, slots=True)
class AvailabilitySummary:
    manifest_fingerprint: bytes
    chunk_count: int
    available_bits: bytes
    version: int = AVAILABILITY_VERSION

    def __post_init__(self) -> None:
        if self.version != AVAILABILITY_VERSION:
            raise ValueError(f"unsupported availability version: {self.version}")
        if not isinstance(self.manifest_fingerprint, bytes) or len(self.manifest_fingerprint) != 32:
            raise ValueError("manifest_fingerprint must be exactly 32 bytes")
        if not isinstance(self.chunk_count, int) or not 1 <= self.chunk_count <= MAX_CHUNKS:
            raise ValueError("chunk_count is out of range")
        expected = math.ceil(self.chunk_count / 8)
        if not isinstance(self.available_bits, bytes) or len(self.available_bits) != expected:
            raise ValueError(f"available_bits must be exactly {expected} bytes")
        unused = expected * 8 - self.chunk_count
        if unused and self.available_bits[-1] >> (8 - unused):
            raise ValueError("unused availability bits must be zero")

    def has(self, index: int) -> bool:
        if not isinstance(index, int) or not 0 <= index < self.chunk_count:
            raise IndexError("chunk index out of range")
        byte_index, bit_index = divmod(index, 8)
        return bool(self.available_bits[byte_index] & (1 << bit_index))

    def encode(self) -> bytes:
        return _AVAILABILITY_HEADER.pack(
            AVAILABILITY_MAGIC,
            self.version,
            self.manifest_fingerprint,
            self.chunk_count,
        ) + self.available_bits

    @classmethod
    def decode(cls, data: bytes) -> AvailabilitySummary:
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        if len(data) < _AVAILABILITY_HEADER.size:
            raise ValueError("availability summary is shorter than the PNA1 header")
        magic, version, fingerprint, chunk_count = _AVAILABILITY_HEADER.unpack_from(data)
        if magic != AVAILABILITY_MAGIC:
            raise ValueError("invalid availability summary magic")
        expected_bits = math.ceil(chunk_count / 8)
        expected = _AVAILABILITY_HEADER.size + expected_bits
        if len(data) != expected:
            raise ValueError(f"availability summary length mismatch: expected {expected}, got {len(data)}")
        return cls(
            version=version,
            manifest_fingerprint=fingerprint,
            chunk_count=chunk_count,
            available_bits=data[_AVAILABILITY_HEADER.size :],
        )


class PollicinoStore:
    """Minimal content-addressed chunk store with full-hash verification."""

    def __init__(self) -> None:
        self._chunks: dict[bytes, bytes] = {}

    def put(self, content: bytes) -> bytes:
        if not isinstance(content, bytes):
            raise TypeError("content must be bytes")
        digest = _sha256(content)
        previous = self._chunks.get(digest)
        if previous is not None and previous != content:
            raise AssertionError("SHA-256 collision detected inside PollicinoStore")
        self._chunks[digest] = content
        return digest

    def has(self, digest: bytes) -> bool:
        return digest in self._chunks

    def get(self, digest: bytes) -> bytes:
        try:
            content = self._chunks[digest]
        except KeyError as exc:
            raise LookupError("chunk is not present in PollicinoStore") from exc
        if _sha256(content) != digest:
            raise ValueError("stored chunk failed SHA-256 verification")
        return content

    def __len__(self) -> int:
        return len(self._chunks)


def build_chunk_manifest(data: bytes, *, chunk_size: int) -> tuple[ChunkManifest, tuple[bytes, ...]]:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if not data:
        raise ValueError("PN-005 chunk manifests require a non-empty object")
    if not isinstance(chunk_size, int) or not 1 <= chunk_size <= 0xFFFFFFFF:
        raise ValueError("chunk_size must be a positive unsigned 32-bit integer")
    chunks = tuple(data[offset : offset + chunk_size] for offset in range(0, len(data), chunk_size))
    manifest = ChunkManifest(
        chunk_size=chunk_size,
        object_size=len(data),
        object_sha256=_sha256(data),
        chunks=tuple(ChunkRef(length=len(chunk), sha256_digest=_sha256(chunk)) for chunk in chunks),
    )
    return manifest, chunks


def availability_for(manifest: ChunkManifest, store: PollicinoStore) -> AvailabilitySummary:
    bits = bytearray(math.ceil(len(manifest.chunks) / 8))
    for index, chunk in enumerate(manifest.chunks):
        if store.has(chunk.sha256_digest):
            byte_index, bit_index = divmod(index, 8)
            bits[byte_index] |= 1 << bit_index
    return AvailabilitySummary(
        manifest_fingerprint=manifest.fingerprint,
        chunk_count=len(manifest.chunks),
        available_bits=bytes(bits),
    )


def reconstruct_from_store(manifest: ChunkManifest, store: PollicinoStore) -> bytes:
    pieces = []
    for ref in manifest.chunks:
        chunk = store.get(ref.sha256_digest)
        if len(chunk) != ref.length:
            raise ValueError("stored chunk length does not match manifest")
        pieces.append(chunk)
    data = b"".join(pieces)
    if len(data) != manifest.object_size or _sha256(data) != manifest.object_sha256:
        raise ValueError("reconstructed object failed manifest verification")
    return data


@dataclass(frozen=True, slots=True)
class StoreSyncReport:
    object_bytes: int
    chunk_count: int
    cached_chunk_count: int
    cached_source_bytes: int
    missing_chunk_count: int
    missing_source_bytes: int
    manifest_wire_bytes: int
    availability_wire_bytes: int
    chunk_wire_bytes: int
    total_scarce_wire_bytes: int
    total_scarce_if_manifest_pre_resolved: int
    retransmissions: int
    exact: bool


def sync_missing_chunks(
    data: bytes,
    *,
    chunk_size: int,
    sender_store: PollicinoStore,
    receiver_store: PollicinoStore,
    profile: ScarceLinkProfile,
    transfer_id_base: int,
    manifest_on_scarce: bool = True,
) -> tuple[bytes, StoreSyncReport]:
    """Synchronize only chunks absent from the receiver's verified store.

    The receiver first obtains the chunk manifest (or receives it out of band),
    returns a compact PNA1 availability bitset, and then receives only missing
    chunks. All manifest/summary/chunk transfers use the same generic PN-002
    exact link primitive, so bytes and retries remain explicitly accounted.
    """

    manifest, chunks = build_chunk_manifest(data, chunk_size=chunk_size)
    for chunk in chunks:
        sender_store.put(chunk)

    next_transfer_id = transfer_id_base
    manifest_wire_bytes = 0
    retransmissions = 0
    if manifest_on_scarce:
        received_manifest_wire, manifest_report = transmit_exact(
            manifest.encode(),
            transfer_id=next_transfer_id,
            profile=profile,
        )
        next_transfer_id += 1
        received_manifest = ChunkManifest.decode(received_manifest_wire)
        if received_manifest != manifest:
            raise AssertionError("chunk manifest changed during exact transfer")
        manifest_wire_bytes = manifest_report.total_wire_bytes
        retransmissions += manifest_report.retransmissions
    else:
        received_manifest = manifest

    summary = availability_for(received_manifest, receiver_store)
    received_summary_wire, summary_report = transmit_exact(
        summary.encode(),
        transfer_id=next_transfer_id,
        profile=profile,
    )
    next_transfer_id += 1
    received_summary = AvailabilitySummary.decode(received_summary_wire)
    if received_summary.manifest_fingerprint != received_manifest.fingerprint:
        raise ValueError("availability summary targets a different chunk manifest")
    retransmissions += summary_report.retransmissions

    cached_chunk_count = 0
    cached_source_bytes = 0
    missing_indices = []
    for index, ref in enumerate(received_manifest.chunks):
        if received_summary.has(index):
            cached_chunk_count += 1
            cached_source_bytes += ref.length
        else:
            missing_indices.append(index)

    chunk_wire_bytes = 0
    missing_source_bytes = 0
    for index in missing_indices:
        ref = received_manifest.chunks[index]
        source_chunk = sender_store.get(ref.sha256_digest)
        packet = _CHUNK_PACKET_HEADER.pack(index) + source_chunk
        received_packet, chunk_report = transmit_exact(
            packet,
            transfer_id=next_transfer_id,
            profile=profile,
        )
        next_transfer_id += 1
        if len(received_packet) < _CHUNK_PACKET_HEADER.size:
            raise ValueError("received chunk packet is truncated")
        received_index = _CHUNK_PACKET_HEADER.unpack_from(received_packet)[0]
        if received_index != index:
            raise ValueError("received chunk packet index mismatch")
        received_chunk = received_packet[_CHUNK_PACKET_HEADER.size :]
        if len(received_chunk) != ref.length or _sha256(received_chunk) != ref.sha256_digest:
            raise ValueError("received chunk failed manifest verification")
        receiver_store.put(received_chunk)
        missing_source_bytes += ref.length
        chunk_wire_bytes += chunk_report.total_wire_bytes
        retransmissions += chunk_report.retransmissions

    reconstructed = reconstruct_from_store(received_manifest, receiver_store)
    availability_wire_bytes = summary_report.total_wire_bytes
    total = manifest_wire_bytes + availability_wire_bytes + chunk_wire_bytes
    report = StoreSyncReport(
        object_bytes=len(data),
        chunk_count=len(received_manifest.chunks),
        cached_chunk_count=cached_chunk_count,
        cached_source_bytes=cached_source_bytes,
        missing_chunk_count=len(missing_indices),
        missing_source_bytes=missing_source_bytes,
        manifest_wire_bytes=manifest_wire_bytes,
        availability_wire_bytes=availability_wire_bytes,
        chunk_wire_bytes=chunk_wire_bytes,
        total_scarce_wire_bytes=total,
        total_scarce_if_manifest_pre_resolved=availability_wire_bytes + chunk_wire_bytes,
        retransmissions=retransmissions,
        exact=reconstructed == data,
    )
    return reconstructed, report
