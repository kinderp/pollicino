from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import IntEnum
import hashlib
import struct
from typing import Sequence

from .bearer import (
    ImpairmentAction,
    LinkDirection,
    MAX_PRESENTATIONS_PER_ATTEMPT,
)
from .catalog import (
    MAX_CATALOG_ITEMS,
    MAX_EXCHANGE_ITEMS,
    MAX_LOGICAL_KEY_BYTES,
    BoundedReference,
    BoundedReferenceCatalog,
    CatalogBoundsError,
    ReferenceConflictError,
)
from .endpoint import (
    B2ContactBudget,
    B2ContactOutcome,
    B2BoundsError,
    B2DecodeError,
    B2MessageType,
    B2ProtocolError,
    EncodedBearerAttemptResult,
    EncodedMessageBearer,
    IndependentEndpoint,
    MAX_B2_IDENTITIES_PER_MESSAGE,
    MAX_B2_MESSAGE_BYTES,
    MAX_B2_OUTBOUND_MESSAGES,
    AdvertisementMessage,
    RecordKind,
    RecordMessage,
    RequestMessage,
    _Reader,
    _decode_identity,
    _encode_identity,
    _identity_sort_key,
    _message_record_logical_bytes,
    decode_message,
    encode_message,
    message_type,
    record_digest,
)
from .local_persistence import PersistenceError
from .query import (
    MAX_QUERY_ID_BYTES,
    MAX_RESULT_ID_BYTES,
    QueryConflictError,
    QueryRecord,
    QueryResultBoundsError,
    QueryResultStore,
    ResultConflictError,
    ResultIdentity,
    ResultRecord,
)


EXPERIMENTAL_B2F_ENCODING = "pollicino.experimental-b2f.v1"
EXPERIMENTAL_B2F_ACCOUNTING_ONLY = "EXPERIMENTAL_B2F_ACCOUNTING_ONLY"
B2F_MAGIC = b"PB2F"
B2F_VERSION = 1
B2F_DIGEST_BYTES = 32

_HEADER = struct.Struct(">4sBBI32s")
_COUNT = struct.Struct(">H")
_RECORD_COUNT = struct.Struct(">H")

MAX_B2F_PAGE_IDENTITIES = MAX_B2_IDENTITIES_PER_MESSAGE
MAX_B2F_PAGES = max(
    MAX_CATALOG_ITEMS,
    10_000,
) // MAX_B2F_PAGE_IDENTITIES
MAX_B2F_DESCRIPTORS_PER_MESSAGE = 50
MAX_B2F_DIRECTORY_MESSAGES_PER_KIND = (
    MAX_B2F_PAGES + MAX_B2F_DESCRIPTORS_PER_MESSAGE - 1
) // MAX_B2F_DESCRIPTORS_PER_MESSAGE
MAX_B2F_SELECTED_REFERENCES = MAX_CATALOG_ITEMS
MAX_RESULT_IDENTITY_ENCODED_BYTES = 4 + MAX_QUERY_ID_BYTES + MAX_RESULT_ID_BYTES
MAX_B2F_DESCRIPTOR_BYTES = (
    _RECORD_COUNT.size
    + 2 * MAX_RESULT_IDENTITY_ENCODED_BYTES
    + B2F_DIGEST_BYTES
)
MAX_B2F_MESSAGE_BYTES = (
    _HEADER.size
    + 1
    + _COUNT.size
    + MAX_B2F_DESCRIPTORS_PER_MESSAGE * MAX_B2F_DESCRIPTOR_BYTES
)
MAX_B2F_LANES = 6
MAX_B2F_PROTOCOL_QUEUE = MAX_B2F_LANES * (
    MAX_B2F_DIRECTORY_MESSAGES_PER_KIND
    + 2 * MAX_B2_OUTBOUND_MESSAGES
    + MAX_B2F_DESCRIPTORS_PER_MESSAGE
)

if MAX_B2F_MESSAGE_BYTES > MAX_B2_MESSAGE_BYTES:
    raise RuntimeError("B2F control envelope exceeds the inherited B1 unit bound")


class B2FFairMessageType(IntEnum):
    DIRECTORY = 1
    PAGE_REQUEST = 2
    REFERENCE_DIRECTORY_REQUEST = 3


Identity = bytes | ResultIdentity


@dataclass(frozen=True, slots=True)
class PageDescriptor:
    record_count: int
    first_identity: Identity
    last_identity: Identity
    page_digest: bytes

    def validate(self, kind: RecordKind) -> None:
        if type(self.record_count) is not int or not (
            1 <= self.record_count <= MAX_B2F_PAGE_IDENTITIES
        ):
            raise B2BoundsError("page record count is outside bounds")
        _encode_identity(kind, self.first_identity)
        _encode_identity(kind, self.last_identity)
        if _identity_sort_key(self.first_identity) > _identity_sort_key(
            self.last_identity
        ):
            raise B2BoundsError("page identity range is reversed")
        if not isinstance(self.page_digest, bytes) or len(
            self.page_digest
        ) != B2F_DIGEST_BYTES:
            raise B2BoundsError("page digest has an invalid size")


def _canonical_descriptors(
    kind: RecordKind, descriptors: Sequence[PageDescriptor]
) -> tuple[PageDescriptor, ...]:
    if not isinstance(descriptors, (tuple, list)):
        raise TypeError("descriptors must be a tuple or list")
    values = tuple(descriptors)
    if not 1 <= len(values) <= MAX_B2F_DESCRIPTORS_PER_MESSAGE:
        raise B2BoundsError("descriptor count is outside bounds")
    for descriptor in values:
        if not isinstance(descriptor, PageDescriptor):
            raise TypeError("descriptors must contain PageDescriptor values")
        descriptor.validate(kind)
    ordered = tuple(
        sorted(values, key=lambda value: _identity_sort_key(value.first_identity))
    )
    for previous, active in zip(ordered, ordered[1:]):
        if _identity_sort_key(previous.last_identity) >= _identity_sort_key(
            active.first_identity
        ):
            raise B2BoundsError("page descriptor ranges overlap")
    return ordered


@dataclass(frozen=True, slots=True)
class DirectoryMessage:
    kind: RecordKind
    pages: tuple[PageDescriptor, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, RecordKind):
            raise TypeError("kind must be RecordKind")
        object.__setattr__(self, "pages", _canonical_descriptors(self.kind, self.pages))


@dataclass(frozen=True, slots=True)
class PageRequestMessage:
    kind: RecordKind
    pages: tuple[PageDescriptor, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, RecordKind):
            raise TypeError("kind must be RecordKind")
        object.__setattr__(self, "pages", _canonical_descriptors(self.kind, self.pages))


@dataclass(frozen=True, slots=True)
class ReferenceDirectoryRequestMessage:
    pass


B2FFairMessage = DirectoryMessage | PageRequestMessage | ReferenceDirectoryRequestMessage


def fair_message_type(message: B2FFairMessage) -> B2FFairMessageType:
    if isinstance(message, DirectoryMessage):
        return B2FFairMessageType.DIRECTORY
    if isinstance(message, PageRequestMessage):
        return B2FFairMessageType.PAGE_REQUEST
    if isinstance(message, ReferenceDirectoryRequestMessage):
        return B2FFairMessageType.REFERENCE_DIRECTORY_REQUEST
    raise TypeError("unsupported B2F message")


def _encode_descriptors(kind: RecordKind, pages: tuple[PageDescriptor, ...]) -> bytes:
    body = bytearray(bytes((kind,)) + _COUNT.pack(len(pages)))
    for page in pages:
        body += _RECORD_COUNT.pack(page.record_count)
        body += _encode_identity(kind, page.first_identity)
        body += _encode_identity(kind, page.last_identity)
        body += page.page_digest
    return bytes(body)


def encode_fair_message(message: B2FFairMessage) -> bytes:
    active_type = fair_message_type(message)
    if isinstance(message, (DirectoryMessage, PageRequestMessage)):
        body = _encode_descriptors(message.kind, message.pages)
    else:
        body = b""
    encoded = _HEADER.pack(
        B2F_MAGIC,
        B2F_VERSION,
        active_type,
        len(body),
        hashlib.sha256(body).digest(),
    ) + body
    if len(encoded) > MAX_B2F_MESSAGE_BYTES:
        raise B2BoundsError("encoded B2F message exceeds maximum")
    return encoded


def _decode_kind(reader: _Reader) -> RecordKind:
    try:
        return RecordKind(reader.take(1)[0])
    except (IndexError, ValueError) as error:
        raise B2DecodeError("unknown B2F record kind") from error


def _decode_descriptors(reader: _Reader) -> tuple[RecordKind, tuple[PageDescriptor, ...]]:
    kind = _decode_kind(reader)
    (count,) = reader.unpack(_COUNT)
    if not 1 <= count <= MAX_B2F_DESCRIPTORS_PER_MESSAGE:
        raise B2DecodeError("B2F descriptor count is outside bounds")
    pages = tuple(
        PageDescriptor(
            reader.unpack(_RECORD_COUNT)[0],
            _decode_identity(kind, reader),
            _decode_identity(kind, reader),
            reader.take(B2F_DIGEST_BYTES),
        )
        for _ in range(count)
    )
    return kind, pages


def decode_fair_message(data: bytes) -> B2FFairMessage:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if len(data) > MAX_B2F_MESSAGE_BYTES:
        raise B2DecodeError("encoded B2F message exceeds maximum")
    if len(data) < _HEADER.size:
        raise B2DecodeError("B2F message header is truncated")
    magic, version, raw_type, body_length, digest = _HEADER.unpack_from(data)
    if magic != B2F_MAGIC:
        raise B2DecodeError("invalid B2F message magic")
    if version != B2F_VERSION:
        raise B2DecodeError(f"unsupported B2F message version: {version}")
    try:
        active_type = B2FFairMessageType(raw_type)
    except ValueError as error:
        raise B2DecodeError("unknown B2F message type") from error
    body = data[_HEADER.size :]
    if len(body) != body_length:
        raise B2DecodeError("B2F message length mismatch")
    if hashlib.sha256(body).digest() != digest:
        raise B2DecodeError("B2F message integrity mismatch")
    reader = _Reader(body)
    try:
        if active_type is B2FFairMessageType.REFERENCE_DIRECTORY_REQUEST:
            reader.finish()
            return ReferenceDirectoryRequestMessage()
        kind, pages = _decode_descriptors(reader)
        reader.finish()
        if active_type is B2FFairMessageType.DIRECTORY:
            return DirectoryMessage(kind, pages)
        return PageRequestMessage(kind, pages)
    except B2DecodeError:
        raise
    except (IndexError, TypeError, ValueError) as error:
        raise B2DecodeError("invalid B2F message body") from error


def _selection(keys: Sequence[bytes]) -> tuple[bytes, ...]:
    if not isinstance(keys, (tuple, list)):
        raise TypeError("selected references must be a tuple or list")
    values = tuple(keys)
    if len(values) > MAX_B2F_SELECTED_REFERENCES:
        raise B2BoundsError("selected reference policy exceeds catalog bound")
    if len(set(values)) != len(values):
        raise ValueError("selected reference policy contains duplicates")
    for key in values:
        if not isinstance(key, bytes) or not key or len(key) > MAX_LOGICAL_KEY_BYTES:
            raise B2BoundsError("selected reference identity is outside bounds")
    return tuple(sorted(values))


@dataclass(frozen=True, slots=True)
class FairContactSelection:
    left_wants_from_right: tuple[bytes, ...] = ()
    right_wants_from_left: tuple[bytes, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "left_wants_from_right", _selection(self.left_wants_from_right)
        )
        object.__setattr__(
            self, "right_wants_from_left", _selection(self.right_wants_from_left)
        )


@dataclass(frozen=True, slots=True)
class FairEndpointReceiveResult:
    outbound_messages: tuple[bytes, ...] = ()
    durable_commits: int = 0
    already_known: int = 0
    pages_reached: int = 0
    pages_repeated: int = 0
    known_metadata_repeated: int = 0
    repeated_control_bytes: int = 0

    def __post_init__(self) -> None:
        if len(self.outbound_messages) > MAX_B2_OUTBOUND_MESSAGES:
            raise B2BoundsError("B2F endpoint response exceeds outbound bound")


class FairIndependentEndpoint:
    """Independent B2F endpoint; all reconciliation reads are local."""

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
        self.__catalog = catalog
        self.__query_results = query_results
        self.__base = IndependentEndpoint(catalog, query_results, diagnostic_label)
        self.diagnostic_label = diagnostic_label

    def _local_ids(self, kind: RecordKind) -> tuple[Identity, ...]:
        values: list[Identity] = []
        offset = 0
        while True:
            if kind is RecordKind.QUERY:
                page: tuple[Identity, ...] = self.__query_results.sorted_query_ids(
                    offset=offset
                )
            elif kind is RecordKind.RESULT:
                page = self.__query_results.sorted_result_ids(offset=offset)
            else:
                page = self.__catalog.sorted_logical_ids(offset=offset)
            if not page:
                return tuple(values)
            values.extend(page)
            offset += len(page)

    def _local_record(self, kind: RecordKind, identity: Identity):
        if kind is RecordKind.QUERY:
            assert isinstance(identity, bytes)
            return self.__query_results.get_query(identity)
        if kind is RecordKind.RESULT:
            assert isinstance(identity, ResultIdentity)
            return self.__query_results.get_result(identity)
        assert isinstance(identity, bytes)
        return self.__catalog.get(identity)

    def _page_digest(self, kind: RecordKind, identities: Sequence[Identity]) -> bytes:
        body = bytearray()
        for identity in identities:
            body += _encode_identity(kind, identity)
            body += record_digest(kind, self._local_record(kind, identity))
        return hashlib.sha256(bytes(body)).digest()

    def directory_messages(self, kind: RecordKind) -> tuple[bytes, ...]:
        identities = self._local_ids(kind)
        descriptors = tuple(
            PageDescriptor(
                len(page),
                page[0],
                page[-1],
                self._page_digest(kind, page),
            )
            for start in range(0, len(identities), MAX_B2F_PAGE_IDENTITIES)
            if (page := identities[start : start + MAX_B2F_PAGE_IDENTITIES])
        )
        return tuple(
            encode_fair_message(
                DirectoryMessage(
                    kind,
                    descriptors[start : start + MAX_B2F_DESCRIPTORS_PER_MESSAGE],
                )
            )
            for start in range(0, len(descriptors), MAX_B2F_DESCRIPTORS_PER_MESSAGE)
        )

    def _ids_in_range(
        self,
        kind: RecordKind,
        descriptor: PageDescriptor,
        identities: tuple[Identity, ...] | None = None,
    ) -> tuple[Identity, ...]:
        low = _identity_sort_key(descriptor.first_identity)
        high = _identity_sort_key(descriptor.last_identity)
        return tuple(
            identity
            for identity in (
                self._local_ids(kind) if identities is None else identities
            )
            if low <= _identity_sort_key(identity) <= high
        )

    def _receive_directory(
        self,
        encoded: bytes,
        message: DirectoryMessage,
        selected_references: tuple[bytes, ...],
    ) -> FairEndpointReceiveResult:
        divergent: list[PageDescriptor] = []
        repeated = 0
        all_local_ids = self._local_ids(message.kind)
        for page in message.pages:
            local_ids = self._ids_in_range(message.kind, page, all_local_ids)
            if message.kind is RecordKind.REFERENCE:
                low = _identity_sort_key(page.first_identity)
                high = _identity_sort_key(page.last_identity)
                wanted = tuple(
                    key
                    for key in selected_references
                    if low <= _identity_sort_key(key) <= high and key not in self.__catalog
                )
                if wanted:
                    divergent.append(page)
                else:
                    repeated += 1
            elif len(local_ids) == page.record_count and self._page_digest(
                message.kind, local_ids
            ) == page.page_digest:
                repeated += 1
            else:
                divergent.append(page)
        outbound = (
            (encode_fair_message(PageRequestMessage(message.kind, tuple(divergent))),)
            if divergent
            else ()
        )
        return FairEndpointReceiveResult(
            outbound,
            pages_reached=len(message.pages),
            pages_repeated=repeated,
            known_metadata_repeated=repeated,
            repeated_control_bytes=len(encoded) if repeated == len(message.pages) else 0,
        )

    def _advertisement(
        self, kind: RecordKind, identities: tuple[Identity, ...]
    ) -> bytes:
        from .endpoint import AdvertisedIdentity

        entries = tuple(
            AdvertisedIdentity(
                identity, record_digest(kind, self._local_record(kind, identity))
            )
            for identity in identities
        )
        return encode_message(AdvertisementMessage(kind, entries))

    def _receive_page_request(
        self, message: PageRequestMessage
    ) -> FairEndpointReceiveResult:
        outbound: list[bytes] = []
        all_local_ids = self._local_ids(message.kind)
        for page in message.pages:
            identities = self._ids_in_range(message.kind, page, all_local_ids)
            if len(identities) > MAX_B2F_PAGE_IDENTITIES:
                raise B2BoundsError("stale page range exceeds advertisement bound")
            if identities:
                outbound.append(self._advertisement(message.kind, identities))
        return FairEndpointReceiveResult(tuple(outbound))

    def _receive_reference_advertisement(
        self,
        encoded: bytes,
        message: AdvertisementMessage,
        selected_references: tuple[bytes, ...],
    ) -> FairEndpointReceiveResult:
        selected = set(selected_references)
        missing: list[Identity] = []
        known = 0
        relevant = 0
        for entry in message.entries:
            assert isinstance(entry.identity, bytes)
            if entry.identity not in selected:
                continue
            relevant += 1
            try:
                local = self.__catalog.get(entry.identity)
            except LookupError:
                missing.append(entry.identity)
                continue
            if record_digest(RecordKind.REFERENCE, local) != entry.record_digest:
                raise ReferenceConflictError(entry.identity)
            known += 1
        outbound = (
            (encode_message(RequestMessage(RecordKind.REFERENCE, tuple(missing))),)
            if missing
            else ()
        )
        return FairEndpointReceiveResult(
            outbound,
            already_known=known,
            known_metadata_repeated=known,
            repeated_control_bytes=len(encoded) if relevant and known == relevant else 0,
        )

    def receive_message(
        self,
        encoded: bytes,
        *,
        selected_references: Sequence[bytes] = (),
    ) -> FairEndpointReceiveResult:
        selected = _selection(selected_references)
        if encoded[:4] == B2F_MAGIC:
            message = decode_fair_message(encoded)
            if isinstance(message, DirectoryMessage):
                return self._receive_directory(encoded, message, selected)
            if isinstance(message, PageRequestMessage):
                return self._receive_page_request(message)
            return FairEndpointReceiveResult(
                self.directory_messages(RecordKind.REFERENCE)
            )
        message = decode_message(encoded)
        if isinstance(message, AdvertisementMessage) and message.kind is RecordKind.REFERENCE:
            return self._receive_reference_advertisement(encoded, message, selected)
        received = self.__base.receive_message(encoded)
        return FairEndpointReceiveResult(
            received.outbound_messages,
            received.durable_commits,
            received.already_known,
            known_metadata_repeated=received.already_known,
            repeated_control_bytes=(
                len(encoded)
                if isinstance(message, AdvertisementMessage)
                and received.already_known == len(message.entries)
                else 0
            ),
        )


@dataclass(frozen=True, slots=True)
class FairTraceEntry:
    attempt: int
    lane: str
    direction: LinkDirection
    message_type: str
    encoded_bytes: int
    action: ImpairmentAction
    presentations: int
    sender_observed: bool


@dataclass(frozen=True, slots=True)
class FairContactReport:
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
    pages_total: int
    pages_reached: int
    pages_repeated: int
    identities_disclosed: int
    digests_disclosed: int
    missing_ids_requested: int
    known_metadata_repeated: int
    repeated_control_bytes: int
    protocol_queue_peak: int
    bearer_queue_peak: int
    progress_left_to_right: int
    progress_right_to_left: int
    error_code: str | None
    error_message: str | None
    trace: tuple[FairTraceEntry, ...]
    accounting_model: str = EXPERIMENTAL_B2F_ACCOUNTING_ONLY


@dataclass(frozen=True, slots=True)
class _Envelope:
    sender: FairIndependentEndpoint
    receiver: FairIndependentEndpoint
    direction: LinkDirection
    encoded: bytes
    lane: str


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


@dataclass(frozen=True, slots=True)
class _MessageInfo:
    label: str
    is_record: bool
    logical_bytes: int
    identities: int
    digests: int
    missing_ids: int
    pages: int


def _message_info(encoded: bytes) -> _MessageInfo:
    if encoded[:4] == B2F_MAGIC:
        message = decode_fair_message(encoded)
        active_type = fair_message_type(message)
        pages = len(message.pages) if isinstance(message, (DirectoryMessage, PageRequestMessage)) else 0
        identities = 2 * pages
        digests = pages if isinstance(message, DirectoryMessage) else 0
        return _MessageInfo(
            f"B2F_{active_type.name}", False, 0, identities, digests, 0, pages
        )
    message = decode_message(encoded)
    active_type = message_type(message)
    identities = 0
    digests = 0
    missing = 0
    if isinstance(message, AdvertisementMessage):
        identities = len(message.entries)
        digests = len(message.entries)
    elif isinstance(message, RequestMessage):
        identities = len(message.identities)
        missing = len(message.identities)
    return _MessageInfo(
        f"B2_{active_type.name}",
        active_type is B2MessageType.RECORD,
        _message_record_logical_bytes(message),
        identities,
        digests,
        missing,
        0,
    )


def run_fair_contact(
    left: FairIndependentEndpoint,
    right: FairIndependentEndpoint,
    *,
    bearer: EncodedMessageBearer,
    budget: B2ContactBudget = B2ContactBudget(),
    selection: FairContactSelection | None = None,
) -> FairContactReport:
    """Run bounded fair lanes; no store or progress state crosses this API."""

    if not isinstance(left, FairIndependentEndpoint) or not isinstance(
        right, FairIndependentEndpoint
    ):
        raise TypeError("left and right must be FairIndependentEndpoint")
    if not isinstance(bearer, EncodedMessageBearer):
        raise TypeError("bearer must implement EncodedMessageBearer")
    if not isinstance(budget, B2ContactBudget):
        raise TypeError("budget must be B2ContactBudget")
    active_selection = FairContactSelection() if selection is None else selection
    if not isinstance(active_selection, FairContactSelection):
        raise TypeError("selection must be FairContactSelection or None")

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
        "pages_total": 0,
        "pages_reached": 0,
        "pages_repeated": 0,
        "identities": 0,
        "digests": 0,
        "missing_ids": 0,
        "known_metadata": 0,
        "repeated_control_bytes": 0,
        "ltr_commits": 0,
        "rtl_commits": 0,
    }
    trace: list[FairTraceEntry] = []
    failure: Exception | None = None
    stopped: B2ContactOutcome | None = None

    lanes: list[deque[_Envelope]] = []

    def add_lane(
        name: str,
        sender: FairIndependentEndpoint,
        receiver: FairIndependentEndpoint,
        direction: LinkDirection,
        messages: Sequence[bytes],
    ) -> None:
        if messages:
            lanes.append(
                deque(
                    _Envelope(sender, receiver, direction, encoded, name)
                    for encoded in messages
                )
            )

    add_lane(
        "QUERY_LEFT_TO_RIGHT",
        left,
        right,
        LinkDirection.LEFT_TO_RIGHT,
        left.directory_messages(RecordKind.QUERY),
    )
    add_lane(
        "QUERY_RIGHT_TO_LEFT",
        right,
        left,
        LinkDirection.RIGHT_TO_LEFT,
        right.directory_messages(RecordKind.QUERY),
    )
    add_lane(
        "RESULT_LEFT_TO_RIGHT",
        left,
        right,
        LinkDirection.LEFT_TO_RIGHT,
        left.directory_messages(RecordKind.RESULT),
    )
    add_lane(
        "RESULT_RIGHT_TO_LEFT",
        right,
        left,
        LinkDirection.RIGHT_TO_LEFT,
        right.directory_messages(RecordKind.RESULT),
    )
    if active_selection.left_wants_from_right:
        add_lane(
            "REFERENCE_RIGHT_TO_LEFT",
            left,
            right,
            LinkDirection.LEFT_TO_RIGHT,
            (encode_fair_message(ReferenceDirectoryRequestMessage()),),
        )
    if active_selection.right_wants_from_left:
        add_lane(
            "REFERENCE_LEFT_TO_RIGHT",
            right,
            left,
            LinkDirection.RIGHT_TO_LEFT,
            (encode_fair_message(ReferenceDirectoryRequestMessage()),),
        )

    def receiver_selection(endpoint: FairIndependentEndpoint) -> tuple[bytes, ...]:
        if endpoint is left:
            return active_selection.left_wants_from_right
        return active_selection.right_wants_from_left

    queue_peak = sum(len(lane) for lane in lanes)

    def over_budget(info: _MessageInfo, encoded: bytes) -> bool:
        if counters["attempts"] + 1 > budget.max_bearer_attempts:
            return True
        if len(trace) + 1 > budget.max_trace_entries:
            return True
        if info.is_record:
            return (
                counters["record_messages"] + 1 > budget.max_record_messages
                or counters["record_bytes"] + len(encoded) > budget.max_record_bytes
                or counters["record_logical_bytes"] + info.logical_bytes
                > budget.max_record_logical_bytes
            )
        return (
            counters["control_messages"] + 1 > budget.max_control_messages
            or counters["control_bytes"] + len(encoded) > budget.max_control_bytes
        )

    while any(lanes) and stopped is None:
        for lane in lanes:
            if not lane or stopped is not None:
                continue
            envelope = lane.popleft()
            try:
                info = _message_info(envelope.encoded)
            except B2DecodeError as error:
                counters["decode_failures"] += 1
                failure = error
                stopped = B2ContactOutcome.ERROR
                break
            if over_budget(info, envelope.encoded):
                stopped = B2ContactOutcome.BUDGET_EXHAUSTED
                break
            counter_prefix = "record" if info.is_record else "control"
            counters[f"{counter_prefix}_messages"] += 1
            counters[f"{counter_prefix}_bytes"] += len(envelope.encoded)
            if info.is_record:
                counters["record_logical_bytes"] += info.logical_bytes
            counters["attempts"] += 1
            counters["pages_total"] += info.pages if info.label == "B2F_DIRECTORY" else 0
            counters["identities"] += info.identities
            counters["digests"] += info.digests
            counters["missing_ids"] += info.missing_ids
            try:
                attempt = bearer.attempt(envelope.direction, envelope.encoded)
            except (B2BoundsError, B2ProtocolError) as error:
                failure = error
                stopped = B2ContactOutcome.ERROR
                break
            if not isinstance(attempt, EncodedBearerAttemptResult):
                failure = B2ProtocolError("bearer returned an invalid attempt result")
                stopped = B2ContactOutcome.ERROR
                break
            trace.append(
                FairTraceEntry(
                    counters["attempts"],
                    envelope.lane,
                    envelope.direction,
                    info.label,
                    len(envelope.encoded),
                    attempt.action,
                    len(attempt.presentations),
                    attempt.sender_observed,
                )
            )
            if attempt.disconnected:
                counters["disconnects"] += 1
                stopped = B2ContactOutcome.DISCONNECTED
                break
            if not attempt.presentations:
                counters["drops"] += 1
                continue

            responses: list[bytes] = []
            for delivered in attempt.presentations:
                try:
                    delivered_info = _message_info(delivered)
                    received = envelope.receiver.receive_message(
                        delivered,
                        selected_references=receiver_selection(envelope.receiver),
                    )
                except B2DecodeError as error:
                    counters["decode_failures"] += 1
                    failure = error
                    stopped = B2ContactOutcome.ERROR
                    break
                except _NATIVE_ERRORS as error:
                    if info.is_record:
                        counters["native_apply_failures"] += 1
                    else:
                        counters["native_validation_failures"] += 1
                    failure = error
                    stopped = B2ContactOutcome.ERROR
                    break
                except (B2BoundsError, B2ProtocolError, LookupError) as error:
                    failure = error
                    stopped = B2ContactOutcome.ERROR
                    break
                counters["presentations"] += 1
                counters["commits"] += received.durable_commits
                counters["known"] += received.already_known
                counters["pages_reached"] += received.pages_reached
                counters["pages_repeated"] += received.pages_repeated
                counters["known_metadata"] += received.known_metadata_repeated
                counters["repeated_control_bytes"] += received.repeated_control_bytes
                if envelope.direction is LinkDirection.LEFT_TO_RIGHT:
                    counters["ltr_commits"] += received.durable_commits
                else:
                    counters["rtl_commits"] += received.durable_commits
                responses.extend(received.outbound_messages)
                if len(responses) > MAX_B2_OUTBOUND_MESSAGES * MAX_PRESENTATIONS_PER_ATTEMPT:
                    failure = B2BoundsError("duplicate response fanout exceeds bound")
                    stopped = B2ContactOutcome.ERROR
                    break
            if stopped is not None:
                break
            counters["duplicates"] += max(0, len(attempt.presentations) - 1)
            counters["delays"] += int(attempt.delayed)
            if not attempt.sender_observed:
                counters["uncertainties"] += 1
                stopped = B2ContactOutcome.SENDER_UNCERTAIN
                break
            for response in reversed(responses):
                lane.appendleft(
                    _Envelope(
                        envelope.receiver,
                        envelope.sender,
                        (
                            LinkDirection.RIGHT_TO_LEFT
                            if envelope.direction is LinkDirection.LEFT_TO_RIGHT
                            else LinkDirection.LEFT_TO_RIGHT
                        ),
                        response,
                        envelope.lane,
                    )
                )
            queued = sum(len(active_lane) for active_lane in lanes)
            if queued > MAX_B2F_PROTOCOL_QUEUE:
                failure = B2BoundsError("B2F protocol queue exceeds bound")
                stopped = B2ContactOutcome.ERROR
                break
            queue_peak = max(queue_peak, queued)

    outcome = stopped
    if outcome is None:
        outcome = (
            B2ContactOutcome.PARTIAL_NOT_DELIVERED
            if counters["drops"]
            else B2ContactOutcome.NO_MORE_PLANNED_WORK
        )
    bearer_peak = getattr(bearer, "queued_units_peak", 0)
    return FairContactReport(
        outcome,
        counters["control_messages"],
        counters["control_bytes"],
        counters["record_messages"],
        counters["record_bytes"],
        counters["record_logical_bytes"],
        counters["attempts"],
        counters["presentations"],
        counters["duplicates"],
        counters["drops"],
        counters["disconnects"],
        counters["delays"],
        counters["uncertainties"],
        counters["decode_failures"],
        counters["native_validation_failures"],
        counters["native_apply_failures"],
        counters["commits"],
        counters["known"],
        counters["pages_total"],
        counters["pages_reached"],
        counters["pages_repeated"],
        counters["identities"],
        counters["digests"],
        counters["missing_ids"],
        counters["known_metadata"],
        counters["repeated_control_bytes"],
        queue_peak,
        bearer_peak,
        counters["ltr_commits"],
        counters["rtl_commits"],
        None if failure is None else _error_code(failure),
        None if failure is None else str(failure),
        tuple(trace),
    )


__all__ = [
    "B2F_MAGIC",
    "B2F_VERSION",
    "B2FFairMessageType",
    "DirectoryMessage",
    "EXPERIMENTAL_B2F_ACCOUNTING_ONLY",
    "EXPERIMENTAL_B2F_ENCODING",
    "FairContactReport",
    "FairContactSelection",
    "FairEndpointReceiveResult",
    "FairIndependentEndpoint",
    "FairTraceEntry",
    "MAX_B2F_DESCRIPTORS_PER_MESSAGE",
    "MAX_B2F_MESSAGE_BYTES",
    "MAX_B2F_PAGES",
    "MAX_B2F_PROTOCOL_QUEUE",
    "MAX_B2F_SELECTED_REFERENCES",
    "PageDescriptor",
    "PageRequestMessage",
    "ReferenceDirectoryRequestMessage",
    "decode_fair_message",
    "encode_fair_message",
    "fair_message_type",
    "run_fair_contact",
]
