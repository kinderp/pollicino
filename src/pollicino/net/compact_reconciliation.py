from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
import hashlib
import math
import struct
from typing import Sequence

from .bearer import ImpairmentAction, LinkDirection
from .catalog import (
    MAX_CATALOG_ITEMS,
    MAX_LOGICAL_KEY_BYTES,
    BoundedReferenceCatalog,
    CatalogBoundsError,
    ReferenceConflictError,
)
from .endpoint import (
    B2BoundsError,
    B2DecodeError,
    B2MessageType,
    B2ProtocolError,
    EncodedBearerAttemptResult,
    EncodedMessageBearer,
    IndependentEndpoint,
    MAX_B2_IDENTITIES_PER_MESSAGE,
    MAX_B2_MESSAGE_BYTES,
    AdvertisementMessage,
    AdvertisedIdentity,
    RecordKind,
    RecordMessage,
    RequestMessage,
    _Reader,
    _decode_identity,
    _encode_identity,
    _identity_sort_key,
    decode_message,
    encode_message,
    message_type,
    record_digest,
)
from .local_persistence import PersistenceError
from .query import (
    MAX_STORED_QUERIES,
    MAX_STORED_RESULTS,
    QueryConflictError,
    QueryResultBoundsError,
    QueryResultStore,
    ResultConflictError,
    ResultIdentity,
)


EXPERIMENTAL_B2C_ENCODING = "pollicino.experimental-b2c.v1"
EXPERIMENTAL_B2C_ACCOUNTING_ONLY = "EXPERIMENTAL_B2C_ACCOUNTING_ONLY"
B2C_MAGIC = b"PB2C"
B2C_VERSION = 1
FINGERPRINT_BYTES = 8
CHECKSUM_BYTES = 4
FULL_SET_DIGEST_BYTES = 32
IBLT_HASH_COUNT = 3
MAX_COMPACT_CAPACITY = 1_000
MAX_COMPACT_IDENTITIES = max(
    MAX_CATALOG_ITEMS, MAX_STORED_QUERIES, MAX_STORED_RESULTS
)
MAX_COMPACT_ROUNDS = 4
MAX_COMPACT_FALLBACKS = 1
MAX_COMPACT_ATTEMPTS = 100
MAX_COMPACT_TRACE = MAX_COMPACT_ATTEMPTS

_HEADER = struct.Struct(">4sBBI32s")
_SUMMARY = struct.Struct(">BHHI32s")
_CELL = struct.Struct(">hQI")
_REQUEST = struct.Struct(">BH")
_REVEAL = struct.Struct(">BH")


class CompactBoundsError(ValueError):
    pass


class CompactDecodeError(ValueError):
    pass


class CompactProtocolError(RuntimeError):
    pass


class CompactMessageType(IntEnum):
    SUMMARY = 1
    FINGERPRINT_REQUEST = 2
    IDENTITY_REVEAL = 3


class CompactDecodeStatus(str, Enum):
    EQUAL = "EQUAL"
    DECODED = "DECODED"
    CAPACITY_EXCEEDED = "CAPACITY_EXCEEDED"
    FINGERPRINT_AMBIGUITY = "FINGERPRINT_AMBIGUITY"
    ROOT_MISMATCH = "ROOT_MISMATCH"


class CompactContactOutcome(str, Enum):
    EQUAL = "EQUAL"
    DISCOVERED = "DISCOVERED"
    PARTIAL_NOT_DELIVERED = "PARTIAL_NOT_DELIVERED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    DISCONNECTED = "DISCONNECTED"
    SENDER_UNCERTAIN = "SENDER_UNCERTAIN"
    FALLBACK_REQUIRED = "FALLBACK_REQUIRED"
    ERROR = "ERROR"


Identity = bytes | ResultIdentity


@dataclass(frozen=True, slots=True)
class IBLTCell:
    count: int
    fingerprint_xor: int
    checksum_xor: int

    def __post_init__(self) -> None:
        if type(self.count) is not int or not -(2**15) <= self.count < 2**15:
            raise CompactBoundsError("IBLT count is outside int16")
        if type(self.fingerprint_xor) is not int or not 0 <= self.fingerprint_xor < 2**64:
            raise CompactBoundsError("IBLT fingerprint XOR is outside uint64")
        if type(self.checksum_xor) is not int or not 0 <= self.checksum_xor < 2**32:
            raise CompactBoundsError("IBLT checksum XOR is outside uint32")


def _cell_count(capacity: int) -> int:
    if type(capacity) is not int or not 1 <= capacity <= MAX_COMPACT_CAPACITY:
        raise CompactBoundsError(
            f"capacity must be between 1 and {MAX_COMPACT_CAPACITY}"
        )
    # Two cells per admitted difference plus a small fixed reserve keep the
    # largest sketch below the inherited B1 complete-unit bound while avoiding
    # pathological tiny-table index collisions.
    return capacity * 2 + 31


MAX_COMPACT_CELLS = _cell_count(MAX_COMPACT_CAPACITY)
MAX_COMPACT_REVEALS_PER_MESSAGE = (
    MAX_B2_MESSAGE_BYTES - _HEADER.size - _REVEAL.size
) // (FINGERPRINT_BYTES + 4 + 256 + FULL_SET_DIGEST_BYTES)
MAX_COMPACT_MESSAGE_BYTES = _HEADER.size + max(
    _SUMMARY.size + MAX_COMPACT_CELLS * _CELL.size,
    _REQUEST.size + MAX_COMPACT_CAPACITY * FINGERPRINT_BYTES,
    _REVEAL.size
    + MAX_COMPACT_REVEALS_PER_MESSAGE
    * (FINGERPRINT_BYTES + 4 + 256 + FULL_SET_DIGEST_BYTES),
)
if MAX_COMPACT_MESSAGE_BYTES > MAX_B2_MESSAGE_BYTES:
    raise RuntimeError("maximum compact message exceeds inherited B1 unit")


def _fingerprint(kind: RecordKind, identity: Identity, digest: bytes) -> int:
    if not isinstance(digest, bytes) or len(digest) != 32:
        raise CompactBoundsError("record digest has invalid size")
    encoded = bytes((kind,)) + _encode_identity(kind, identity) + digest
    return int.from_bytes(hashlib.sha256(b"B2C-FP" + encoded).digest()[:8], "big")


def _checksum(fingerprint: int) -> int:
    raw = fingerprint.to_bytes(FINGERPRINT_BYTES, "big")
    return int.from_bytes(hashlib.sha256(b"B2C-CHECK" + raw).digest()[:4], "big")


def _indexes(fingerprint: int, cell_count: int) -> tuple[int, ...]:
    raw = fingerprint.to_bytes(FINGERPRINT_BYTES, "big")
    digest = hashlib.sha256(b"B2C-INDEX" + raw).digest()
    indexes: list[int] = []
    cursor = 0
    while len(indexes) < IBLT_HASH_COUNT:
        candidate = int.from_bytes(digest[cursor : cursor + 8], "big") % cell_count
        cursor += 8
        while candidate in indexes:
            candidate = (candidate + 1) % cell_count
        indexes.append(candidate)
    return tuple(indexes)


def _identity_digest(kind: RecordKind, identity: Identity) -> bytes:
    return hashlib.sha256(b"B2C-IDENTITY" + _encode_identity(kind, identity)).digest()


def _items(
    kind: RecordKind,
    identities: Sequence[Identity],
    digests: Sequence[bytes] | None,
) -> tuple[tuple[Identity, bytes], ...]:
    canonical = tuple(sorted(set(identities), key=_identity_sort_key))
    if len(canonical) != len(tuple(identities)):
        raise CompactBoundsError("identity set contains duplicates")
    if digests is None:
        return tuple((identity, _identity_digest(kind, identity)) for identity in canonical)
    if len(digests) != len(identities):
        raise CompactBoundsError("record digest count does not match identities")
    mapping = dict(zip(identities, digests, strict=True))
    if any(not isinstance(digest, bytes) or len(digest) != 32 for digest in digests):
        raise CompactBoundsError("record digest has invalid size")
    return tuple((identity, mapping[identity]) for identity in canonical)


def _root_digest(kind: RecordKind, items: Sequence[tuple[Identity, bytes]]) -> bytes:
    body = bytearray()
    for identity, digest in sorted(items, key=lambda item: _identity_sort_key(item[0])):
        body += _encode_identity(kind, identity)
        body += digest
    return hashlib.sha256(bytes(body)).digest()


@dataclass(frozen=True, slots=True)
class SketchSummaryMessage:
    kind: RecordKind
    capacity: int
    cardinality: int
    root_digest: bytes
    cells: tuple[IBLTCell, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, RecordKind):
            raise TypeError("kind must be RecordKind")
        expected = _cell_count(self.capacity)
        if type(self.cardinality) is not int or not 0 <= self.cardinality <= MAX_COMPACT_IDENTITIES:
            raise CompactBoundsError("summary cardinality is outside bounds")
        if not isinstance(self.root_digest, bytes) or len(self.root_digest) != FULL_SET_DIGEST_BYTES:
            raise CompactBoundsError("root digest has invalid size")
        if not isinstance(self.cells, tuple) or len(self.cells) != expected:
            raise CompactBoundsError("summary cell count does not match capacity")
        if any(not isinstance(cell, IBLTCell) for cell in self.cells):
            raise TypeError("cells must contain IBLTCell values")


@dataclass(frozen=True, slots=True)
class FingerprintRequestMessage:
    kind: RecordKind
    fingerprints: tuple[int, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, RecordKind):
            raise TypeError("kind must be RecordKind")
        values = tuple(sorted(self.fingerprints))
        if not 1 <= len(values) <= MAX_COMPACT_CAPACITY:
            raise CompactBoundsError("fingerprint request count is outside bounds")
        if len(set(values)) != len(values) or any(
            type(value) is not int or not 0 <= value < 2**64 for value in values
        ):
            raise CompactBoundsError("fingerprint request is invalid")
        object.__setattr__(self, "fingerprints", values)


@dataclass(frozen=True, slots=True)
class RevealedIdentity:
    fingerprint: int
    identity: Identity
    record_digest: bytes

    def validate(self, kind: RecordKind) -> None:
        if self.fingerprint != _fingerprint(kind, self.identity, self.record_digest):
            raise CompactDecodeError("revealed identity fingerprint mismatch")
        if not isinstance(self.record_digest, bytes) or len(self.record_digest) != 32:
            raise CompactBoundsError("record digest has invalid size")


@dataclass(frozen=True, slots=True)
class IdentityRevealMessage:
    kind: RecordKind
    entries: tuple[RevealedIdentity, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, RecordKind):
            raise TypeError("kind must be RecordKind")
        if not 1 <= len(self.entries) <= MAX_COMPACT_REVEALS_PER_MESSAGE:
            raise CompactBoundsError("identity reveal count is outside bounds")
        for entry in self.entries:
            if not isinstance(entry, RevealedIdentity):
                raise TypeError("entries must contain RevealedIdentity values")
            entry.validate(self.kind)
        ordered = tuple(sorted(self.entries, key=lambda entry: entry.fingerprint))
        if len({entry.fingerprint for entry in ordered}) != len(ordered):
            raise CompactBoundsError("identity reveal contains ambiguous fingerprints")
        object.__setattr__(self, "entries", ordered)


CompactMessage = SketchSummaryMessage | FingerprintRequestMessage | IdentityRevealMessage


def compact_message_type(message: CompactMessage) -> CompactMessageType:
    if isinstance(message, SketchSummaryMessage):
        return CompactMessageType.SUMMARY
    if isinstance(message, FingerprintRequestMessage):
        return CompactMessageType.FINGERPRINT_REQUEST
    if isinstance(message, IdentityRevealMessage):
        return CompactMessageType.IDENTITY_REVEAL
    raise TypeError("unsupported compact message")


def encode_compact_message(message: CompactMessage) -> bytes:
    active_type = compact_message_type(message)
    body = bytearray()
    if isinstance(message, SketchSummaryMessage):
        body += _SUMMARY.pack(
            message.kind,
            message.capacity,
            len(message.cells),
            message.cardinality,
            message.root_digest,
        )
        for cell in message.cells:
            body += _CELL.pack(cell.count, cell.fingerprint_xor, cell.checksum_xor)
    elif isinstance(message, FingerprintRequestMessage):
        body += _REQUEST.pack(message.kind, len(message.fingerprints))
        for fingerprint in message.fingerprints:
            body += fingerprint.to_bytes(FINGERPRINT_BYTES, "big")
    else:
        body += _REVEAL.pack(message.kind, len(message.entries))
        for entry in message.entries:
            body += entry.fingerprint.to_bytes(FINGERPRINT_BYTES, "big")
            body += _encode_identity(message.kind, entry.identity)
            body += entry.record_digest
    raw = bytes(body)
    encoded = _HEADER.pack(
        B2C_MAGIC,
        B2C_VERSION,
        active_type,
        len(raw),
        hashlib.sha256(raw).digest(),
    ) + raw
    if len(encoded) > MAX_COMPACT_MESSAGE_BYTES:
        raise CompactBoundsError("compact message exceeds maximum")
    return encoded


def decode_compact_message(data: bytes) -> CompactMessage:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if len(data) > MAX_COMPACT_MESSAGE_BYTES or len(data) < _HEADER.size:
        raise CompactDecodeError("compact envelope size is invalid")
    magic, version, raw_type, body_length, digest = _HEADER.unpack_from(data)
    if magic != B2C_MAGIC:
        raise CompactDecodeError("invalid compact message magic")
    if version != B2C_VERSION:
        raise CompactDecodeError("unsupported compact message version")
    try:
        active_type = CompactMessageType(raw_type)
    except ValueError as error:
        raise CompactDecodeError("unknown compact message type") from error
    body = data[_HEADER.size :]
    if len(body) != body_length or hashlib.sha256(body).digest() != digest:
        raise CompactDecodeError("compact message integrity failure")
    reader = _Reader(body)
    try:
        if active_type is CompactMessageType.SUMMARY:
            raw_kind, capacity, cell_count, cardinality, root = reader.unpack(_SUMMARY)
            kind = RecordKind(raw_kind)
            cells = tuple(IBLTCell(*reader.unpack(_CELL)) for _ in range(cell_count))
            message: CompactMessage = SketchSummaryMessage(
                kind, capacity, cardinality, root, cells
            )
        elif active_type is CompactMessageType.FINGERPRINT_REQUEST:
            raw_kind, count = reader.unpack(_REQUEST)
            kind = RecordKind(raw_kind)
            message = FingerprintRequestMessage(
                kind,
                tuple(
                    int.from_bytes(reader.take(FINGERPRINT_BYTES), "big")
                    for _ in range(count)
                ),
            )
        else:
            raw_kind, count = reader.unpack(_REVEAL)
            kind = RecordKind(raw_kind)
            entries = tuple(
                RevealedIdentity(
                    int.from_bytes(reader.take(FINGERPRINT_BYTES), "big"),
                    _decode_identity(kind, reader),
                    reader.take(32),
                )
                for _ in range(count)
            )
            message = IdentityRevealMessage(kind, entries)
        reader.finish()
        return message
    except CompactDecodeError:
        raise
    except (B2BoundsError, IndexError, TypeError, ValueError) as error:
        raise CompactDecodeError("invalid compact message body") from error


def _build_cells(
    kind: RecordKind,
    items: Sequence[tuple[Identity, bytes]],
    capacity: int,
) -> tuple[IBLTCell, ...]:
    mutable = [[0, 0, 0] for _ in range(_cell_count(capacity))]
    for identity, digest in items:
        fingerprint = _fingerprint(kind, identity, digest)
        checksum = _checksum(fingerprint)
        for index in _indexes(fingerprint, len(mutable)):
            mutable[index][0] += 1
            mutable[index][1] ^= fingerprint
            mutable[index][2] ^= checksum
    return tuple(IBLTCell(*cell) for cell in mutable)


def build_summary(
    kind: RecordKind,
    identities: Sequence[Identity],
    capacity: int,
    record_digests: Sequence[bytes] | None = None,
) -> SketchSummaryMessage:
    items = _items(kind, identities, record_digests)
    if len(items) > MAX_COMPACT_IDENTITIES:
        raise CompactBoundsError("identity set exceeds native maximum")
    return SketchSummaryMessage(
        kind,
        capacity,
        len(items),
        _root_digest(kind, items),
        _build_cells(kind, items, capacity),
    )


@dataclass(frozen=True, slots=True)
class CompactDifference:
    status: CompactDecodeStatus
    source_only_fingerprints: tuple[int, ...]
    receiver_only_fingerprints: tuple[int, ...]
    decode_operations: int
    temporary_bytes: int

    @property
    def decode_success(self) -> bool:
        return self.status in (CompactDecodeStatus.EQUAL, CompactDecodeStatus.DECODED)


def decode_difference(
    summary: SketchSummaryMessage,
    receiver_identities: Sequence[Identity],
    receiver_record_digests: Sequence[bytes] | None = None,
) -> CompactDifference:
    receiver = _items(summary.kind, receiver_identities, receiver_record_digests)
    receiver_root = _root_digest(summary.kind, receiver)
    temporary = len(summary.cells) * _CELL.size
    if summary.cardinality == len(receiver) and summary.root_digest == receiver_root:
        return CompactDifference(CompactDecodeStatus.EQUAL, (), (), 0, temporary)
    cells = [[cell.count, cell.fingerprint_xor, cell.checksum_xor] for cell in summary.cells]
    for identity, digest in receiver:
        fingerprint = _fingerprint(summary.kind, identity, digest)
        checksum = _checksum(fingerprint)
        for index in _indexes(fingerprint, len(cells)):
            cells[index][0] -= 1
            cells[index][1] ^= fingerprint
            cells[index][2] ^= checksum
    positive: set[int] = set()
    negative: set[int] = set()
    operations = len(receiver) * IBLT_HASH_COUNT
    queue = list(range(len(cells)))
    while queue:
        index = queue.pop()
        count, fingerprint, checksum = cells[index]
        if abs(count) != 1 or checksum != _checksum(fingerprint):
            continue
        target = positive if count == 1 else negative
        if fingerprint in target:
            continue
        target.add(fingerprint)
        item_checksum = _checksum(fingerprint)
        for active in _indexes(fingerprint, len(cells)):
            cells[active][0] -= count
            cells[active][1] ^= fingerprint
            cells[active][2] ^= item_checksum
            queue.append(active)
            operations += 1
    if any(count or fingerprint or checksum for count, fingerprint, checksum in cells):
        return CompactDifference(
            CompactDecodeStatus.CAPACITY_EXCEEDED, (), (), operations, temporary
        )
    if not positive and not negative:
        return CompactDifference(
            CompactDecodeStatus.ROOT_MISMATCH, (), (), operations, temporary
        )
    return CompactDifference(
        CompactDecodeStatus.DECODED,
        tuple(sorted(positive)),
        tuple(sorted(negative)),
        operations,
        temporary,
    )


def _selected(keys: Sequence[bytes]) -> tuple[bytes, ...]:
    values = tuple(sorted(keys))
    if len(values) > MAX_CATALOG_ITEMS or len(set(values)) != len(values):
        raise CompactBoundsError("selected reference policy is invalid")
    if any(not isinstance(key, bytes) or not key or len(key) > MAX_LOGICAL_KEY_BYTES for key in values):
        raise CompactBoundsError("selected reference identity is outside bounds")
    return values


@dataclass(frozen=True, slots=True)
class CompactEndpointResult:
    outbound_messages: tuple[bytes, ...] = ()
    difference: CompactDifference | None = None
    durable_commits: int = 0
    already_known: int = 0


class CompactIndependentEndpoint:
    """B2C endpoint that reads only its own native state."""

    def __init__(self, catalog: BoundedReferenceCatalog, query_results: QueryResultStore) -> None:
        if not isinstance(catalog, BoundedReferenceCatalog) or not isinstance(query_results, QueryResultStore):
            raise TypeError("compact endpoint requires native catalog and query/result stores")
        self.__catalog = catalog
        self.__query_results = query_results
        self.__base = IndependentEndpoint(catalog, query_results)

    def local_identities(self, kind: RecordKind, selected_references: Sequence[bytes] = ()) -> tuple[Identity, ...]:
        if kind is RecordKind.REFERENCE:
            selected = _selected(selected_references)
            return tuple(key for key in selected if key in self.__catalog)
        values: list[Identity] = []
        offset = 0
        while True:
            page = (
                self.__query_results.sorted_query_ids(offset=offset)
                if kind is RecordKind.QUERY
                else self.__query_results.sorted_result_ids(offset=offset)
            )
            if not page:
                return tuple(values)
            values.extend(page)
            offset += len(page)

    def _record(self, kind: RecordKind, identity: Identity):
        if kind is RecordKind.QUERY:
            assert isinstance(identity, bytes)
            return self.__query_results.get_query(identity)
        if kind is RecordKind.RESULT:
            assert isinstance(identity, ResultIdentity)
            return self.__query_results.get_result(identity)
        assert isinstance(identity, bytes)
        return self.__catalog.get(identity)

    def _local_digests(
        self, kind: RecordKind, identities: Sequence[Identity]
    ) -> tuple[bytes, ...]:
        return tuple(record_digest(kind, self._record(kind, identity)) for identity in identities)

    def summary_message(self, kind: RecordKind, capacity: int, selected_references: Sequence[bytes] = ()) -> bytes:
        identities = self.local_identities(kind, selected_references)
        return encode_compact_message(
            build_summary(kind, identities, capacity, self._local_digests(kind, identities))
        )

    def receive_summary(self, encoded: bytes, selected_references: Sequence[bytes] = ()) -> CompactEndpointResult:
        message = decode_compact_message(encoded)
        if not isinstance(message, SketchSummaryMessage):
            raise CompactProtocolError("expected compact summary")
        identities = self.local_identities(message.kind, selected_references)
        difference = decode_difference(
            message, identities, self._local_digests(message.kind, identities)
        )
        outbound = ()
        if difference.status is CompactDecodeStatus.DECODED and difference.source_only_fingerprints:
            outbound = (
                encode_compact_message(
                    FingerprintRequestMessage(
                        message.kind, difference.source_only_fingerprints
                    )
                ),
            )
        return CompactEndpointResult(outbound, difference)

    def receive_fingerprint_request(self, encoded: bytes, selected_references: Sequence[bytes] = ()) -> CompactEndpointResult:
        message = decode_compact_message(encoded)
        if not isinstance(message, FingerprintRequestMessage):
            raise CompactProtocolError("expected fingerprint request")
        identities = self.local_identities(message.kind, selected_references)
        mapping: dict[int, list[Identity]] = {}
        for identity in identities:
            digest = record_digest(message.kind, self._record(message.kind, identity))
            mapping.setdefault(_fingerprint(message.kind, identity, digest), []).append(identity)
        entries: list[RevealedIdentity] = []
        for fingerprint in message.fingerprints:
            matches = mapping.get(fingerprint, [])
            if len(matches) != 1:
                raise CompactProtocolError("fingerprint is absent or ambiguous")
            identity = matches[0]
            entries.append(
                RevealedIdentity(
                    fingerprint,
                    identity,
                    record_digest(message.kind, self._record(message.kind, identity)),
                )
            )
        outbound = tuple(
            encode_compact_message(
                IdentityRevealMessage(
                    message.kind,
                    tuple(entries[start : start + MAX_COMPACT_REVEALS_PER_MESSAGE]),
                )
            )
            for start in range(0, len(entries), MAX_COMPACT_REVEALS_PER_MESSAGE)
        )
        return CompactEndpointResult(outbound)

    def receive_identity_reveal(self, encoded: bytes) -> CompactEndpointResult:
        message = decode_compact_message(encoded)
        if not isinstance(message, IdentityRevealMessage):
            raise CompactProtocolError("expected identity reveal")
        advertisement = AdvertisementMessage(
            message.kind,
            tuple(
                AdvertisedIdentity(entry.identity, entry.record_digest)
                for entry in message.entries
            ),
        )
        received = self.__base.receive_message(encode_message(advertisement))
        return CompactEndpointResult(
            received.outbound_messages,
            durable_commits=received.durable_commits,
            already_known=received.already_known,
        )

    def receive_b2(self, encoded: bytes) -> CompactEndpointResult:
        received = self.__base.receive_message(encoded)
        return CompactEndpointResult(
            received.outbound_messages,
            durable_commits=received.durable_commits,
            already_known=received.already_known,
        )


@dataclass(frozen=True, slots=True)
class CompactTraceEntry:
    attempt: int
    direction: LinkDirection
    message_type: str
    encoded_bytes: int
    action: ImpairmentAction


@dataclass(frozen=True, slots=True)
class CompactContactReport:
    outcome: CompactContactOutcome
    decode_status: CompactDecodeStatus | None
    control_messages: int
    control_bytes: int
    record_messages: int
    record_bytes: int
    bearer_attempts: int
    drops: int
    duplicates: int
    disconnects: int
    sender_uncertainties: int
    durable_commits: int
    exact_identities_disclosed: int
    full_digests_disclosed: int
    short_fingerprints_disclosed: int
    sketch_cells_disclosed: int
    temporary_bytes: int
    decode_operations: int
    fallback_required: bool
    error_code: str | None
    trace: tuple[CompactTraceEntry, ...]
    accounting_model: str = EXPERIMENTAL_B2C_ACCOUNTING_ONLY


_NATIVE_ERRORS = (
    CatalogBoundsError,
    PersistenceError,
    QueryConflictError,
    QueryResultBoundsError,
    ReferenceConflictError,
    ResultConflictError,
)


def run_compact_contact(
    source: CompactIndependentEndpoint,
    receiver: CompactIndependentEndpoint,
    *,
    kind: RecordKind,
    capacity: int,
    bearer: EncodedMessageBearer,
    selected_references: Sequence[bytes] = (),
    max_attempts: int = MAX_COMPACT_ATTEMPTS,
) -> CompactContactReport:
    """One bounded directional compact attempt; fallback is caller-controlled."""

    if not isinstance(source, CompactIndependentEndpoint) or not isinstance(receiver, CompactIndependentEndpoint):
        raise TypeError("source and receiver must be CompactIndependentEndpoint")
    if not isinstance(bearer, EncodedMessageBearer):
        raise TypeError("bearer must implement EncodedMessageBearer")
    if type(max_attempts) is not int or not 1 <= max_attempts <= MAX_COMPACT_ATTEMPTS:
        raise CompactBoundsError("max_attempts is outside bounds")
    selected = _selected(selected_references)
    queue: list[tuple[CompactIndependentEndpoint, CompactIndependentEndpoint, LinkDirection, bytes]] = [
        (
            source,
            receiver,
            LinkDirection.LEFT_TO_RIGHT,
            source.summary_message(kind, capacity, selected),
        )
    ]
    counters = {name: 0 for name in (
        "control_messages", "control_bytes", "record_messages", "record_bytes",
        "attempts", "drops", "duplicates", "disconnects", "uncertainties",
        "commits", "identities", "digests", "fingerprints", "cells",
    )}
    trace: list[CompactTraceEntry] = []
    status: CompactDecodeStatus | None = None
    temporary = 0
    operations = 0
    outcome: CompactContactOutcome | None = None
    failure: Exception | None = None

    while queue and outcome is None:
        sender, target, direction, encoded = queue.pop(0)
        if counters["attempts"] >= max_attempts:
            outcome = CompactContactOutcome.BUDGET_EXHAUSTED
            break
        try:
            if encoded[:4] == B2C_MAGIC:
                message = decode_compact_message(encoded)
                label = compact_message_type(message).name
                is_record = False
                if isinstance(message, SketchSummaryMessage):
                    counters["cells"] += len(message.cells)
                    counters["digests"] += 1
                elif isinstance(message, FingerprintRequestMessage):
                    counters["fingerprints"] += len(message.fingerprints)
                else:
                    counters["fingerprints"] += len(message.entries)
                    counters["identities"] += len(message.entries)
                    counters["digests"] += len(message.entries)
            else:
                message = decode_message(encoded)
                label = f"B2_{message_type(message).name}"
                is_record = isinstance(message, RecordMessage)
                if isinstance(message, RequestMessage):
                    counters["identities"] += len(message.identities)
        except (B2DecodeError, CompactDecodeError) as error:
            failure = error
            outcome = CompactContactOutcome.ERROR
            break
        prefix = "record" if is_record else "control"
        counters[f"{prefix}_messages"] += 1
        counters[f"{prefix}_bytes"] += len(encoded)
        counters["attempts"] += 1
        try:
            attempt = bearer.attempt(direction, encoded)
        except Exception as error:
            failure = error
            outcome = CompactContactOutcome.ERROR
            break
        if not isinstance(attempt, EncodedBearerAttemptResult):
            failure = CompactProtocolError("bearer returned invalid result")
            outcome = CompactContactOutcome.ERROR
            break
        trace.append(CompactTraceEntry(counters["attempts"], direction, label, len(encoded), attempt.action))
        if attempt.disconnected:
            counters["disconnects"] += 1
            outcome = CompactContactOutcome.DISCONNECTED
            break
        if not attempt.presentations:
            counters["drops"] += 1
            continue
        responses: list[bytes] = []
        for delivered in attempt.presentations:
            try:
                if delivered[:4] == B2C_MAGIC:
                    delivered_message = decode_compact_message(delivered)
                    if isinstance(delivered_message, SketchSummaryMessage):
                        received = target.receive_summary(delivered, selected)
                        assert received.difference is not None
                        status = received.difference.status
                        temporary = max(temporary, received.difference.temporary_bytes)
                        operations += received.difference.decode_operations
                        if not received.difference.decode_success:
                            outcome = CompactContactOutcome.FALLBACK_REQUIRED
                            break
                    elif isinstance(delivered_message, FingerprintRequestMessage):
                        received = target.receive_fingerprint_request(delivered, selected)
                    else:
                        received = target.receive_identity_reveal(delivered)
                else:
                    received = target.receive_b2(delivered)
                counters["commits"] += received.durable_commits
                responses.extend(received.outbound_messages)
            except (CompactDecodeError, CompactProtocolError, B2DecodeError, B2BoundsError, *_NATIVE_ERRORS) as error:
                failure = error
                outcome = CompactContactOutcome.ERROR
                break
        counters["duplicates"] += max(0, len(attempt.presentations) - 1)
        if outcome is not None:
            break
        if not attempt.sender_observed:
            counters["uncertainties"] += 1
            outcome = CompactContactOutcome.SENDER_UNCERTAIN
            break
        reverse = LinkDirection.RIGHT_TO_LEFT if direction is LinkDirection.LEFT_TO_RIGHT else LinkDirection.LEFT_TO_RIGHT
        queue[0:0] = [(target, sender, reverse, response) for response in responses]

    if outcome is None:
        if counters["drops"]:
            outcome = CompactContactOutcome.PARTIAL_NOT_DELIVERED
        elif status is CompactDecodeStatus.EQUAL:
            outcome = CompactContactOutcome.EQUAL
        else:
            outcome = CompactContactOutcome.DISCOVERED
    return CompactContactReport(
        outcome,
        status,
        counters["control_messages"],
        counters["control_bytes"],
        counters["record_messages"],
        counters["record_bytes"],
        counters["attempts"],
        counters["drops"],
        counters["duplicates"],
        counters["disconnects"],
        counters["uncertainties"],
        counters["commits"],
        counters["identities"],
        counters["digests"],
        counters["fingerprints"],
        counters["cells"],
        temporary,
        operations,
        outcome is CompactContactOutcome.FALLBACK_REQUIRED,
        None if failure is None else type(failure).__name__.upper(),
        tuple(trace),
    )


__all__ = [
    "B2C_MAGIC", "B2C_VERSION", "CHECKSUM_BYTES", "CompactBoundsError",
    "CompactContactOutcome", "CompactContactReport", "CompactDecodeError",
    "CompactDecodeStatus", "CompactDifference", "CompactIndependentEndpoint",
    "CompactMessageType", "CompactProtocolError", "EXPERIMENTAL_B2C_ENCODING",
    "FINGERPRINT_BYTES", "FingerprintRequestMessage", "IBLTCell",
    "IdentityRevealMessage", "MAX_COMPACT_CAPACITY", "MAX_COMPACT_MESSAGE_BYTES",
    "MAX_COMPACT_REVEALS_PER_MESSAGE", "MAX_COMPACT_ROUNDS", "RevealedIdentity",
    "SketchSummaryMessage", "build_summary", "compact_message_type",
    "decode_compact_message", "decode_difference", "encode_compact_message",
    "run_compact_contact",
]
