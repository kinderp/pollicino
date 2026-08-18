from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
import zlib


FRAME_MAGIC = b"PNF1"
_FRAME_HEADER = struct.Struct(">4sIHHHI")
FRAME_HEADER_BYTES = _FRAME_HEADER.size
_MAX_PPM = 1_000_000


def _bounded_int(name: str, value: int, minimum: int, maximum: int) -> None:
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an int")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")


@dataclass(frozen=True, slots=True)
class FragmentFrame:
    """One deterministic PollicinoNet exact-transfer fragment."""

    transfer_id: int
    sequence: int
    total: int
    payload: bytes

    def __post_init__(self) -> None:
        _bounded_int("transfer_id", self.transfer_id, 0, 0xFFFFFFFF)
        _bounded_int("total", self.total, 1, 0xFFFF)
        _bounded_int("sequence", self.sequence, 0, self.total - 1)
        if not isinstance(self.payload, bytes):
            raise TypeError("payload must be bytes")
        if len(self.payload) > 0xFFFF:
            raise ValueError("payload exceeds frame length field")

    def encode(self) -> bytes:
        crc = zlib.crc32(self.payload) & 0xFFFFFFFF
        return _FRAME_HEADER.pack(
            FRAME_MAGIC,
            self.transfer_id,
            self.sequence,
            self.total,
            len(self.payload),
            crc,
        ) + self.payload

    @classmethod
    def decode(cls, data: bytes) -> FragmentFrame:
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        if len(data) < FRAME_HEADER_BYTES:
            raise ValueError("frame is shorter than the PNF1 header")

        magic, transfer_id, sequence, total, payload_len, expected_crc = _FRAME_HEADER.unpack_from(data)
        if magic != FRAME_MAGIC:
            raise ValueError("invalid PollicinoNet frame magic")
        if total == 0 or sequence >= total:
            raise ValueError("invalid frame sequence/total")

        expected_len = FRAME_HEADER_BYTES + payload_len
        if len(data) != expected_len:
            raise ValueError(f"frame length mismatch: expected {expected_len}, got {len(data)}")

        payload = data[FRAME_HEADER_BYTES:]
        actual_crc = zlib.crc32(payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError("frame CRC mismatch")

        return cls(
            transfer_id=transfer_id,
            sequence=sequence,
            total=total,
            payload=payload,
        )

    @property
    def wire_size(self) -> int:
        return FRAME_HEADER_BYTES + len(self.payload)


def fragment_payload(data: bytes, *, transfer_id: int, max_frame_bytes: int) -> tuple[FragmentFrame, ...]:
    """Split arbitrary bytes into deterministic PNF1 frames.

    ``max_frame_bytes`` is a generic link budget for the whole encoded frame,
    not a LoRa-specific constant.
    """

    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    _bounded_int("transfer_id", transfer_id, 0, 0xFFFFFFFF)
    if not isinstance(max_frame_bytes, int):
        raise TypeError("max_frame_bytes must be an int")
    if max_frame_bytes <= FRAME_HEADER_BYTES:
        raise ValueError("max_frame_bytes must leave room for at least one payload byte")

    payload_capacity = max_frame_bytes - FRAME_HEADER_BYTES
    chunks = [data[i : i + payload_capacity] for i in range(0, len(data), payload_capacity)]
    if not chunks:
        chunks = [b""]
    if len(chunks) > 0xFFFF:
        raise ValueError("transfer requires more than 65535 frames")

    total = len(chunks)
    return tuple(
        FragmentFrame(transfer_id=transfer_id, sequence=sequence, total=total, payload=chunk)
        for sequence, chunk in enumerate(chunks)
    )


def reassemble_frames(frames: tuple[FragmentFrame, ...] | list[FragmentFrame]) -> bytes:
    """Reassemble a complete transfer, tolerating identical duplicate frames."""

    if not frames:
        raise ValueError("at least one frame is required")

    first = frames[0]
    received: dict[int, bytes] = {}
    for frame in frames:
        if frame.transfer_id != first.transfer_id or frame.total != first.total:
            raise ValueError("frames belong to different transfers")
        previous = received.get(frame.sequence)
        if previous is not None and previous != frame.payload:
            raise ValueError("conflicting duplicate frame")
        received[frame.sequence] = frame.payload

    missing = [sequence for sequence in range(first.total) if sequence not in received]
    if missing:
        raise ValueError(f"transfer is incomplete; missing sequences: {missing}")

    return b"".join(received[sequence] for sequence in range(first.total))


@dataclass(frozen=True, slots=True)
class ScarceLinkProfile:
    """Transport-independent deterministic impairment model.

    Loss values use parts-per-million integers to avoid floating-point routing
    decisions and make experiment inputs explicit.
    """

    max_frame_bytes: int
    bitrate_bps: int
    data_loss_ppm: int = 0
    ack_loss_ppm: int = 0
    max_retries: int = 3
    ack_bytes: int = 0
    seed: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.max_frame_bytes, int) or self.max_frame_bytes <= FRAME_HEADER_BYTES:
            raise ValueError("max_frame_bytes must exceed the PNF1 header size")
        if not isinstance(self.bitrate_bps, int) or self.bitrate_bps <= 0:
            raise ValueError("bitrate_bps must be a positive integer")
        _bounded_int("data_loss_ppm", self.data_loss_ppm, 0, _MAX_PPM)
        _bounded_int("ack_loss_ppm", self.ack_loss_ppm, 0, _MAX_PPM)
        _bounded_int("max_retries", self.max_retries, 0, 255)
        _bounded_int("ack_bytes", self.ack_bytes, 0, 0xFFFF)
        _bounded_int("seed", self.seed, 0, 0xFFFFFFFFFFFFFFFF)

    @property
    def payload_capacity_bytes(self) -> int:
        return self.max_frame_bytes - FRAME_HEADER_BYTES


@dataclass(frozen=True, slots=True)
class TransferReport:
    source_bytes: int
    reconstructed_bytes: int
    frame_count: int
    payload_capacity_bytes: int
    data_transmissions: int
    retransmissions: int
    duplicate_deliveries: int
    ack_transmissions: int
    data_wire_bytes: int
    ack_wire_bytes: int
    total_wire_bytes: int
    nominal_serialization_seconds: float
    success: bool


class DeliveryError(RuntimeError):
    pass


def _lost(profile: ScarceLinkProfile, channel: bytes, sequence: int, attempt: int, ppm: int) -> bool:
    if ppm == 0:
        return False
    if ppm == _MAX_PPM:
        return True

    digest = hashlib.blake2s(digest_size=8, person=b"PNL1")
    digest.update(struct.pack(">Q", profile.seed))
    digest.update(channel)
    digest.update(struct.pack(">II", sequence, attempt))
    value = int.from_bytes(digest.digest(), "big") % _MAX_PPM
    return value < ppm


def transmit_exact(
    data: bytes,
    *,
    transfer_id: int,
    profile: ScarceLinkProfile,
) -> tuple[bytes, TransferReport]:
    """Transfer bytes with deterministic fragmentation and stop-and-wait retry.

    A data frame can be delivered while its acknowledgement is lost. The
    sender then retries and the receiver observes an identical duplicate,
    exercising deduplication without changing the exact reconstructed bytes.
    """

    frames = fragment_payload(data, transfer_id=transfer_id, max_frame_bytes=profile.max_frame_bytes)
    received: dict[int, FragmentFrame] = {}

    data_transmissions = 0
    duplicate_deliveries = 0
    ack_transmissions = 0
    data_wire_bytes = 0
    ack_wire_bytes = 0

    for frame in frames:
        encoded = frame.encode()
        acknowledged = False

        for attempt in range(profile.max_retries + 1):
            data_transmissions += 1
            data_wire_bytes += len(encoded)

            if _lost(profile, b"data", frame.sequence, attempt, profile.data_loss_ppm):
                continue

            if frame.sequence in received:
                duplicate_deliveries += 1
            else:
                received[frame.sequence] = frame

            if profile.ack_bytes:
                ack_transmissions += 1
                ack_wire_bytes += profile.ack_bytes
                if _lost(profile, b"ack", frame.sequence, attempt, profile.ack_loss_ppm):
                    continue

            acknowledged = True
            break

        if not acknowledged:
            raise DeliveryError(
                f"frame {frame.sequence}/{frame.total} exceeded retry budget "
                f"after {profile.max_retries + 1} attempts"
            )

    reconstructed = reassemble_frames(list(received.values()))
    if reconstructed != data:
        raise AssertionError("exact transfer reconstruction mismatch")

    total_wire_bytes = data_wire_bytes + ack_wire_bytes
    report = TransferReport(
        source_bytes=len(data),
        reconstructed_bytes=len(reconstructed),
        frame_count=len(frames),
        payload_capacity_bytes=profile.payload_capacity_bytes,
        data_transmissions=data_transmissions,
        retransmissions=data_transmissions - len(frames),
        duplicate_deliveries=duplicate_deliveries,
        ack_transmissions=ack_transmissions,
        data_wire_bytes=data_wire_bytes,
        ack_wire_bytes=ack_wire_bytes,
        total_wire_bytes=total_wire_bytes,
        nominal_serialization_seconds=(total_wire_bytes * 8) / profile.bitrate_bps,
        success=True,
    )
    return reconstructed, report
