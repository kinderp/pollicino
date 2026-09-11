from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Sequence

from .bearer import LinkDirection
from .catalog import BoundedReferenceCatalog
from .compact_reconciliation import (
    CompactContactOutcome,
    CompactContactReport,
    CompactIndependentEndpoint,
    MAX_COMPACT_CAPACITY,
    run_compact_contact,
)
from .endpoint import (
    B2ContactBudget,
    B2ContactOutcome,
    B2BoundsError,
    EncodedBearerAttemptResult,
    EncodedMessageBearer,
    MAX_B2_IDENTITIES_PER_MESSAGE,
    MAX_B2_MESSAGE_BYTES,
    RecordKind,
    RecordMessage,
    decode_message,
)
from .fair_reconciliation import (
    FairContactReport,
    FairContactSelection,
    FairIndependentEndpoint,
    MAX_B2F_DESCRIPTORS_PER_MESSAGE,
    MAX_B2F_MESSAGE_BYTES,
    run_fair_contact,
)
from .query import QueryResultStore


EXPERIMENTAL_B2A_POLICY = "pollicino.experimental-b2a.v1"
EXPERIMENTAL_B2A_ACCOUNTING_ONLY = "EXPERIMENTAL_B2A_ACCOUNTING_ONLY"
DEFAULT_SELECTED_CAPACITIES = (10,)
DEFAULT_MAX_COMPACT_PROBES = 1
DEFAULT_MAX_COMPACT_CONTROL_BYTES = 5_000
DEFAULT_MAX_SUMMARY_BYTES = 5_000
DEFAULT_EXACT_PROGRESS_RESERVE_ATTEMPTS = 8
DEFAULT_LARGE_STATE_THRESHOLD = 5_000


class AdaptivePolicyKind(str, Enum):
    EXACT_ALWAYS = "EXACT_ALWAYS"
    FIXED_COMPACT_THEN_EXACT = "FIXED_COMPACT_THEN_EXACT"
    BOUNDED_ESCALATION = "BOUNDED_ESCALATION"
    COST_AWARE_ESCALATION = "COST_AWARE_ESCALATION"


class AdaptiveOutcome(str, Enum):
    COMPACT_EQUAL = "COMPACT_EQUAL"
    COMPACT_PROGRESS = "COMPACT_PROGRESS"
    EXACT_PROGRESS = "EXACT_PROGRESS"
    PARTIAL = "PARTIAL"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    DISCONNECTED = "DISCONNECTED"
    SENDER_UNCERTAIN = "SENDER_UNCERTAIN"
    ERROR = "ERROR"


class AdaptiveBudgetExhausted(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AdaptivePolicy:
    kind: AdaptivePolicyKind
    capacities: tuple[int, ...] = ()
    max_compact_probes: int = DEFAULT_MAX_COMPACT_PROBES
    max_compact_control_bytes: int = DEFAULT_MAX_COMPACT_CONTROL_BYTES
    max_summary_bytes: int = DEFAULT_MAX_SUMMARY_BYTES
    exact_progress_reserve_attempts: int = DEFAULT_EXACT_PROGRESS_RESERVE_ATTEMPTS
    large_state_threshold: int = DEFAULT_LARGE_STATE_THRESHOLD
    exact_fallback: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.kind, AdaptivePolicyKind):
            raise TypeError("kind must be AdaptivePolicyKind")
        if len(self.capacities) > 4 or any(
            type(value) is not int or not 1 <= value <= MAX_COMPACT_CAPACITY
            for value in self.capacities
        ):
            raise B2BoundsError("adaptive capacity ladder is outside bounds")
        if tuple(sorted(set(self.capacities))) != self.capacities:
            raise B2BoundsError("adaptive capacities must be unique and increasing")
        if self.kind is AdaptivePolicyKind.EXACT_ALWAYS and self.capacities:
            raise B2BoundsError("exact-only policy cannot have compact capacities")
        if self.kind is not AdaptivePolicyKind.EXACT_ALWAYS and not self.capacities:
            raise B2BoundsError("compact policy requires at least one capacity")
        if self.kind is AdaptivePolicyKind.FIXED_COMPACT_THEN_EXACT and len(self.capacities) != 1:
            raise B2BoundsError("fixed compact policy requires one capacity")
        if type(self.max_compact_probes) is not int or not 0 <= self.max_compact_probes <= 4:
            raise B2BoundsError("max compact probes is outside bounds")
        for name in (
            "max_compact_control_bytes",
            "max_summary_bytes",
            "exact_progress_reserve_attempts",
            "large_state_threshold",
        ):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise B2BoundsError(f"{name} must be positive")
        if type(self.exact_fallback) is not bool:
            raise TypeError("exact_fallback must be bool")

    @classmethod
    def exact_always(cls) -> AdaptivePolicy:
        return cls(AdaptivePolicyKind.EXACT_ALWAYS, (), max_compact_probes=0)

    @classmethod
    def fixed(cls, capacity: int) -> AdaptivePolicy:
        return cls(
            AdaptivePolicyKind.FIXED_COMPACT_THEN_EXACT,
            (capacity,),
            max_compact_probes=1,
            max_compact_control_bytes=MAX_B2_MESSAGE_BYTES,
            max_summary_bytes=MAX_B2_MESSAGE_BYTES,
        )

    @classmethod
    def escalating(cls, capacities: Sequence[int]) -> AdaptivePolicy:
        values = tuple(capacities)
        return cls(
            AdaptivePolicyKind.BOUNDED_ESCALATION,
            values,
            max_compact_probes=len(values),
            max_compact_control_bytes=4 * MAX_B2_MESSAGE_BYTES,
            max_summary_bytes=MAX_B2_MESSAGE_BYTES,
        )

    @classmethod
    def selected_cost_aware(cls) -> AdaptivePolicy:
        return cls(AdaptivePolicyKind.COST_AWARE_ESCALATION, DEFAULT_SELECTED_CAPACITIES)


class AdaptiveIndependentEndpoint:
    """Local-only views of the unchanged compact and exact endpoint layers."""

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
        self.compact = CompactIndependentEndpoint(catalog, query_results)
        self.exact = FairIndependentEndpoint(catalog, query_results, diagnostic_label)

    def local_cardinality(
        self, kind: RecordKind, selected_references: Sequence[bytes] = ()
    ) -> int:
        return len(self.compact.local_identities(kind, selected_references))

    def compact_summary_bytes(
        self,
        kind: RecordKind,
        capacity: int,
        selected_references: Sequence[bytes] = (),
    ) -> int:
        return len(self.compact.summary_message(kind, capacity, selected_references))

    def exact_control_upper_bound(
        self, kind: RecordKind, selected_references: Sequence[bytes] = ()
    ) -> int:
        count = self.local_cardinality(kind, selected_references)
        pages = math.ceil(count / MAX_B2_IDENTITIES_PER_MESSAGE)
        directory_messages = max(1, math.ceil(pages / MAX_B2F_DESCRIPTORS_PER_MESSAGE))
        # Deployable, deliberately conservative: local directory/page-request
        # envelopes plus one maximum advertisement and request per local page.
        return (
            2 * directory_messages * MAX_B2F_MESSAGE_BYTES
            + 2 * pages * MAX_B2_MESSAGE_BYTES
        )


class _BudgetedBearer:
    def __init__(self, bearer: EncodedMessageBearer, budget: B2ContactBudget) -> None:
        if not isinstance(bearer, EncodedMessageBearer):
            raise TypeError("bearer must implement EncodedMessageBearer")
        self.bearer = bearer
        self.budget = budget
        self.control_messages = 0
        self.control_bytes = 0
        self.record_messages = 0
        self.record_bytes = 0
        self.attempts = 0
        self.exhausted_reason: str | None = None

    def _is_record(self, encoded: bytes) -> bool:
        if encoded[:4] != b"PB2E":
            return False
        return isinstance(decode_message(encoded), RecordMessage)

    def attempt(
        self, direction: LinkDirection, encoded: bytes
    ) -> EncodedBearerAttemptResult:
        is_record = self._is_record(encoded)
        prefix = "record" if is_record else "control"
        messages = getattr(self, f"{prefix}_messages")
        octets = getattr(self, f"{prefix}_bytes")
        max_messages = getattr(self.budget, f"max_{prefix}_messages")
        max_octets = getattr(self.budget, f"max_{prefix}_bytes")
        if self.attempts + 1 > self.budget.max_bearer_attempts:
            self.exhausted_reason = "BEARER_ATTEMPTS"
        elif messages + 1 > max_messages:
            self.exhausted_reason = f"{prefix.upper()}_MESSAGES"
        elif octets + len(encoded) > max_octets:
            self.exhausted_reason = f"{prefix.upper()}_BYTES"
        if self.exhausted_reason is not None:
            raise AdaptiveBudgetExhausted(self.exhausted_reason)
        setattr(self, f"{prefix}_messages", messages + 1)
        setattr(self, f"{prefix}_bytes", octets + len(encoded))
        self.attempts += 1
        return self.bearer.attempt(direction, encoded)

    def remaining_budget(self) -> B2ContactBudget | None:
        values = {
            "max_control_messages": self.budget.max_control_messages - self.control_messages,
            "max_control_bytes": self.budget.max_control_bytes - self.control_bytes,
            "max_record_messages": self.budget.max_record_messages - self.record_messages,
            "max_record_bytes": self.budget.max_record_bytes - self.record_bytes,
            "max_record_logical_bytes": self.budget.max_record_logical_bytes,
            "max_bearer_attempts": self.budget.max_bearer_attempts - self.attempts,
            "max_trace_entries": self.budget.max_trace_entries - self.attempts,
        }
        if any(value < 1 for value in values.values()):
            return None
        return B2ContactBudget(**values)


@dataclass(frozen=True, slots=True)
class AdaptiveDecision:
    action: str
    capacity: int | None
    reason: str
    estimated_exact_upper_bytes: int
    compact_bytes_spent: int


@dataclass(frozen=True, slots=True)
class AdaptiveContactReport:
    outcome: AdaptiveOutcome
    policy_kind: AdaptivePolicyKind
    capacities_attempted: tuple[int, ...]
    compact_reports: tuple[CompactContactReport, ...]
    exact_report: FairContactReport | None
    decisions: tuple[AdaptiveDecision, ...]
    control_messages: int
    control_bytes: int
    record_messages: int
    record_bytes: int
    bearer_attempts: int
    durable_commits: int
    exact_fallback_triggered: bool
    largest_summary_bytes: int
    b2_ceiling_margin: int
    budget_exhausted_reason: str | None
    accounting_model: str = EXPERIMENTAL_B2A_ACCOUNTING_ONLY

    @property
    def compact_control_bytes(self) -> int:
        return sum(report.control_bytes for report in self.compact_reports)

    @property
    def exact_control_bytes(self) -> int:
        return 0 if self.exact_report is None else self.exact_report.control_bytes_encoded

    @property
    def exact_identities_disclosed(self) -> int:
        return sum(
            report.exact_identities_disclosed for report in self.compact_reports
        ) + (0 if self.exact_report is None else self.exact_report.identities_disclosed)

    @property
    def short_fingerprints_disclosed(self) -> int:
        return sum(
            report.short_fingerprints_disclosed for report in self.compact_reports
        )

    @property
    def estimated_exact_upper_bytes(self) -> int:
        return self.decisions[0].estimated_exact_upper_bytes if self.decisions else 0


def _mapped_outcome(
    compact: CompactContactReport | None,
    exact: FairContactReport | None,
    budgeted: _BudgetedBearer,
) -> AdaptiveOutcome:
    if budgeted.exhausted_reason is not None:
        return AdaptiveOutcome.BUDGET_EXHAUSTED
    if exact is not None:
        if exact.outcome is B2ContactOutcome.ERROR:
            return AdaptiveOutcome.ERROR
        if exact.outcome is B2ContactOutcome.BUDGET_EXHAUSTED:
            return AdaptiveOutcome.BUDGET_EXHAUSTED
        if exact.outcome is B2ContactOutcome.DISCONNECTED:
            return AdaptiveOutcome.DISCONNECTED
        if exact.outcome is B2ContactOutcome.SENDER_UNCERTAIN:
            return AdaptiveOutcome.SENDER_UNCERTAIN
        if exact.outcome is B2ContactOutcome.PARTIAL_NOT_DELIVERED:
            return AdaptiveOutcome.PARTIAL
        return AdaptiveOutcome.EXACT_PROGRESS
    assert compact is not None
    if compact.outcome is CompactContactOutcome.EQUAL:
        return AdaptiveOutcome.COMPACT_EQUAL
    if compact.outcome is CompactContactOutcome.DISCOVERED:
        return AdaptiveOutcome.COMPACT_PROGRESS
    if compact.outcome is CompactContactOutcome.BUDGET_EXHAUSTED:
        return AdaptiveOutcome.BUDGET_EXHAUSTED
    if compact.outcome is CompactContactOutcome.DISCONNECTED:
        return AdaptiveOutcome.DISCONNECTED
    if compact.outcome is CompactContactOutcome.SENDER_UNCERTAIN:
        return AdaptiveOutcome.SENDER_UNCERTAIN
    if compact.outcome is CompactContactOutcome.ERROR:
        return AdaptiveOutcome.ERROR
    return AdaptiveOutcome.PARTIAL


def run_adaptive_contact(
    source: AdaptiveIndependentEndpoint,
    receiver: AdaptiveIndependentEndpoint,
    *,
    kind: RecordKind,
    bearer: EncodedMessageBearer,
    policy: AdaptivePolicy,
    budget: B2ContactBudget = B2ContactBudget(),
    selected_references: Sequence[bytes] = (),
) -> AdaptiveContactReport:
    """Run one finite oracle-blind policy over unchanged B2C/B2F paths."""

    if not isinstance(source, AdaptiveIndependentEndpoint) or not isinstance(
        receiver, AdaptiveIndependentEndpoint
    ):
        raise TypeError("source and receiver must be adaptive endpoints")
    if not isinstance(kind, RecordKind):
        raise TypeError("kind must be RecordKind")
    if not isinstance(policy, AdaptivePolicy):
        raise TypeError("policy must be AdaptivePolicy")
    if not isinstance(budget, B2ContactBudget):
        raise TypeError("budget must be B2ContactBudget")

    budgeted = _BudgetedBearer(bearer, budget)
    estimate = source.exact_control_upper_bound(kind, selected_references)
    local_count = source.local_cardinality(kind, selected_references)
    compact_reports: list[CompactContactReport] = []
    decisions: list[AdaptiveDecision] = []
    capacities_attempted: list[int] = []
    compact_spent = 0
    largest_summary = 0
    active_compact: CompactContactReport | None = None
    exact_report: FairContactReport | None = None

    for capacity in policy.capacities:
        if len(capacities_attempted) >= policy.max_compact_probes:
            decisions.append(AdaptiveDecision("EXACT", None, "PROBE_LIMIT", estimate, compact_spent))
            break
        summary_bytes = source.compact_summary_bytes(kind, capacity, selected_references)
        largest_summary = max(largest_summary, summary_bytes)
        if policy.kind is AdaptivePolicyKind.COST_AWARE_ESCALATION:
            if compact_spent + summary_bytes >= estimate:
                decisions.append(AdaptiveDecision("EXACT", None, "EXACT_COST_BOUND", estimate, compact_spent))
                break
            if capacity > 10 and local_count < policy.large_state_threshold:
                decisions.append(AdaptiveDecision("EXACT", None, "LOCAL_SCALE", estimate, compact_spent))
                break
            if summary_bytes > policy.max_summary_bytes:
                decisions.append(AdaptiveDecision("EXACT", None, "SUMMARY_PRESSURE", estimate, compact_spent))
                break
            if compact_spent + summary_bytes > policy.max_compact_control_bytes:
                decisions.append(AdaptiveDecision("EXACT", None, "COMPACT_BYTE_LIMIT", estimate, compact_spent))
                break
            remaining_attempts = budget.max_bearer_attempts - budgeted.attempts
            if remaining_attempts <= policy.exact_progress_reserve_attempts + 1:
                decisions.append(AdaptiveDecision("EXACT", None, "EXACT_RESERVE", estimate, compact_spent))
                break
        if budgeted.control_bytes + summary_bytes > budget.max_control_bytes:
            decisions.append(AdaptiveDecision("EXACT", None, "CONTACT_CONTROL_BUDGET", estimate, compact_spent))
            break
        remaining_attempts = budget.max_bearer_attempts - budgeted.attempts
        if remaining_attempts < 1:
            break
        decisions.append(AdaptiveDecision("COMPACT", capacity, "PROBE", estimate, compact_spent))
        capacities_attempted.append(capacity)
        active_compact = run_compact_contact(
            source.compact,
            receiver.compact,
            kind=kind,
            capacity=capacity,
            bearer=budgeted,
            selected_references=selected_references,
            max_attempts=min(remaining_attempts, 100),
        )
        compact_reports.append(active_compact)
        compact_spent = budgeted.control_bytes
        if active_compact.outcome is CompactContactOutcome.FALLBACK_REQUIRED:
            continue
        return AdaptiveContactReport(
            _mapped_outcome(active_compact, None, budgeted),
            policy.kind,
            tuple(capacities_attempted),
            tuple(compact_reports),
            None,
            tuple(decisions),
            budgeted.control_messages,
            budgeted.control_bytes,
            budgeted.record_messages,
            budgeted.record_bytes,
            budgeted.attempts,
            sum(report.durable_commits for report in compact_reports),
            False,
            largest_summary,
            MAX_B2_MESSAGE_BYTES - largest_summary,
            budgeted.exhausted_reason,
        )

    if policy.exact_fallback:
        remaining = budgeted.remaining_budget()
        if remaining is not None:
            reason = (
                "EXACT_ALWAYS"
                if policy.kind is AdaptivePolicyKind.EXACT_ALWAYS
                else "FALLBACK"
            )
            decisions.append(AdaptiveDecision("EXACT", None, reason, estimate, compact_spent))
            selection = FairContactSelection(
                right_wants_from_left=tuple(selected_references)
                if kind is RecordKind.REFERENCE
                else ()
            )
            exact_report = run_fair_contact(
                source.exact,
                receiver.exact,
                bearer=budgeted,
                budget=remaining,
                selection=selection,
            )
    outcome = _mapped_outcome(active_compact, exact_report, budgeted) if (
        active_compact is not None or exact_report is not None
    ) else AdaptiveOutcome.BUDGET_EXHAUSTED
    return AdaptiveContactReport(
        outcome,
        policy.kind,
        tuple(capacities_attempted),
        tuple(compact_reports),
        exact_report,
        tuple(decisions),
        budgeted.control_messages,
        budgeted.control_bytes,
        budgeted.record_messages,
        budgeted.record_bytes,
        budgeted.attempts,
        sum(report.durable_commits for report in compact_reports)
        + (0 if exact_report is None else exact_report.durable_commits),
        exact_report is not None and policy.kind is not AdaptivePolicyKind.EXACT_ALWAYS,
        largest_summary,
        MAX_B2_MESSAGE_BYTES - largest_summary,
        budgeted.exhausted_reason,
    )


__all__ = [
    "AdaptiveContactReport",
    "AdaptiveDecision",
    "AdaptiveIndependentEndpoint",
    "AdaptiveOutcome",
    "AdaptivePolicy",
    "AdaptivePolicyKind",
    "DEFAULT_SELECTED_CAPACITIES",
    "EXPERIMENTAL_B2A_ACCOUNTING_ONLY",
    "EXPERIMENTAL_B2A_POLICY",
    "run_adaptive_contact",
]
