from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
import hashlib
import struct
from typing import Iterator, Protocol, Sequence, runtime_checkable

from .bearer import (
    ImpairmentAction,
    LinkDirection,
    MAX_PRESENTATIONS_PER_ATTEMPT,
    ScriptedImpairmentPlan,
)
from .catalog import (
    MAX_EXCHANGE_ITEMS,
    MAX_LOGICAL_KEY_BYTES,
    MAX_REFERENCE_BYTES,
    BoundedReference,
    BoundedReferenceCatalog,
    CatalogBoundsError,
    MutationResult,
    ReferenceConflictError,
)
from .contact import MAX_CONTACT_BYTES, MAX_CONTACT_ITEMS
from .local_persistence import PersistenceError
from .query import (
    MAX_QUERY_EXCHANGE_ITEMS,
    MAX_QUERY_ID_BYTES,
    MAX_QUERY_PAYLOAD_BYTES,
    MAX_RESULT_ID_BYTES,
    MAX_RESULT_KEYS,
    QueryConflictError,
    QueryMutationResult,
    QueryRecord,
    QueryResultBoundsError,
    QueryResultStore,
    ResultConflictError,
    ResultIdentity,
    ResultRecord,
)


EXPERIMENTAL_B2_ENCODING = "pollicino.experimental-b2.v1"
EXPERIMENTAL_B2_ACCOUNTING_ONLY = "EXPERIMENTAL_B2_ACCOUNTING_ONLY"
B2_MAGIC = b"PB2E"
B2_VERSION = 1
B2_DIGEST_BYTES = 32

_MESSAGE_HEADER = struct.Struct(">4sBBI32s")
_COUNT = struct.Struct(">H")
_ONE_LENGTH = struct.Struct(">H")
_TWO_LENGTHS = struct.Struct(">HH")
_QUERY_RECORD_HEADER = struct.Struct(">HI")
_RESULT_RECORD_HEADER = struct.Struct(">HHH")
_REFERENCE_RECORD_HEADER = struct.Struct(">HI")

MAX_B2_IDENTITIES_PER_MESSAGE = min(MAX_EXCHANGE_ITEMS, MAX_QUERY_EXCHANGE_ITEMS)
MAX_QUERY_IDENTITY_ENCODED_BYTES = 2 + MAX_QUERY_ID_BYTES
MAX_RESULT_IDENTITY_ENCODED_BYTES = 4 + MAX_QUERY_ID_BYTES + MAX_RESULT_ID_BYTES
MAX_REFERENCE_IDENTITY_ENCODED_BYTES = 2 + MAX_LOGICAL_KEY_BYTES
MAX_ADVERTISED_IDENTITY_BYTES = max(
    MAX_QUERY_IDENTITY_ENCODED_BYTES,
    MAX_RESULT_IDENTITY_ENCODED_BYTES,
    MAX_REFERENCE_IDENTITY_ENCODED_BYTES,
) + B2_DIGEST_BYTES
MAX_ADVERTISEMENT_BODY_BYTES = (
    1 + _COUNT.size + MAX_B2_IDENTITIES_PER_MESSAGE * MAX_ADVERTISED_IDENTITY_BYTES
)
MAX_REQUEST_BODY_BYTES = 1 + _COUNT.size + MAX_B2_IDENTITIES_PER_MESSAGE * max(
    MAX_QUERY_IDENTITY_ENCODED_BYTES,
    MAX_RESULT_IDENTITY_ENCODED_BYTES,
    MAX_REFERENCE_IDENTITY_ENCODED_BYTES,
)
MAX_SELECTION_BODY_BYTES = (
    _COUNT.size
    + MAX_B2_IDENTITIES_PER_MESSAGE * MAX_REFERENCE_IDENTITY_ENCODED_BYTES
)
MAX_QUERY_RECORD_BODY_BYTES = (
    1 + _QUERY_RECORD_HEADER.size + MAX_QUERY_ID_BYTES + MAX_QUERY_PAYLOAD_BYTES
)
MAX_RESULT_RECORD_BODY_BYTES = (
    1
    + _RESULT_RECORD_HEADER.size
    + MAX_QUERY_ID_BYTES
    + MAX_RESULT_ID_BYTES
    + MAX_RESULT_KEYS * (2 + MAX_LOGICAL_KEY_BYTES)
)
MAX_REFERENCE_RECORD_BODY_BYTES = (
    1 + _REFERENCE_RECORD_HEADER.size + MAX_LOGICAL_KEY_BYTES + MAX_REFERENCE_BYTES
)
MAX_B2_RECORD_BODY_BYTES = max(
    MAX_QUERY_RECORD_BODY_BYTES,
    MAX_RESULT_RECORD_BODY_BYTES,
    MAX_REFERENCE_RECORD_BODY_BYTES,
)
MAX_B2_MESSAGE_BYTES = _MESSAGE_HEADER.size + max(
    MAX_ADVERTISEMENT_BODY_BYTES,
    MAX_REQUEST_BODY_BYTES,
    MAX_SELECTION_BODY_BYTES,
    MAX_B2_RECORD_BODY_BYTES,
)
MAX_B2_CONTROL_MESSAGES = MAX_CONTACT_ITEMS
MAX_B2_RECORD_MESSAGES = MAX_CONTACT_ITEMS
MAX_B2_BEARER_ATTEMPTS = MAX_CONTACT_ITEMS
MAX_B2_TRACE_ENTRIES = MAX_B2_BEARER_ATTEMPTS
MAX_B2_OUTBOUND_MESSAGES = MAX_B2_IDENTITIES_PER_MESSAGE
MAX_B2_CONTROL_BYTES = MAX_B2_CONTROL_MESSAGES * MAX_B2_MESSAGE_BYTES
MAX_B2_RECORD_BYTES = MAX_B2_RECORD_MESSAGES * MAX_B2_MESSAGE_BYTES


class B2BoundsError(ValueError):
    pass


class B2DecodeError(ValueError):
    pass


class B2ProtocolError(RuntimeError):
    pass


class B2MessageType(IntEnum):
    ADVERTISEMENT = 1
    REQUEST = 2
    RECORD = 3
    REFERENCE_SELECTION = 4


class RecordKind(IntEnum):
    QUERY = 1
    RESULT = 2
    REFERENCE = 3


Identity = bytes | ResultIdentity
RecordValue = QueryRecord | ResultRecord | BoundedReference


def _identity_sort_key(identity: Identity) -> tuple[bytes, bytes]:
    if isinstance(identity, ResultIdentity):
        return identity.query_id, identity.result_id
    return identity, b""


def _validate_identity(kind: RecordKind, identity: Identity) -> None:
    if kind is RecordKind.RESULT:
        if not isinstance(identity, ResultIdentity):
            raise TypeError("result identity must be ResultIdentity")
        return
    if not isinstance(identity, bytes):
        raise TypeError("query/reference identity must be bytes")
    maximum = (
        MAX_QUERY_ID_BYTES if kind is RecordKind.QUERY else MAX_LOGICAL_KEY_BYTES
    )
    if not identity:
        raise B2BoundsError("identity must not be empty")
    if len(identity) > maximum:
        raise B2BoundsError(f"identity exceeds {maximum} bytes")


def _canonical_identities(
    kind: RecordKind,
    identities: Sequence[Identity],
) -> tuple[Identity, ...]:
    if not isinstance(identities, (tuple, list)):
        raise TypeError("identities must be a tuple or list")
    values = tuple(identities)
    if len(values) > MAX_B2_IDENTITIES_PER_MESSAGE:
        raise B2BoundsError("identity page exceeds exchange bound")
    for identity in values:
        _validate_identity(kind, identity)
    if len(set(values)) != len(values):
        raise ValueError("identity page contains duplicates")
    return tuple(sorted(values, key=_identity_sort_key))


@dataclass(frozen=True, slots=True)
class AdvertisedIdentity:
    identity: Identity
    record_digest: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.record_digest, bytes):
            raise TypeError("record_digest must be bytes")
        if len(self.record_digest) != B2_DIGEST_BYTES:
            raise B2BoundsError(f"record_digest must be {B2_DIGEST_BYTES} bytes")


@dataclass(frozen=True, slots=True)
class AdvertisementMessage:
    kind: RecordKind
    entries: tuple[AdvertisedIdentity, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, RecordKind):
            raise TypeError("kind must be RecordKind")
        if not isinstance(self.entries, tuple):
            raise TypeError("entries must be a tuple")
        if not self.entries:
            raise B2BoundsError("advertisement must not be empty")
        if any(not isinstance(entry, AdvertisedIdentity) for entry in self.entries):
            raise TypeError("entries must contain AdvertisedIdentity values")
        identities = _canonical_identities(
            self.kind, tuple(entry.identity for entry in self.entries)
        )
        by_identity = {entry.identity: entry for entry in self.entries}
        if len(by_identity) != len(self.entries):
            raise ValueError("advertisement contains duplicate identities")
        ordered = tuple(by_identity[identity] for identity in identities)
        object.__setattr__(self, "entries", ordered)


@dataclass(frozen=True, slots=True)
class RequestMessage:
    kind: RecordKind
    identities: tuple[Identity, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, RecordKind):
            raise TypeError("kind must be RecordKind")
        canonical = _canonical_identities(self.kind, self.identities)
        if not canonical:
            raise B2BoundsError("request must not be empty")
        object.__setattr__(self, "identities", canonical)


@dataclass(frozen=True, slots=True)
class RecordMessage:
    kind: RecordKind
    record: RecordValue

    def __post_init__(self) -> None:
        if not isinstance(self.kind, RecordKind):
            raise TypeError("kind must be RecordKind")
        expected = {
            RecordKind.QUERY: QueryRecord,
            RecordKind.RESULT: ResultRecord,
            RecordKind.REFERENCE: BoundedReference,
        }
        if not isinstance(self.record, expected[self.kind]):
            raise TypeError("record type does not match kind")


@dataclass(frozen=True, slots=True)
class ReferenceSelectionMessage:
    logical_keys: tuple[bytes, ...]

    def __post_init__(self) -> None:
        canonical = _canonical_identities(RecordKind.REFERENCE, self.logical_keys)
        if not canonical:
            raise B2BoundsError("reference selection must not be empty")
        object.__setattr__(self, "logical_keys", canonical)


B2Message = (
    AdvertisementMessage | RequestMessage | RecordMessage | ReferenceSelectionMessage
)


class _Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.offset = 0

    def take(self, size: int) -> bytes:
        if type(size) is not int or size < 0:
            raise B2DecodeError("invalid read size")
        end = self.offset + size
        if end > len(self.data):
            raise B2DecodeError("message body is truncated")
        value = self.data[self.offset:end]
        self.offset = end
        return value

    def unpack(self, structure: struct.Struct) -> tuple[int, ...]:
        return structure.unpack(self.take(structure.size))

    def finish(self) -> None:
        if self.offset != len(self.data):
            raise B2DecodeError("message body contains trailing bytes")


def _encode_identity(kind: RecordKind, identity: Identity) -> bytes:
    _validate_identity(kind, identity)
    if kind is RecordKind.RESULT:
        assert isinstance(identity, ResultIdentity)
        return (
            _TWO_LENGTHS.pack(len(identity.query_id), len(identity.result_id))
            + identity.query_id
            + identity.result_id
        )
    assert isinstance(identity, bytes)
    return _ONE_LENGTH.pack(len(identity)) + identity


def _decode_identity(kind: RecordKind, reader: _Reader) -> Identity:
    if kind is RecordKind.RESULT:
        query_length, result_length = reader.unpack(_TWO_LENGTHS)
        return ResultIdentity(reader.take(query_length), reader.take(result_length))
    (length,) = reader.unpack(_ONE_LENGTH)
    identity = reader.take(length)
    _validate_identity(kind, identity)
    return identity


def _record_payload(kind: RecordKind, record: RecordValue) -> bytes:
    RecordMessage(kind, record)
    if kind is RecordKind.QUERY:
        assert isinstance(record, QueryRecord)
        return (
            _QUERY_RECORD_HEADER.pack(len(record.query_id), len(record.opaque_query))
            + record.query_id
            + record.opaque_query
        )
    if kind is RecordKind.RESULT:
        assert isinstance(record, ResultRecord)
        body = bytearray(
            _RESULT_RECORD_HEADER.pack(
                len(record.query_id),
                len(record.result_id),
                len(record.candidate_keys),
            )
        )
        body += record.query_id + record.result_id
        for key in record.candidate_keys:
            body += _ONE_LENGTH.pack(len(key)) + key
        return bytes(body)
    assert isinstance(record, BoundedReference)
    return (
        _REFERENCE_RECORD_HEADER.pack(
            len(record.logical_key), len(record.opaque_reference)
        )
        + record.logical_key
        + record.opaque_reference
    )


def _decode_record(kind: RecordKind, reader: _Reader) -> RecordValue:
    if kind is RecordKind.QUERY:
        query_length, opaque_length = reader.unpack(_QUERY_RECORD_HEADER)
        return QueryRecord(reader.take(query_length), reader.take(opaque_length))
    if kind is RecordKind.RESULT:
        query_length, result_length, key_count = reader.unpack(_RESULT_RECORD_HEADER)
        if key_count > MAX_RESULT_KEYS:
            raise B2DecodeError("result candidate count exceeds bound")
        query_id = reader.take(query_length)
        result_id = reader.take(result_length)
        keys = []
        for _ in range(key_count):
            (key_length,) = reader.unpack(_ONE_LENGTH)
            keys.append(reader.take(key_length))
        return ResultRecord(query_id, result_id, tuple(keys))
    key_length, reference_length = reader.unpack(_REFERENCE_RECORD_HEADER)
    return BoundedReference(reader.take(key_length), reader.take(reference_length))


def record_digest(kind: RecordKind, record: RecordValue) -> bytes:
    return hashlib.sha256(_record_payload(kind, record)).digest()


def message_type(message: B2Message) -> B2MessageType:
    if isinstance(message, AdvertisementMessage):
        return B2MessageType.ADVERTISEMENT
    if isinstance(message, RequestMessage):
        return B2MessageType.REQUEST
    if isinstance(message, RecordMessage):
        return B2MessageType.RECORD
    if isinstance(message, ReferenceSelectionMessage):
        return B2MessageType.REFERENCE_SELECTION
    raise TypeError("unsupported B2 message")


def encode_message(message: B2Message) -> bytes:
    active_type = message_type(message)
    body = bytearray()
    if isinstance(message, AdvertisementMessage):
        body += bytes((message.kind,)) + _COUNT.pack(len(message.entries))
        for entry in message.entries:
            body += _encode_identity(message.kind, entry.identity)
            body += entry.record_digest
    elif isinstance(message, RequestMessage):
        body += bytes((message.kind,)) + _COUNT.pack(len(message.identities))
        for identity in message.identities:
            body += _encode_identity(message.kind, identity)
    elif isinstance(message, RecordMessage):
        body += bytes((message.kind,)) + _record_payload(message.kind, message.record)
    else:
        assert isinstance(message, ReferenceSelectionMessage)
        body += _COUNT.pack(len(message.logical_keys))
        for logical_key in message.logical_keys:
            body += _encode_identity(RecordKind.REFERENCE, logical_key)
    body_bytes = bytes(body)
    encoded = _MESSAGE_HEADER.pack(
        B2_MAGIC,
        B2_VERSION,
        active_type,
        len(body_bytes),
        hashlib.sha256(body_bytes).digest(),
    ) + body_bytes
    if len(encoded) > MAX_B2_MESSAGE_BYTES:
        raise B2BoundsError("encoded B2 message exceeds maximum")
    return encoded


def _kind(reader: _Reader) -> RecordKind:
    try:
        return RecordKind(reader.take(1)[0])
    except ValueError as error:
        raise B2DecodeError("unknown record kind") from error


def decode_message(data: bytes) -> B2Message:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if len(data) > MAX_B2_MESSAGE_BYTES:
        raise B2DecodeError("encoded B2 message exceeds maximum")
    if len(data) < _MESSAGE_HEADER.size:
        raise B2DecodeError("message header is truncated")
    magic, version, raw_type, body_length, digest = _MESSAGE_HEADER.unpack_from(data)
    if magic != B2_MAGIC:
        raise B2DecodeError("invalid B2 message magic")
    if version != B2_VERSION:
        raise B2DecodeError(f"unsupported B2 message version: {version}")
    try:
        active_type = B2MessageType(raw_type)
    except ValueError as error:
        raise B2DecodeError("unknown B2 message type") from error
    body = data[_MESSAGE_HEADER.size :]
    if len(body) != body_length:
        raise B2DecodeError("B2 message length mismatch")
    if hashlib.sha256(body).digest() != digest:
        raise B2DecodeError("B2 message integrity mismatch")
    reader = _Reader(body)
    try:
        if active_type is B2MessageType.ADVERTISEMENT:
            kind = _kind(reader)
            (count,) = reader.unpack(_COUNT)
            if not 1 <= count <= MAX_B2_IDENTITIES_PER_MESSAGE:
                raise B2DecodeError("advertisement count is outside bounds")
            entries = tuple(
                AdvertisedIdentity(
                    _decode_identity(kind, reader), reader.take(B2_DIGEST_BYTES)
                )
                for _ in range(count)
            )
            message: B2Message = AdvertisementMessage(kind, entries)
        elif active_type is B2MessageType.REQUEST:
            kind = _kind(reader)
            (count,) = reader.unpack(_COUNT)
            if not 1 <= count <= MAX_B2_IDENTITIES_PER_MESSAGE:
                raise B2DecodeError("request count is outside bounds")
            message = RequestMessage(
                kind, tuple(_decode_identity(kind, reader) for _ in range(count))
            )
        elif active_type is B2MessageType.RECORD:
            kind = _kind(reader)
            message = RecordMessage(kind, _decode_record(kind, reader))
        else:
            (count,) = reader.unpack(_COUNT)
            if not 1 <= count <= MAX_B2_IDENTITIES_PER_MESSAGE:
                raise B2DecodeError("reference selection count is outside bounds")
            message = ReferenceSelectionMessage(
                tuple(
                    _decode_identity(RecordKind.REFERENCE, reader)
                    for _ in range(count)
                )
            )
        reader.finish()
        return message
    except B2DecodeError:
        raise
    except (IndexError, TypeError, ValueError) as error:
        raise B2DecodeError("invalid B2 message body") from error


def _message_record_logical_bytes(message: B2Message) -> int:
    if not isinstance(message, RecordMessage):
        return 0
    record = message.record
    if isinstance(record, QueryRecord):
        return 6 + record.payload_bytes
    if isinstance(record, ResultRecord):
        return 6 + len(record.query_id) + len(record.result_id) + sum(
            2 + len(key) for key in record.candidate_keys
        )
    return 6 + record.payload_bytes


def _record_identity(kind: RecordKind, record: RecordValue) -> Identity:
    if kind is RecordKind.QUERY:
        assert isinstance(record, QueryRecord)
        return record.query_id
    if kind is RecordKind.RESULT:
        assert isinstance(record, ResultRecord)
        return record.identity
    assert isinstance(record, BoundedReference)
    return record.logical_key


@dataclass(frozen=True, slots=True)
class EndpointReceiveResult:
    outbound_messages: tuple[bytes, ...] = ()
    durable_commits: int = 0
    already_known: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.outbound_messages, tuple):
            raise TypeError("outbound_messages must be a tuple")
        if len(self.outbound_messages) > MAX_B2_OUTBOUND_MESSAGES:
            raise B2BoundsError("endpoint response exceeds outbound-message bound")
        if any(not isinstance(value, bytes) for value in self.outbound_messages):
            raise TypeError("outbound messages must be bytes")
        if type(self.durable_commits) is not int or self.durable_commits < 0:
            raise ValueError("durable_commits must be a non-negative integer")
        if type(self.already_known) is not int or self.already_known < 0:
            raise ValueError("already_known must be a non-negative integer")


class IndependentEndpoint:
    """A B2 endpoint whose reconciliation methods inspect only local state."""

    def __init__(
        self,
        catalog: BoundedReferenceCatalog,
        query_results: QueryResultStore,
        diagnostic_label: str | None = None,
    ) -> None:
        if not isinstance(catalog, BoundedReferenceCatalog):
            raise TypeError("catalog must be BoundedReferenceCatalog")
        if not isinstance(query_results, QueryResultStore):
            raise TypeError("query_results must be QueryResultStore")
        if diagnostic_label is not None and not isinstance(diagnostic_label, str):
            raise TypeError("diagnostic_label must be str or None")
        self.__catalog = catalog
        self.__query_results = query_results
        self.diagnostic_label = diagnostic_label

    def _local_ids(self, kind: RecordKind, offset: int) -> tuple[Identity, ...]:
        if kind is RecordKind.QUERY:
            return self.__query_results.sorted_query_ids(offset=offset)
        if kind is RecordKind.RESULT:
            return self.__query_results.sorted_result_ids(offset=offset)
        raise B2ProtocolError("reference advertisements require explicit selection")

    def _local_record(self, kind: RecordKind, identity: Identity) -> RecordValue:
        if kind is RecordKind.QUERY:
            assert isinstance(identity, bytes)
            return self.__query_results.get_query(identity)
        if kind is RecordKind.RESULT:
            assert isinstance(identity, ResultIdentity)
            return self.__query_results.get_result(identity)
        assert isinstance(identity, bytes)
        return self.__catalog.get(identity)

    def advertisement_messages(self, kind: RecordKind) -> Iterator[bytes]:
        if kind not in (RecordKind.QUERY, RecordKind.RESULT):
            raise B2ProtocolError("only query/result state is automatically advertised")
        offset = 0
        while True:
            identities = self._local_ids(kind, offset)
            if not identities:
                return
            entries = tuple(
                AdvertisedIdentity(
                    identity,
                    record_digest(kind, self._local_record(kind, identity)),
                )
                for identity in identities
            )
            yield encode_message(AdvertisementMessage(kind, entries))
            offset += len(identities)

    def reference_selection_message(
        self, selected_keys: Sequence[bytes]
    ) -> bytes | None:
        selected = _canonical_identities(RecordKind.REFERENCE, selected_keys)
        if not selected:
            return None
        return encode_message(ReferenceSelectionMessage(selected))

    def _receive_advertisement(
        self, message: AdvertisementMessage
    ) -> EndpointReceiveResult:
        missing: list[Identity] = []
        known = 0
        for entry in message.entries:
            try:
                local_record = self._local_record(message.kind, entry.identity)
            except LookupError:
                missing.append(entry.identity)
                continue
            if record_digest(message.kind, local_record) != entry.record_digest:
                if message.kind is RecordKind.QUERY:
                    assert isinstance(entry.identity, bytes)
                    raise QueryConflictError(entry.identity)
                if message.kind is RecordKind.RESULT:
                    assert isinstance(entry.identity, ResultIdentity)
                    raise ResultConflictError(
                        entry.identity.query_id, entry.identity.result_id
                    )
                assert isinstance(entry.identity, bytes)
                raise ReferenceConflictError(entry.identity)
            known += 1
        outbound = (
            (encode_message(RequestMessage(message.kind, tuple(missing))),)
            if missing
            else ()
        )
        return EndpointReceiveResult(outbound, already_known=known)

    def _receive_request(self, message: RequestMessage) -> EndpointReceiveResult:
        records = tuple(
            encode_message(
                RecordMessage(message.kind, self._local_record(message.kind, identity))
            )
            for identity in message.identities
        )
        return EndpointReceiveResult(records)

    def _receive_selection(
        self, message: ReferenceSelectionMessage
    ) -> EndpointReceiveResult:
        entries = tuple(
            AdvertisedIdentity(
                logical_key,
                record_digest(
                    RecordKind.REFERENCE,
                    self._local_record(RecordKind.REFERENCE, logical_key),
                ),
            )
            for logical_key in message.logical_keys
        )
        return EndpointReceiveResult(
            (encode_message(AdvertisementMessage(RecordKind.REFERENCE, entries)),)
        )

    def _receive_record(self, message: RecordMessage) -> EndpointReceiveResult:
        if message.kind is RecordKind.QUERY:
            assert isinstance(message.record, QueryRecord)
            mutation = self.__query_results.add_query(message.record)
        elif message.kind is RecordKind.RESULT:
            assert isinstance(message.record, ResultRecord)
            mutation = self.__query_results.add_result(message.record)
        else:
            assert isinstance(message.record, BoundedReference)
            mutation = self.__catalog.add(message.record)
        added = mutation in (MutationResult.ADDED, QueryMutationResult.ADDED)
        return EndpointReceiveResult(
            durable_commits=int(added), already_known=int(not added)
        )

    def receive_message(self, encoded: bytes) -> EndpointReceiveResult:
        message = decode_message(encoded)
        if isinstance(message, AdvertisementMessage):
            return self._receive_advertisement(message)
        if isinstance(message, RequestMessage):
            return self._receive_request(message)
        if isinstance(message, RecordMessage):
            return self._receive_record(message)
        return self._receive_selection(message)


@dataclass(frozen=True, slots=True)
class EncodedBearerAttemptResult:
    action: ImpairmentAction
    presentations: tuple[bytes, ...]
    sender_observed: bool
    disconnected: bool = False
    delayed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.action, ImpairmentAction):
            raise TypeError("action must be ImpairmentAction")
        if not isinstance(self.presentations, tuple):
            raise TypeError("presentations must be a tuple")
        if len(self.presentations) > MAX_PRESENTATIONS_PER_ATTEMPT:
            raise B2BoundsError("too many presentations in one attempt")
        if any(not isinstance(value, bytes) for value in self.presentations):
            raise TypeError("presentations must contain bytes")
        if type(self.sender_observed) is not bool:
            raise TypeError("sender_observed must be bool")
        if type(self.disconnected) is not bool or type(self.delayed) is not bool:
            raise TypeError("disconnected and delayed must be bool")


@runtime_checkable
class EncodedMessageBearer(Protocol):
    def attempt(
        self, direction: LinkDirection, encoded: bytes
    ) -> EncodedBearerAttemptResult:
        ...


class ScriptedEncodedMessageLink:
    """Ephemeral deterministic complete-message adapter over PX9 actions."""

    def __init__(self, plan: ScriptedImpairmentPlan = ScriptedImpairmentPlan()) -> None:
        if not isinstance(plan, ScriptedImpairmentPlan):
            raise TypeError("plan must be ScriptedImpairmentPlan")
        self._plan = plan
        self._left_index = 0
        self._right_index = 0
        self._disconnected = False
        self._pending: bytes | None = None
        self._queued_peak = 0

    @property
    def queued_units_peak(self) -> int:
        return self._queued_peak

    def _next_action(self, direction: LinkDirection) -> ImpairmentAction:
        if direction is LinkDirection.LEFT_TO_RIGHT:
            index = self._left_index
            self._left_index += 1
            return (
                self._plan.left_to_right[index]
                if index < len(self._plan.left_to_right)
                else self._plan.default_left_to_right
            )
        index = self._right_index
        self._right_index += 1
        return (
            self._plan.right_to_left[index]
            if index < len(self._plan.right_to_left)
            else self._plan.default_right_to_left
        )

    def attempt(
        self, direction: LinkDirection, encoded: bytes
    ) -> EncodedBearerAttemptResult:
        if not isinstance(direction, LinkDirection):
            raise TypeError("direction must be LinkDirection")
        if not isinstance(encoded, bytes):
            raise TypeError("encoded must be bytes")
        if len(encoded) > MAX_B2_MESSAGE_BYTES:
            raise B2BoundsError("bearer unit exceeds B2 message bound")
        if self._disconnected:
            raise B2ProtocolError("message link is already disconnected")
        action = self._next_action(direction)
        if action is ImpairmentAction.DROP:
            return EncodedBearerAttemptResult(action, (), True)
        if action is ImpairmentAction.DISCONNECT:
            self._disconnected = True
            return EncodedBearerAttemptResult(action, (), False, disconnected=True)
        if action is ImpairmentAction.DUPLICATE:
            return EncodedBearerAttemptResult(action, (encoded, encoded), True)
        if action is ImpairmentAction.DELIVER_UNCERTAIN:
            return EncodedBearerAttemptResult(action, (encoded,), False)
        if action is ImpairmentAction.DELAY_DELIVER:
            if self._pending is not None:
                raise B2BoundsError("delay slot is occupied")
            self._pending = encoded
            self._queued_peak = max(self._queued_peak, 1)
            delivered = self._pending
            self._pending = None
            return EncodedBearerAttemptResult(
                action, (delivered,), True, delayed=True
            )
        return EncodedBearerAttemptResult(action, (encoded,), True)


@dataclass(frozen=True, slots=True)
class B2ContactSelection:
    left_wants_from_right: tuple[bytes, ...] = ()
    right_wants_from_left: tuple[bytes, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "left_wants_from_right",
            _canonical_identities(
                RecordKind.REFERENCE, self.left_wants_from_right
            ),
        )
        object.__setattr__(
            self,
            "right_wants_from_left",
            _canonical_identities(
                RecordKind.REFERENCE, self.right_wants_from_left
            ),
        )


@dataclass(frozen=True, slots=True)
class B2ContactBudget:
    max_control_messages: int = MAX_B2_CONTROL_MESSAGES
    max_control_bytes: int = MAX_CONTACT_BYTES
    max_record_messages: int = MAX_B2_RECORD_MESSAGES
    max_record_bytes: int = MAX_CONTACT_BYTES
    max_record_logical_bytes: int = MAX_CONTACT_BYTES
    max_bearer_attempts: int = MAX_B2_BEARER_ATTEMPTS
    max_trace_entries: int = MAX_B2_TRACE_ENTRIES

    def __post_init__(self) -> None:
        bounds = (
            ("max_control_messages", self.max_control_messages, MAX_B2_CONTROL_MESSAGES),
            ("max_control_bytes", self.max_control_bytes, MAX_B2_CONTROL_BYTES),
            ("max_record_messages", self.max_record_messages, MAX_B2_RECORD_MESSAGES),
            ("max_record_bytes", self.max_record_bytes, MAX_B2_RECORD_BYTES),
            ("max_record_logical_bytes", self.max_record_logical_bytes, MAX_CONTACT_BYTES),
            ("max_bearer_attempts", self.max_bearer_attempts, MAX_B2_BEARER_ATTEMPTS),
            ("max_trace_entries", self.max_trace_entries, MAX_B2_TRACE_ENTRIES),
        )
        for name, value, maximum in bounds:
            if type(value) is not int or not 1 <= value <= maximum:
                raise B2BoundsError(f"{name} must be between 1 and {maximum}")


class B2ContactOutcome(str, Enum):
    NO_MORE_PLANNED_WORK = "NO_MORE_PLANNED_WORK"
    PARTIAL_NOT_DELIVERED = "PARTIAL_NOT_DELIVERED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    DISCONNECTED = "DISCONNECTED"
    SENDER_UNCERTAIN = "SENDER_UNCERTAIN"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class B2TraceEntry:
    attempt: int
    direction: LinkDirection
    message_type: B2MessageType
    encoded_bytes: int
    action: ImpairmentAction
    presentations: int
    sender_observed: bool


@dataclass(frozen=True, slots=True)
class B2ContactReport:
    outcome: B2ContactOutcome
    control_messages_sent: int
    control_bytes_encoded: int
    record_messages_sent: int
    record_bytes_encoded: int
    record_logical_bytes: int
    bearer_attempts: int
    delivered_presentations: int
    duplicate_presentations: int
    drops: int
    disconnects: int
    delayed_units: int
    sender_uncertainties: int
    decode_failures: int
    native_validation_failures: int
    native_apply_failures: int
    durable_commits: int
    already_known_records_skipped: int
    queued_units_peak: int
    error_code: str | None
    error_message: str | None
    trace: tuple[B2TraceEntry, ...]
    accounting_model: str = EXPERIMENTAL_B2_ACCOUNTING_ONLY


_NATIVE_ERRORS = (
    CatalogBoundsError,
    PersistenceError,
    QueryConflictError,
    QueryResultBoundsError,
    ReferenceConflictError,
    ResultConflictError,
)


def _error_code(error: Exception) -> str:
    if isinstance(error, QueryConflictError):
        return "QUERY_CONFLICT"
    if isinstance(error, ResultConflictError):
        return "RESULT_CONFLICT"
    if isinstance(error, ReferenceConflictError):
        return "REFERENCE_CONFLICT"
    if isinstance(error, QueryResultBoundsError):
        return "QUERY_RESULT_BOUNDS_ERROR"
    if isinstance(error, CatalogBoundsError):
        return "CATALOG_BOUNDS_ERROR"
    if isinstance(error, PersistenceError):
        return error.code
    if isinstance(error, B2DecodeError):
        return "B2_DECODE_ERROR"
    if isinstance(error, B2BoundsError):
        return "B2_BOUNDS_ERROR"
    if isinstance(error, B2ProtocolError):
        return "B2_PROTOCOL_ERROR"
    return type(error).__name__.upper()


def _opposite(direction: LinkDirection) -> LinkDirection:
    if direction is LinkDirection.LEFT_TO_RIGHT:
        return LinkDirection.RIGHT_TO_LEFT
    return LinkDirection.LEFT_TO_RIGHT


def run_independent_contact(
    left: IndependentEndpoint,
    right: IndependentEndpoint,
    *,
    bearer: EncodedMessageBearer,
    budget: B2ContactBudget = B2ContactBudget(),
    selection: B2ContactSelection | None = None,
) -> B2ContactReport:
    """Exchange encoded B2 messages without inspecting the peer's stores."""

    if not isinstance(left, IndependentEndpoint) or not isinstance(
        right, IndependentEndpoint
    ):
        raise TypeError("left and right must be IndependentEndpoint")
    if not isinstance(bearer, EncodedMessageBearer):
        raise TypeError("bearer must implement EncodedMessageBearer")
    if not isinstance(budget, B2ContactBudget):
        raise TypeError("budget must be B2ContactBudget")
    active_selection = B2ContactSelection() if selection is None else selection
    if not isinstance(active_selection, B2ContactSelection):
        raise TypeError("selection must be B2ContactSelection or None")

    counters = {
        "control_messages": 0,
        "control_bytes": 0,
        "record_messages": 0,
        "record_bytes": 0,
        "record_logical_bytes": 0,
        "attempts": 0,
        "presentations": 0,
        "duplicates": 0,
        "drops": 0,
        "disconnects": 0,
        "delays": 0,
        "uncertainties": 0,
        "decode_failures": 0,
        "native_validation_failures": 0,
        "native_apply_failures": 0,
        "commits": 0,
        "known": 0,
    }
    trace: list[B2TraceEntry] = []
    stopped: B2ContactOutcome | None = None
    failure: Exception | None = None

    def over_budget(active_type: B2MessageType, encoded: bytes, logical: int) -> bool:
        if counters["attempts"] + 1 > budget.max_bearer_attempts:
            return True
        if len(trace) + 1 > budget.max_trace_entries:
            return True
        if active_type is B2MessageType.RECORD:
            return (
                counters["record_messages"] + 1 > budget.max_record_messages
                or counters["record_bytes"] + len(encoded) > budget.max_record_bytes
                or counters["record_logical_bytes"] + logical
                > budget.max_record_logical_bytes
            )
        return (
            counters["control_messages"] + 1 > budget.max_control_messages
            or counters["control_bytes"] + len(encoded) > budget.max_control_bytes
        )

    def send(
        sender: IndependentEndpoint,
        receiver: IndependentEndpoint,
        direction: LinkDirection,
        encoded: bytes,
    ) -> bool:
        nonlocal stopped, failure
        try:
            outgoing = decode_message(encoded)
        except B2DecodeError as error:
            stopped = B2ContactOutcome.ERROR
            failure = error
            counters["decode_failures"] += 1
            return False
        active_type = message_type(outgoing)
        logical = _message_record_logical_bytes(outgoing)
        if over_budget(active_type, encoded, logical):
            stopped = B2ContactOutcome.BUDGET_EXHAUSTED
            return False
        if active_type is B2MessageType.RECORD:
            counters["record_messages"] += 1
            counters["record_bytes"] += len(encoded)
            counters["record_logical_bytes"] += logical
        else:
            counters["control_messages"] += 1
            counters["control_bytes"] += len(encoded)
        counters["attempts"] += 1
        try:
            attempt = bearer.attempt(direction, encoded)
        except (B2BoundsError, B2ProtocolError) as error:
            stopped = B2ContactOutcome.ERROR
            failure = error
            return False
        if not isinstance(attempt, EncodedBearerAttemptResult):
            stopped = B2ContactOutcome.ERROR
            failure = B2ProtocolError("bearer returned an invalid attempt result")
            return False
        trace.append(
            B2TraceEntry(
                counters["attempts"],
                direction,
                active_type,
                len(encoded),
                attempt.action,
                len(attempt.presentations),
                attempt.sender_observed,
            )
        )
        if attempt.disconnected:
            counters["disconnects"] += 1
            stopped = B2ContactOutcome.DISCONNECTED
            return False
        if not attempt.presentations:
            counters["drops"] += 1
            return True

        responses: list[bytes] = []
        for delivered in attempt.presentations:
            delivered_type: B2MessageType | None = None
            try:
                delivered_type = message_type(decode_message(delivered))
                received = receiver.receive_message(delivered)
            except B2DecodeError as error:
                counters["decode_failures"] += 1
                stopped = B2ContactOutcome.ERROR
                failure = error
                return False
            except _NATIVE_ERRORS as error:
                if delivered_type is B2MessageType.RECORD:
                    counters["native_apply_failures"] += 1
                else:
                    counters["native_validation_failures"] += 1
                stopped = B2ContactOutcome.ERROR
                failure = error
                return False
            except (B2BoundsError, B2ProtocolError, LookupError) as error:
                stopped = B2ContactOutcome.ERROR
                failure = error
                return False
            counters["presentations"] += 1
            counters["commits"] += received.durable_commits
            counters["known"] += received.already_known
            responses.extend(received.outbound_messages)
            if len(responses) > MAX_B2_OUTBOUND_MESSAGES * MAX_PRESENTATIONS_PER_ATTEMPT:
                stopped = B2ContactOutcome.ERROR
                failure = B2BoundsError("duplicate response fanout exceeds bound")
                return False
        counters["duplicates"] += max(0, len(attempt.presentations) - 1)
        counters["delays"] += int(attempt.delayed)
        if not attempt.sender_observed:
            counters["uncertainties"] += 1
            stopped = B2ContactOutcome.SENDER_UNCERTAIN
            return False
        for response in responses:
            if not send(receiver, sender, _opposite(direction), response):
                return False
        return True

    phases = (
        (left, right, LinkDirection.LEFT_TO_RIGHT, RecordKind.QUERY),
        (right, left, LinkDirection.RIGHT_TO_LEFT, RecordKind.QUERY),
        (left, right, LinkDirection.LEFT_TO_RIGHT, RecordKind.RESULT),
        (right, left, LinkDirection.RIGHT_TO_LEFT, RecordKind.RESULT),
    )
    for sender, receiver, direction, kind in phases:
        for encoded in sender.advertisement_messages(kind):
            if not send(sender, receiver, direction, encoded):
                break
        if stopped is not None:
            break

    if stopped is None:
        selections = (
            (
                left,
                right,
                LinkDirection.LEFT_TO_RIGHT,
                active_selection.left_wants_from_right,
            ),
            (
                right,
                left,
                LinkDirection.RIGHT_TO_LEFT,
                active_selection.right_wants_from_left,
            ),
        )
        for requester, source, direction, selected_keys in selections:
            encoded = requester.reference_selection_message(selected_keys)
            if encoded is not None and not send(requester, source, direction, encoded):
                break

    final_outcome = stopped
    if final_outcome is None:
        final_outcome = (
            B2ContactOutcome.PARTIAL_NOT_DELIVERED
            if counters["drops"]
            else B2ContactOutcome.NO_MORE_PLANNED_WORK
        )
    queued_peak = (
        bearer.queued_units_peak
        if isinstance(bearer, ScriptedEncodedMessageLink)
        else 0
    )
    return B2ContactReport(
        outcome=final_outcome,
        control_messages_sent=counters["control_messages"],
        control_bytes_encoded=counters["control_bytes"],
        record_messages_sent=counters["record_messages"],
        record_bytes_encoded=counters["record_bytes"],
        record_logical_bytes=counters["record_logical_bytes"],
        bearer_attempts=counters["attempts"],
        delivered_presentations=counters["presentations"],
        duplicate_presentations=counters["duplicates"],
        drops=counters["drops"],
        disconnects=counters["disconnects"],
        delayed_units=counters["delays"],
        sender_uncertainties=counters["uncertainties"],
        decode_failures=counters["decode_failures"],
        native_validation_failures=counters["native_validation_failures"],
        native_apply_failures=counters["native_apply_failures"],
        durable_commits=counters["commits"],
        already_known_records_skipped=counters["known"],
        queued_units_peak=queued_peak,
        error_code=None if failure is None else _error_code(failure),
        error_message=None if failure is None else str(failure),
        trace=tuple(trace),
    )


__all__ = [
    "AdvertisementMessage",
    "AdvertisedIdentity",
    "B2BoundsError",
    "B2ContactBudget",
    "B2ContactOutcome",
    "B2ContactReport",
    "B2ContactSelection",
    "B2DecodeError",
    "B2MessageType",
    "B2ProtocolError",
    "B2TraceEntry",
    "EncodedBearerAttemptResult",
    "EncodedMessageBearer",
    "EndpointReceiveResult",
    "EXPERIMENTAL_B2_ACCOUNTING_ONLY",
    "EXPERIMENTAL_B2_ENCODING",
    "IndependentEndpoint",
    "MAX_B2_BEARER_ATTEMPTS",
    "MAX_B2_CONTROL_BYTES",
    "MAX_B2_CONTROL_MESSAGES",
    "MAX_B2_IDENTITIES_PER_MESSAGE",
    "MAX_B2_MESSAGE_BYTES",
    "MAX_B2_OUTBOUND_MESSAGES",
    "MAX_B2_RECORD_BYTES",
    "MAX_B2_RECORD_MESSAGES",
    "MAX_B2_TRACE_ENTRIES",
    "RecordKind",
    "RecordMessage",
    "ReferenceSelectionMessage",
    "RequestMessage",
    "ScriptedEncodedMessageLink",
    "decode_message",
    "encode_message",
    "message_type",
    "record_digest",
    "run_independent_contact",
]
