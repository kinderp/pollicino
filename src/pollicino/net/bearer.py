from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from .catalog import (
    BoundedReference,
    CatalogBoundsError,
    ReferenceConflictError,
)
from .contact import (
    MAX_CONTACT_ITEMS,
    ContactBudget,
    ContactNode,
    ContactSelection,
    _WorkItem,
    _error_code,
    _native_validate_known,
    _work_plan,
)
from .local_persistence import PersistenceError
from .query import (
    QueryConflictError,
    QueryRecord,
    QueryResultBoundsError,
    ResultConflictError,
    ResultIdentity,
    ResultRecord,
)


MAX_BEARER_ATTEMPTS = MAX_CONTACT_ITEMS
MAX_BEARER_TRACE_ENTRIES = MAX_BEARER_ATTEMPTS
MAX_QUEUED_UNITS = 1
MAX_PRESENTATIONS_PER_ATTEMPT = 2
EXPERIMENTAL_BEARER_ACCOUNTING_ONLY = "EXPERIMENTAL_BEARER_ACCOUNTING_ONLY"


class BearerBoundsError(ValueError):
    pass


class BearerContractError(RuntimeError):
    pass


class LinkDirection(str, Enum):
    LEFT_TO_RIGHT = "LEFT_TO_RIGHT"
    RIGHT_TO_LEFT = "RIGHT_TO_LEFT"


class ImpairmentAction(str, Enum):
    DELIVER = "DELIVER"
    DROP = "DROP"
    DUPLICATE = "DUPLICATE"
    DISCONNECT = "DISCONNECT"
    DELAY_DELIVER = "DELAY_DELIVER"
    DELIVER_UNCERTAIN = "DELIVER_UNCERTAIN"


class BearerContactOutcome(str, Enum):
    NO_MORE_ELIGIBLE_WORK = "NO_MORE_ELIGIBLE_WORK"
    PARTIAL_NOT_DELIVERED = "PARTIAL_NOT_DELIVERED"
    CONTACT_BUDGET_EXHAUSTED = "CONTACT_BUDGET_EXHAUSTED"
    BEARER_BUDGET_EXHAUSTED = "BEARER_BUDGET_EXHAUSTED"
    DISCONNECTED = "DISCONNECTED"
    SENDER_UNCERTAIN = "SENDER_UNCERTAIN"
    ERROR = "ERROR"


RecordValue = QueryRecord | ResultRecord | BoundedReference


@dataclass(frozen=True, slots=True)
class CompleteRecordUnit:
    """One complete local B1 unit; this is not a stable wire encoding."""

    direction: LinkDirection
    kind: str
    identity: bytes | ResultIdentity
    record: RecordValue
    logical_bytes: int

    def __post_init__(self) -> None:
        if not isinstance(self.direction, LinkDirection):
            raise TypeError("direction must be LinkDirection")
        expected = {
            "query": QueryRecord,
            "result": ResultRecord,
            "reference": BoundedReference,
        }
        if self.kind not in expected:
            raise ValueError("kind must be query, result, or reference")
        if not isinstance(self.record, expected[self.kind]):
            raise TypeError("record type does not match kind")
        if type(self.logical_bytes) is not int or self.logical_bytes <= 0:
            raise BearerBoundsError("logical_bytes must be a positive integer")


@dataclass(frozen=True, slots=True)
class BearerAttemptResult:
    action: ImpairmentAction
    presentations: tuple[CompleteRecordUnit, ...]
    sender_observed: bool
    disconnected: bool = False
    delayed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.action, ImpairmentAction):
            raise TypeError("action must be ImpairmentAction")
        if not isinstance(self.presentations, tuple):
            raise TypeError("presentations must be a tuple")
        if len(self.presentations) > MAX_PRESENTATIONS_PER_ATTEMPT:
            raise BearerBoundsError("too many presentations in one attempt")
        if any(not isinstance(unit, CompleteRecordUnit) for unit in self.presentations):
            raise TypeError("presentations must contain CompleteRecordUnit values")
        if type(self.sender_observed) is not bool:
            raise TypeError("sender_observed must be bool")
        if type(self.disconnected) is not bool or type(self.delayed) is not bool:
            raise TypeError("disconnected and delayed must be bool")


@runtime_checkable
class CompleteRecordBearer(Protocol):
    """Minimum B1 capability: attempt one complete bounded record."""

    def attempt(self, unit: CompleteRecordUnit) -> BearerAttemptResult:
        ...


def _actions(name: str, values: tuple[ImpairmentAction, ...]) -> tuple[ImpairmentAction, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple")
    if len(values) > MAX_BEARER_ATTEMPTS:
        raise BearerBoundsError(f"{name} exceeds {MAX_BEARER_ATTEMPTS} actions")
    if any(not isinstance(value, ImpairmentAction) for value in values):
        raise TypeError(f"{name} must contain ImpairmentAction values")
    return values


@dataclass(frozen=True, slots=True)
class ScriptedImpairmentPlan:
    left_to_right: tuple[ImpairmentAction, ...] = ()
    right_to_left: tuple[ImpairmentAction, ...] = ()
    default_left_to_right: ImpairmentAction = ImpairmentAction.DELIVER
    default_right_to_left: ImpairmentAction = ImpairmentAction.DELIVER

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "left_to_right",
            _actions("left_to_right", self.left_to_right),
        )
        object.__setattr__(
            self,
            "right_to_left",
            _actions("right_to_left", self.right_to_left),
        )
        if not isinstance(self.default_left_to_right, ImpairmentAction):
            raise TypeError("default_left_to_right must be ImpairmentAction")
        if not isinstance(self.default_right_to_left, ImpairmentAction):
            raise TypeError("default_right_to_left must be ImpairmentAction")


@dataclass(frozen=True, slots=True)
class BearerBudget:
    max_attempts: int = MAX_BEARER_ATTEMPTS
    max_trace_entries: int = MAX_BEARER_TRACE_ENTRIES

    def __post_init__(self) -> None:
        for name, value, maximum in (
            ("max_attempts", self.max_attempts, MAX_BEARER_ATTEMPTS),
            ("max_trace_entries", self.max_trace_entries, MAX_BEARER_TRACE_ENTRIES),
        ):
            if type(value) is not int or not 1 <= value <= maximum:
                raise BearerBoundsError(f"{name} must be between 1 and {maximum}")


@dataclass(frozen=True, slots=True)
class BearerTraceEntry:
    attempt: int
    direction: LinkDirection
    kind: str
    action: ImpairmentAction
    logical_bytes: int
    presentations: int
    sender_observed: bool


class ScriptedInMemoryLink:
    """Deterministic ephemeral B1 link with no clock, retry, or durable state."""

    def __init__(self, plan: ScriptedImpairmentPlan = ScriptedImpairmentPlan()) -> None:
        if not isinstance(plan, ScriptedImpairmentPlan):
            raise TypeError("plan must be ScriptedImpairmentPlan")
        self._plan = plan
        self._left_index = 0
        self._right_index = 0
        self._disconnected = False
        self._pending: CompleteRecordUnit | None = None
        self._queued_units_peak = 0

    @property
    def queued_units(self) -> int:
        return 0 if self._pending is None else 1

    @property
    def queued_units_peak(self) -> int:
        return self._queued_units_peak

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

    def attempt(self, unit: CompleteRecordUnit) -> BearerAttemptResult:
        if not isinstance(unit, CompleteRecordUnit):
            raise TypeError("unit must be CompleteRecordUnit")
        if self._disconnected:
            raise BearerContractError("link is already disconnected")
        action = self._next_action(unit.direction)
        if action is ImpairmentAction.DROP:
            return BearerAttemptResult(action, (), True)
        if action is ImpairmentAction.DISCONNECT:
            self._disconnected = True
            return BearerAttemptResult(action, (), False, disconnected=True)
        if action is ImpairmentAction.DUPLICATE:
            return BearerAttemptResult(action, (unit, unit), True)
        if action is ImpairmentAction.DELIVER_UNCERTAIN:
            return BearerAttemptResult(action, (unit,), False)
        if action is ImpairmentAction.DELAY_DELIVER:
            if self._pending is not None:
                raise BearerBoundsError("delay queue already contains a unit")
            self._pending = unit
            self._queued_units_peak = max(self._queued_units_peak, self.queued_units)
            delivered = self._pending
            self._pending = None
            return BearerAttemptResult(action, (delivered,), True, delayed=True)
        return BearerAttemptResult(action, (unit,), True)


@dataclass(frozen=True, slots=True)
class BearerContactReport:
    outcome: BearerContactOutcome
    records_considered: int
    records_skipped_already_known: int
    logical_records_attempted: int
    logical_bytes_attempted: int
    bearer_attempts: int
    delivered_presentations: int
    duplicate_presentations: int
    dropped_units: int
    delayed_units: int
    disconnects: int
    sender_uncertainties: int
    durable_records_committed: int
    durable_logical_bytes: int
    remaining_missing_work: int
    contact_items_remaining: int
    contact_bytes_remaining: int
    bearer_attempts_remaining: int
    trace_entries_remaining: int
    queued_units_peak: int
    state_changed_left: bool
    state_changed_right: bool
    error_code: str | None
    error_message: str | None
    trace: tuple[BearerTraceEntry, ...]
    accounting_model: str = EXPERIMENTAL_BEARER_ACCOUNTING_ONLY


_NATIVE_ERRORS = (
    CatalogBoundsError,
    PersistenceError,
    QueryConflictError,
    QueryResultBoundsError,
    ReferenceConflictError,
    ResultConflictError,
)


def _direction(item: _WorkItem) -> LinkDirection:
    if item.phase.value.endswith("LEFT_TO_RIGHT"):
        return LinkDirection.LEFT_TO_RIGHT
    return LinkDirection.RIGHT_TO_LEFT


def _record(item: _WorkItem) -> RecordValue:
    if item.kind == "query":
        assert isinstance(item.identity, bytes)
        return item.sender.query_results.get_query(item.identity)
    if item.kind == "result":
        assert isinstance(item.identity, ResultIdentity)
        return item.sender.query_results.get_result(item.identity)
    assert isinstance(item.identity, bytes)
    return item.sender.catalog.get(item.identity)


def _unit(item: _WorkItem) -> CompleteRecordUnit:
    return CompleteRecordUnit(
        direction=_direction(item),
        kind=item.kind,
        identity=item.identity,
        record=_record(item),
        logical_bytes=item.encoded_bytes,
    )


def _node_state(node: ContactNode) -> tuple[bytes, bytes]:
    return node.catalog.state_digest, node.query_results.state_digest


def _apply_presented_record(receiver: ContactNode, unit: CompleteRecordUnit) -> None:
    """Apply the exact complete record presented by the bearer via native stores."""

    if unit.kind == "query":
        assert isinstance(unit.record, QueryRecord)
        receiver.query_results.add_query(unit.record)
    elif unit.kind == "result":
        assert isinstance(unit.record, ResultRecord)
        receiver.query_results.add_result(unit.record)
    else:
        assert isinstance(unit.record, BoundedReference)
        receiver.catalog.add(unit.record)


def run_bearer_contact(
    left: ContactNode,
    right: ContactNode,
    *,
    bearer: CompleteRecordBearer,
    contact_budget: ContactBudget,
    bearer_budget: BearerBudget = BearerBudget(),
    selection: ContactSelection | None = None,
) -> BearerContactReport:
    """Run one bounded D4 work plan through a complete-record B1 bearer."""

    if not isinstance(left, ContactNode) or not isinstance(right, ContactNode):
        raise TypeError("left and right must be ContactNode")
    if not isinstance(bearer, CompleteRecordBearer):
        raise TypeError("bearer must implement CompleteRecordBearer")
    if not isinstance(contact_budget, ContactBudget):
        raise TypeError("contact_budget must be ContactBudget")
    if not isinstance(bearer_budget, BearerBudget):
        raise TypeError("bearer_budget must be BearerBudget")
    active_selection = ContactSelection() if selection is None else selection
    if not isinstance(active_selection, ContactSelection):
        raise TypeError("selection must be ContactSelection or None")

    left_before = _node_state(left)
    right_before = _node_state(right)
    plan = _work_plan(left, right, active_selection)
    remaining_missing = sum(item.missing for _, items in plan for item in items)
    considered = 0
    skipped = 0
    records_attempted = 0
    bytes_attempted = 0
    attempts = 0
    presentations = 0
    duplicate_presentations = 0
    drops = 0
    delays = 0
    disconnects = 0
    uncertainties = 0
    durable_commits = 0
    durable_bytes = 0
    trace: list[BearerTraceEntry] = []

    def finish(
        outcome: BearerContactOutcome,
        error: Exception | None = None,
    ) -> BearerContactReport:
        queued_peak = (
            bearer.queued_units_peak
            if isinstance(bearer, ScriptedInMemoryLink)
            else 0
        )
        return BearerContactReport(
            outcome=outcome,
            records_considered=considered,
            records_skipped_already_known=skipped,
            logical_records_attempted=records_attempted,
            logical_bytes_attempted=bytes_attempted,
            bearer_attempts=attempts,
            delivered_presentations=presentations,
            duplicate_presentations=duplicate_presentations,
            dropped_units=drops,
            delayed_units=delays,
            disconnects=disconnects,
            sender_uncertainties=uncertainties,
            durable_records_committed=durable_commits,
            durable_logical_bytes=durable_bytes,
            remaining_missing_work=remaining_missing,
            contact_items_remaining=contact_budget.max_items - records_attempted,
            contact_bytes_remaining=contact_budget.max_bytes - bytes_attempted,
            bearer_attempts_remaining=bearer_budget.max_attempts - attempts,
            trace_entries_remaining=bearer_budget.max_trace_entries - len(trace),
            queued_units_peak=queued_peak,
            state_changed_left=_node_state(left) != left_before,
            state_changed_right=_node_state(right) != right_before,
            error_code=None if error is None else _error_code(error),
            error_message=None if error is None else str(error),
            trace=tuple(trace),
        )

    for _, items in plan:
        for item in items:
            considered += 1
            if not item.missing:
                try:
                    _native_validate_known(item)
                except _NATIVE_ERRORS as error:
                    return finish(BearerContactOutcome.ERROR, error)
                skipped += 1
                continue

            if (
                records_attempted + 1 > contact_budget.max_items
                or bytes_attempted + item.encoded_bytes > contact_budget.max_bytes
            ):
                return finish(BearerContactOutcome.CONTACT_BUDGET_EXHAUSTED)
            if (
                attempts + 1 > bearer_budget.max_attempts
                or len(trace) + 1 > bearer_budget.max_trace_entries
            ):
                return finish(BearerContactOutcome.BEARER_BUDGET_EXHAUSTED)

            unit = _unit(item)
            records_attempted += 1
            bytes_attempted += unit.logical_bytes
            attempts += 1
            try:
                attempt = bearer.attempt(unit)
            except (BearerBoundsError, BearerContractError) as error:
                return finish(BearerContactOutcome.ERROR, error)
            if not isinstance(attempt, BearerAttemptResult):
                return finish(
                    BearerContactOutcome.ERROR,
                    BearerContractError("bearer returned an invalid attempt result"),
                )
            trace.append(
                BearerTraceEntry(
                    attempt=attempts,
                    direction=unit.direction,
                    kind=unit.kind,
                    action=attempt.action,
                    logical_bytes=unit.logical_bytes,
                    presentations=len(attempt.presentations),
                    sender_observed=attempt.sender_observed,
                )
            )
            if attempt.disconnected:
                disconnects += 1
                return finish(BearerContactOutcome.DISCONNECTED)
            if not attempt.presentations:
                drops += 1
                continue
            if any(delivered != unit for delivered in attempt.presentations):
                return finish(
                    BearerContactOutcome.ERROR,
                    BearerContractError("bearer changed or substituted a complete unit"),
                )

            receiver_before = _node_state(item.receiver)
            try:
                for delivered in attempt.presentations:
                    _apply_presented_record(item.receiver, delivered)
            except _NATIVE_ERRORS as error:
                return finish(BearerContactOutcome.ERROR, error)
            receiver_changed = _node_state(item.receiver) != receiver_before
            presentations += len(attempt.presentations)
            duplicate_presentations += max(0, len(attempt.presentations) - 1)
            delays += int(attempt.delayed)
            if receiver_changed:
                durable_commits += 1
                durable_bytes += unit.logical_bytes
                remaining_missing -= 1
            if not attempt.sender_observed:
                uncertainties += 1
                return finish(BearerContactOutcome.SENDER_UNCERTAIN)

    return finish(
        BearerContactOutcome.NO_MORE_ELIGIBLE_WORK
        if remaining_missing == 0
        else BearerContactOutcome.PARTIAL_NOT_DELIVERED
    )


__all__ = [
    "BearerAttemptResult",
    "BearerBoundsError",
    "BearerBudget",
    "BearerContactOutcome",
    "BearerContactReport",
    "BearerContractError",
    "BearerTraceEntry",
    "CompleteRecordBearer",
    "CompleteRecordUnit",
    "EXPERIMENTAL_BEARER_ACCOUNTING_ONLY",
    "ImpairmentAction",
    "LinkDirection",
    "MAX_BEARER_ATTEMPTS",
    "MAX_BEARER_TRACE_ENTRIES",
    "MAX_PRESENTATIONS_PER_ATTEMPT",
    "MAX_QUEUED_UNITS",
    "ScriptedImpairmentPlan",
    "ScriptedInMemoryLink",
    "run_bearer_contact",
]
