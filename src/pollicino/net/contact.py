from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Literal, Sequence

from .catalog import (
    MAX_EXCHANGE_ITEMS,
    MAX_LOGICAL_KEY_BYTES,
    MAX_REFERENCE_BYTES,
    BoundedReferenceCatalog,
    CatalogBoundsError,
    ReferenceConflictError,
    reconcile_and_pull,
)
from .local_persistence import PersistenceError
from .persistent_catalog import (
    PersistentBoundedReferenceCatalog,
    persist_reconcile_and_pull,
)
from .query import (
    MAX_QUERY_EXCHANGE_ITEMS,
    MAX_QUERY_ID_BYTES,
    MAX_QUERY_PAYLOAD_BYTES,
    MAX_RESULT_ID_BYTES,
    MAX_RESULT_KEYS,
    QueryConflictError,
    QueryResultBoundsError,
    QueryResultStore,
    ResultConflictError,
    ResultIdentity,
    reconcile_queries,
    reconcile_results,
)


# These sizes are the existing canonical per-entry framing plus maximum lawful
# record payload. They are accounting bounds, not a D4 frame or wire format.
MAX_QUERY_RECORD_ENCODED_BYTES = 6 + MAX_QUERY_ID_BYTES + MAX_QUERY_PAYLOAD_BYTES
MAX_RESULT_RECORD_ENCODED_BYTES = (
    6
    + MAX_QUERY_ID_BYTES
    + MAX_RESULT_ID_BYTES
    + MAX_RESULT_KEYS * (2 + MAX_LOGICAL_KEY_BYTES)
)
MAX_REFERENCE_RECORD_ENCODED_BYTES = (
    6 + MAX_LOGICAL_KEY_BYTES + MAX_REFERENCE_BYTES
)
MAX_CONTACT_ITEMS = min(MAX_EXCHANGE_ITEMS, MAX_QUERY_EXCHANGE_ITEMS)
MAX_CONTACT_BYTES = MAX_CONTACT_ITEMS * max(
    MAX_QUERY_RECORD_ENCODED_BYTES,
    MAX_RESULT_RECORD_ENCODED_BYTES,
    MAX_REFERENCE_RECORD_ENCODED_BYTES,
)
LOCAL_PROTOCOL_ACCOUNTING_ONLY = "LOCAL_PROTOCOL_ACCOUNTING_ONLY"


class ContactOutcome(str, Enum):
    NO_MORE_ELIGIBLE_WORK = "NO_MORE_ELIGIBLE_WORK"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"


class ContactPhase(str, Enum):
    QUERIES_LEFT_TO_RIGHT = "QUERIES_LEFT_TO_RIGHT"
    QUERIES_RIGHT_TO_LEFT = "QUERIES_RIGHT_TO_LEFT"
    RESULTS_LEFT_TO_RIGHT = "RESULTS_LEFT_TO_RIGHT"
    RESULTS_RIGHT_TO_LEFT = "RESULTS_RIGHT_TO_LEFT"
    REFERENCES_LEFT_TO_RIGHT = "REFERENCES_LEFT_TO_RIGHT"
    REFERENCES_RIGHT_TO_LEFT = "REFERENCES_RIGHT_TO_LEFT"


@dataclass(frozen=True, slots=True)
class ContactBudget:
    max_items: int = MAX_CONTACT_ITEMS
    max_bytes: int = MAX_CONTACT_BYTES

    def __post_init__(self) -> None:
        if type(self.max_items) is not int or not 1 <= self.max_items <= MAX_CONTACT_ITEMS:
            raise ValueError(f"max_items must be between 1 and {MAX_CONTACT_ITEMS}")
        if type(self.max_bytes) is not int or not 1 <= self.max_bytes <= MAX_CONTACT_BYTES:
            raise ValueError(f"max_bytes must be between 1 and {MAX_CONTACT_BYTES}")


def _selection(name: str, values: Sequence[bytes]) -> tuple[bytes, ...]:
    if not isinstance(values, (tuple, list)):
        raise TypeError(f"{name} must be a tuple or list")
    selected = tuple(values)
    if len(selected) > MAX_EXCHANGE_ITEMS:
        raise CatalogBoundsError(f"{name} exceeds {MAX_EXCHANGE_ITEMS} items")
    if any(not isinstance(value, bytes) for value in selected):
        raise TypeError(f"{name} values must be bytes")
    if len(set(selected)) != len(selected):
        raise ValueError(f"{name} contains duplicate keys")
    return tuple(sorted(selected))


@dataclass(frozen=True, slots=True)
class ContactSelection:
    """Caller-owned D2 selections; neither direction is persisted by D4."""

    right_wants_from_left: tuple[bytes, ...] = ()
    left_wants_from_right: tuple[bytes, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "right_wants_from_left",
            _selection("right_wants_from_left", self.right_wants_from_left),
        )
        object.__setattr__(
            self,
            "left_wants_from_right",
            _selection("left_wants_from_right", self.left_wants_from_right),
        )


@dataclass(frozen=True, slots=True)
class ContactInterruption:
    """Deterministic local fault model at complete-record boundaries."""

    before_phase: ContactPhase | None = None
    before_apply_item: int | None = None
    after_apply_item: int | None = None

    def __post_init__(self) -> None:
        if self.before_phase is not None and not isinstance(self.before_phase, ContactPhase):
            raise TypeError("before_phase must be ContactPhase")
        for name, value in (
            ("before_apply_item", self.before_apply_item),
            ("after_apply_item", self.after_apply_item),
        ):
            if value is not None and (type(value) is not int or value < 1):
                raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class ContactNode:
    catalog: BoundedReferenceCatalog
    query_results: QueryResultStore
    diagnostic_label: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.catalog, BoundedReferenceCatalog):
            raise TypeError("catalog must be BoundedReferenceCatalog")
        if not isinstance(self.query_results, QueryResultStore):
            raise TypeError("query_results must be QueryResultStore")
        if self.diagnostic_label is not None and not isinstance(self.diagnostic_label, str):
            raise TypeError("diagnostic_label must be str or None")


@dataclass(frozen=True, slots=True)
class TransferAccounting:
    queries: int = 0
    query_bytes: int = 0
    results: int = 0
    result_bytes: int = 0
    references: int = 0
    reference_bytes: int = 0

    @property
    def records(self) -> int:
        return self.queries + self.results + self.references

    @property
    def encoded_bytes(self) -> int:
        return self.query_bytes + self.result_bytes + self.reference_bytes


@dataclass(frozen=True, slots=True)
class ContactReport:
    outcome: ContactOutcome
    left_to_right: TransferAccounting
    right_to_left: TransferAccounting
    records_considered: int
    records_skipped_already_known: int
    items_used: int
    encoded_bytes_accounted: int
    items_remaining: int
    bytes_remaining: int
    remaining_missing_work: int
    budget_exhausted: bool
    interruption_point: str | None
    state_changed_left: bool
    state_changed_right: bool
    error_code: str | None
    error_message: str | None
    accounting_model: str = LOCAL_PROTOCOL_ACCOUNTING_ONLY


@dataclass(frozen=True, slots=True)
class _WorkItem:
    phase: ContactPhase
    sender: ContactNode
    receiver: ContactNode
    kind: Literal["query", "result", "reference"]
    identity: bytes | ResultIdentity
    missing: bool
    encoded_bytes: int


def _query_bytes(node: ContactNode, query_id: bytes) -> int:
    record = node.query_results.get_query(query_id)
    return 6 + record.payload_bytes


def _result_bytes(node: ContactNode, identity: ResultIdentity) -> int:
    record = node.query_results.get_result(identity)
    return 6 + len(record.query_id) + len(record.result_id) + sum(
        2 + len(key) for key in record.candidate_keys
    )


def _reference_bytes(node: ContactNode, logical_key: bytes) -> int:
    return 6 + node.catalog.get(logical_key).payload_bytes


def _query_work(
    phase: ContactPhase, sender: ContactNode, receiver: ContactNode
) -> Iterator[_WorkItem]:
    offset = 0
    while True:
        advertised = sender.query_results.sorted_query_ids(offset=offset)
        if not advertised:
            return
        scan = reconcile_queries(
            sender.query_results,
            receiver.query_results,
            advertised_ids=advertised,
            selected_ids=(),
        )
        candidates = set(scan.candidate_ids)
        for query_id in advertised:
            yield _WorkItem(
                phase,
                sender,
                receiver,
                "query",
                query_id,
                query_id in candidates,
                _query_bytes(sender, query_id),
            )
        offset += len(advertised)


def _result_work(
    phase: ContactPhase, sender: ContactNode, receiver: ContactNode
) -> Iterator[_WorkItem]:
    offset = 0
    while True:
        advertised = sender.query_results.sorted_result_ids(offset=offset)
        if not advertised:
            return
        scan = reconcile_results(
            sender.query_results,
            receiver.query_results,
            advertised_ids=advertised,
            selected_ids=(),
        )
        candidates = set(scan.candidate_ids)
        for identity in advertised:
            yield _WorkItem(
                phase,
                sender,
                receiver,
                "result",
                identity,
                identity in candidates,
                _result_bytes(sender, identity),
            )
        offset += len(advertised)


def _reference_work(
    phase: ContactPhase,
    sender: ContactNode,
    receiver: ContactNode,
    selected_keys: tuple[bytes, ...],
) -> Iterator[_WorkItem]:
    # Native D2 methods validate the complete caller selection before mutation.
    sender.catalog.pull_selected(selected_keys)
    known = set(receiver.catalog.receiver_known_ids(selected_keys))
    for logical_key in selected_keys:
        yield _WorkItem(
            phase,
            sender,
            receiver,
            "reference",
            logical_key,
            logical_key not in known,
            _reference_bytes(sender, logical_key),
        )


def _work_plan(
    left: ContactNode,
    right: ContactNode,
    selection: ContactSelection,
) -> tuple[tuple[ContactPhase, tuple[_WorkItem, ...]], ...]:
    # Materialize against the state at contact entry. Directional symmetry then
    # cannot turn a record received earlier in this same contact into new work.
    return (
        (
            ContactPhase.QUERIES_LEFT_TO_RIGHT,
            tuple(_query_work(ContactPhase.QUERIES_LEFT_TO_RIGHT, left, right)),
        ),
        (
            ContactPhase.QUERIES_RIGHT_TO_LEFT,
            tuple(_query_work(ContactPhase.QUERIES_RIGHT_TO_LEFT, right, left)),
        ),
        (
            ContactPhase.RESULTS_LEFT_TO_RIGHT,
            tuple(_result_work(ContactPhase.RESULTS_LEFT_TO_RIGHT, left, right)),
        ),
        (
            ContactPhase.RESULTS_RIGHT_TO_LEFT,
            tuple(_result_work(ContactPhase.RESULTS_RIGHT_TO_LEFT, right, left)),
        ),
        (
            ContactPhase.REFERENCES_LEFT_TO_RIGHT,
            tuple(
                _reference_work(
                    ContactPhase.REFERENCES_LEFT_TO_RIGHT,
                    left,
                    right,
                    selection.right_wants_from_left,
                )
            ),
        ),
        (
            ContactPhase.REFERENCES_RIGHT_TO_LEFT,
            tuple(
                _reference_work(
                    ContactPhase.REFERENCES_RIGHT_TO_LEFT,
                    right,
                    left,
                    selection.left_wants_from_right,
                )
            ),
        ),
    )


def _native_apply(item: _WorkItem) -> None:
    if item.kind == "query":
        assert isinstance(item.identity, bytes)
        reconcile_queries(
            item.sender.query_results,
            item.receiver.query_results,
            advertised_ids=(item.identity,),
            selected_ids=(item.identity,),
        )
        return
    if item.kind == "result":
        assert isinstance(item.identity, ResultIdentity)
        reconcile_results(
            item.sender.query_results,
            item.receiver.query_results,
            advertised_ids=(item.identity,),
            selected_ids=(item.identity,),
        )
        return
    assert isinstance(item.identity, bytes)
    reconcile = (
        persist_reconcile_and_pull
        if isinstance(item.receiver.catalog, PersistentBoundedReferenceCatalog)
        else reconcile_and_pull
    )
    reconcile(
        item.sender.catalog,
        item.receiver.catalog,
        advertised_keys=(item.identity,),
        selected_keys=(item.identity,),
    )


def _native_validate_known(item: _WorkItem) -> None:
    # The native stores remain authoritative for duplicate/conflict semantics.
    # This local collision check is not missing-work transfer accounting.
    if item.kind == "query":
        assert isinstance(item.identity, bytes)
        item.receiver.query_results.add_query(
            item.sender.query_results.get_query(item.identity)
        )
    elif item.kind == "result":
        assert isinstance(item.identity, ResultIdentity)
        item.receiver.query_results.add_result(
            item.sender.query_results.get_result(item.identity)
        )
    else:
        assert isinstance(item.identity, bytes)
        item.receiver.catalog.add(item.sender.catalog.get(item.identity))


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
    return type(error).__name__.upper()


def run_contact(
    left: ContactNode,
    right: ContactNode,
    *,
    budget: ContactBudget,
    selection: ContactSelection | None = None,
    interruption: ContactInterruption | None = None,
) -> ContactReport:
    """Run one bounded, bearer-neutral contact over existing D2/D3 state."""

    if not isinstance(left, ContactNode) or not isinstance(right, ContactNode):
        raise TypeError("left and right must be ContactNode")
    if not isinstance(budget, ContactBudget):
        raise TypeError("budget must be ContactBudget")
    active_selection = ContactSelection() if selection is None else selection
    if not isinstance(active_selection, ContactSelection):
        raise TypeError("selection must be ContactSelection or None")
    active_interruption = (
        ContactInterruption() if interruption is None else interruption
    )
    if not isinstance(active_interruption, ContactInterruption):
        raise TypeError("interruption must be ContactInterruption or None")

    left_before = (left.catalog.state_digest, left.query_results.state_digest)
    right_before = (right.catalog.state_digest, right.query_results.state_digest)
    plan = _work_plan(left, right, active_selection)
    initial_missing = sum(item.missing for _, items in plan for item in items)
    counts = {
        "left_to_right": {"query": [0, 0], "result": [0, 0], "reference": [0, 0]},
        "right_to_left": {"query": [0, 0], "result": [0, 0], "reference": [0, 0]},
    }
    considered = 0
    skipped = 0
    items_used = 0
    bytes_used = 0
    apply_ordinal = 0

    def direction(phase: ContactPhase) -> str:
        return "left_to_right" if phase.value.endswith("LEFT_TO_RIGHT") else "right_to_left"

    def accounting(name: str) -> TransferAccounting:
        values = counts[name]
        return TransferAccounting(
            queries=values["query"][0],
            query_bytes=values["query"][1],
            results=values["result"][0],
            result_bytes=values["result"][1],
            references=values["reference"][0],
            reference_bytes=values["reference"][1],
        )

    def finish(
        outcome: ContactOutcome,
        *,
        interruption_point: str | None = None,
        error: Exception | None = None,
    ) -> ContactReport:
        left_after = (left.catalog.state_digest, left.query_results.state_digest)
        right_after = (right.catalog.state_digest, right.query_results.state_digest)
        return ContactReport(
            outcome=outcome,
            left_to_right=accounting("left_to_right"),
            right_to_left=accounting("right_to_left"),
            records_considered=considered,
            records_skipped_already_known=skipped,
            items_used=items_used,
            encoded_bytes_accounted=bytes_used,
            items_remaining=budget.max_items - items_used,
            bytes_remaining=budget.max_bytes - bytes_used,
            remaining_missing_work=initial_missing - items_used,
            budget_exhausted=outcome is ContactOutcome.BUDGET_EXHAUSTED,
            interruption_point=interruption_point,
            state_changed_left=left_after != left_before,
            state_changed_right=right_after != right_before,
            error_code=None if error is None else _error_code(error),
            error_message=None if error is None else str(error),
        )

    for phase, phase_items in plan:
        if active_interruption.before_phase is phase:
            return finish(
                ContactOutcome.INTERRUPTED,
                interruption_point=f"BEFORE_PHASE:{phase.value}",
            )
        for item in phase_items:
            considered += 1
            if not item.missing:
                try:
                    _native_validate_known(item)
                except (
                    CatalogBoundsError,
                    PersistenceError,
                    QueryConflictError,
                    QueryResultBoundsError,
                    ReferenceConflictError,
                    ResultConflictError,
                ) as error:
                    return finish(ContactOutcome.ERROR, error=error)
                skipped += 1
                continue

            apply_ordinal += 1
            if active_interruption.before_apply_item == apply_ordinal:
                return finish(
                    ContactOutcome.INTERRUPTED,
                    interruption_point=f"BEFORE_APPLY:{apply_ordinal}",
                )
            if (
                items_used + 1 > budget.max_items
                or bytes_used + item.encoded_bytes > budget.max_bytes
            ):
                return finish(ContactOutcome.BUDGET_EXHAUSTED)
            try:
                _native_apply(item)
            except (
                CatalogBoundsError,
                PersistenceError,
                QueryConflictError,
                QueryResultBoundsError,
                ReferenceConflictError,
                ResultConflictError,
            ) as error:
                return finish(ContactOutcome.ERROR, error=error)
            items_used += 1
            bytes_used += item.encoded_bytes
            bucket = counts[direction(phase)][item.kind]
            bucket[0] += 1
            bucket[1] += item.encoded_bytes
            if active_interruption.after_apply_item == items_used:
                return finish(
                    ContactOutcome.INTERRUPTED,
                    interruption_point=f"AFTER_APPLY:{items_used}",
                )

    return finish(ContactOutcome.NO_MORE_ELIGIBLE_WORK)


__all__ = [
    "ContactBudget",
    "ContactInterruption",
    "ContactNode",
    "ContactOutcome",
    "ContactPhase",
    "ContactReport",
    "ContactSelection",
    "LOCAL_PROTOCOL_ACCOUNTING_ONLY",
    "MAX_CONTACT_BYTES",
    "MAX_CONTACT_ITEMS",
    "TransferAccounting",
    "run_contact",
]
