from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol


RICH_CHEAP_FEATURE_VERSION = "rich-cheap-v1"
RICH_CHEAP_FEATURE_NAMES = (
    "probe_code_bits_ceil",
    "unique_count",
    "max_hist_count",
    "transition_count",
    "distinct_transition_count",
    "longest_run",
    "surprise_sum_ceil",
    "surprise_max_ceil",
    "surprise_range_ceil",
    "surprise_variance_proxy",
    "surprise_early_minus_late",
    "very_surprising_count",
)


def integer_codelength_bounds(numerator: int, denominator: int) -> tuple[int, int]:
    """Return floor/ceil(-log2(numerator / denominator)) exactly."""
    if numerator <= 0 or denominator <= 0 or numerator > denominator:
        raise ValueError("invalid likelihood ratio")
    floor_bits = max(0, denominator.bit_length() - numerator.bit_length())
    while floor_bits > 0 and (numerator << floor_bits) > denominator:
        floor_bits -= 1
    while (numerator << (floor_bits + 1)) <= denominator:
        floor_bits += 1
    exact = (numerator << floor_bits) == denominator
    return floor_bits, floor_bits if exact else floor_bits + 1


@dataclass(frozen=True)
class CheapAdmissionFeatures:
    """Exact bounded cheap-only features observed over one block probe."""

    probe_code_bits_floor: int
    probe_code_bits_ceil: int
    unique_count: int
    max_hist_count: int
    transition_count: int
    distinct_transition_count: int
    longest_run: int
    surprise_sum_ceil: int
    surprise_max_ceil: int
    surprise_range_ceil: int
    surprise_variance_proxy: int
    surprise_early_minus_late: int
    very_surprising_count: int

    def value(self, name: str) -> int:
        if name not in RICH_CHEAP_FEATURE_NAMES:
            raise ValueError(f"unknown rich-cheap feature: {name}")
        return int(getattr(self, name))

    def as_dict(self) -> dict[str, int]:
        return {
            "probe_code_bits_floor": self.probe_code_bits_floor,
            **{name: self.value(name) for name in RICH_CHEAP_FEATURE_NAMES},
        }


class CheapAdmissionFeatureAccumulator:
    """Accumulate rich features from CDFs already produced by cheap coding."""

    def __init__(
        self,
        probe_bytes: int,
        *,
        very_surprising_bits: int = 9,
        required_features: Sequence[str] | None = None,
    ) -> None:
        if probe_bytes <= 0:
            raise ValueError("probe_bytes must be positive")
        if very_surprising_bits < 0:
            raise ValueError("very_surprising_bits must be non-negative")
        self.probe_bytes = int(probe_bytes)
        self.very_surprising_bits = int(very_surprising_bits)
        self.required_features = frozenset(
            RICH_CHEAP_FEATURE_NAMES if required_features is None else required_features
        )
        unknown = self.required_features.difference(RICH_CHEAP_FEATURE_NAMES)
        if unknown:
            raise ValueError(f"unknown rich-cheap features: {sorted(unknown)}")
        self._need_codelength = "probe_code_bits_ceil" in self.required_features
        self._need_histogram = bool(
            self.required_features.intersection(("unique_count", "max_hist_count"))
        )
        self._need_adjacency = bool(
            self.required_features.intersection(
                ("transition_count", "distinct_transition_count", "longest_run")
            )
        )
        self._need_surprise = bool(
            self.required_features.intersection(
                (
                    "surprise_sum_ceil",
                    "surprise_max_ceil",
                    "surprise_range_ceil",
                    "surprise_variance_proxy",
                    "surprise_early_minus_late",
                    "very_surprising_count",
                )
            )
        )
        self._observed = 0
        self._likelihood_num = 1
        self._likelihood_den = 1
        self._histogram: dict[int, int] = {}
        self._transitions: set[tuple[int, int]] = set()
        self._surprises: list[int] = []
        self._previous: int | None = None
        self._adjacent_changes = 0
        self._current_run = 0
        self._longest_run = 0

    @staticmethod
    def _term(cdf: Sequence[int], symbol: int) -> tuple[int, int]:
        if not 0 <= symbol < len(cdf) - 1:
            raise ValueError("symbol outside provider alphabet")
        numerator = int(cdf[symbol + 1]) - int(cdf[symbol])
        denominator = int(cdf[-1])
        if numerator <= 0 or denominator <= 0 or numerator > denominator:
            raise ValueError("provider returned an invalid CDF")
        return numerator, denominator

    def observe(self, cdf: Sequence[int], symbol: int) -> None:
        if self._observed >= self.probe_bytes:
            raise ValueError("feature accumulator received bytes beyond its probe")
        symbol = int(symbol)
        if self._need_codelength or self._need_surprise:
            numerator, denominator = self._term(cdf, symbol)
        if self._need_codelength:
            self._likelihood_num *= numerator
            self._likelihood_den *= denominator
        if self._need_surprise:
            _, surprise_ceil = integer_codelength_bounds(numerator, denominator)
            self._surprises.append(surprise_ceil)
        if self._need_histogram:
            self._histogram[symbol] = self._histogram.get(symbol, 0) + 1
        if self._need_adjacency:
            if self._previous is None:
                self._current_run = 1
            elif symbol == self._previous:
                if "distinct_transition_count" in self.required_features:
                    self._transitions.add((self._previous, symbol))
                self._current_run += 1
            else:
                if "distinct_transition_count" in self.required_features:
                    self._transitions.add((self._previous, symbol))
                self._adjacent_changes += 1
                self._current_run = 1
            self._longest_run = max(self._longest_run, self._current_run)
            self._previous = symbol
        self._observed += 1

    def features(self) -> CheapAdmissionFeatures:
        if self._observed != self.probe_bytes:
            raise RuntimeError("cheap admission features requested before probe completion")
        floor_bits, ceil_bits = (
            integer_codelength_bounds(self._likelihood_num, self._likelihood_den)
            if self._need_codelength
            else (0, 0)
        )
        surprise_sum = (
            sum(self._surprises)
            if self.required_features.intersection(
                ("surprise_sum_ceil", "surprise_variance_proxy")
            )
            else 0
        )
        surprise_sq_sum = (
            sum(value * value for value in self._surprises)
            if "surprise_variance_proxy" in self.required_features
            else 0
        )
        half = self.probe_bytes // 2
        early_late = (
            sum(self._surprises[:half]) - sum(self._surprises[half:])
            if self._need_surprise
            else 0
        )
        return CheapAdmissionFeatures(
            probe_code_bits_floor=floor_bits,
            probe_code_bits_ceil=ceil_bits,
            unique_count=len(self._histogram) if "unique_count" in self.required_features else 0,
            max_hist_count=(
                max(self._histogram.values())
                if "max_hist_count" in self.required_features
                else 0
            ),
            transition_count=(
                self._adjacent_changes
                if "transition_count" in self.required_features
                else 0
            ),
            distinct_transition_count=(
                len(self._transitions)
                if "distinct_transition_count" in self.required_features
                else 0
            ),
            longest_run=(
                self._longest_run if "longest_run" in self.required_features else 0
            ),
            surprise_sum_ceil=(
                surprise_sum if "surprise_sum_ceil" in self.required_features else 0
            ),
            surprise_max_ceil=(
                max(self._surprises)
                if "surprise_max_ceil" in self.required_features
                else 0
            ),
            surprise_range_ceil=(
                max(self._surprises) - min(self._surprises)
                if "surprise_range_ceil" in self.required_features
                else 0
            ),
            surprise_variance_proxy=(
                self.probe_bytes * surprise_sq_sum - surprise_sum**2
                if "surprise_variance_proxy" in self.required_features
                else 0
            ),
            surprise_early_minus_late=(
                early_late
                if "surprise_early_minus_late" in self.required_features
                else 0
            ),
            very_surprising_count=(
                sum(value >= self.very_surprising_bits for value in self._surprises)
                if "very_surprising_count" in self.required_features
                else 0
            ),
        )


@dataclass(frozen=True)
class AdmissionBudgetState:
    admitted_bytes: int
    max_admitted_bytes: int


@dataclass(frozen=True)
class CheapAdmissionDecision:
    score: int
    threshold: int
    rule_match: bool
    budget_allows: bool
    admitted: bool


class IntegerAdmissionRule(Protocol):
    threshold: int

    def score(self, features: CheapAdmissionFeatures) -> int: ...

    def to_dict(self) -> dict: ...


@dataclass(frozen=True)
class QuantizedLinearAdmissionRule:
    feature_names: tuple[str, ...]
    weights: tuple[int, ...]
    bias: int
    threshold: int

    def __post_init__(self) -> None:
        if not self.feature_names or len(self.feature_names) != len(self.weights):
            raise ValueError("linear rule needs equally sized non-empty names and weights")
        if len(set(self.feature_names)) != len(self.feature_names):
            raise ValueError("linear rule feature names must be unique")
        for name in self.feature_names:
            if name not in RICH_CHEAP_FEATURE_NAMES:
                raise ValueError(f"unknown rich-cheap feature: {name}")

    def score(self, features: CheapAdmissionFeatures) -> int:
        return int(self.bias) + sum(
            int(weight) * features.value(name)
            for name, weight in zip(self.feature_names, self.weights, strict=True)
        )

    def to_dict(self) -> dict:
        return {
            "type": "quantized-linear",
            "feature_names": list(self.feature_names),
            "weights": list(self.weights),
            "bias": int(self.bias),
            "threshold": int(self.threshold),
        }


@dataclass(frozen=True)
class DecisionTreeNode:
    feature: str | None = None
    threshold: int | None = None
    less_equal: int | None = None
    greater: int | None = None
    value: int | None = None

    def __post_init__(self) -> None:
        is_leaf = self.value is not None
        if is_leaf:
            if any(item is not None for item in (self.feature, self.threshold, self.less_equal, self.greater)):
                raise ValueError("tree leaf cannot contain split fields")
        elif (
            self.feature not in RICH_CHEAP_FEATURE_NAMES
            or self.threshold is None
            or self.less_equal is None
            or self.greater is None
        ):
            raise ValueError("tree split is incomplete or names an unknown feature")

    def to_dict(self) -> dict:
        if self.value is not None:
            return {"value": int(self.value)}
        return {
            "feature": self.feature,
            "threshold": int(self.threshold),
            "less_equal": int(self.less_equal),
            "greater": int(self.greater),
        }


@dataclass(frozen=True)
class CheapAdmissionDecisionTree:
    nodes: tuple[DecisionTreeNode, ...]
    threshold: int

    def __post_init__(self) -> None:
        if not self.nodes:
            raise ValueError("tree rule needs at least one node")
        for node in self.nodes:
            for child in (node.less_equal, node.greater):
                if child is not None and not 0 <= child < len(self.nodes):
                    raise ValueError("tree child index is outside node array")
        self._validate_depth()

    def _validate_depth(self) -> None:
        stack = [(0, 0)]
        seen: set[int] = set()
        while stack:
            index, depth = stack.pop()
            if index in seen:
                raise ValueError("tree contains a cycle or shared node")
            seen.add(index)
            if depth > 3:
                raise ValueError("rich-cheap decision tree depth exceeds 3")
            node = self.nodes[index]
            if node.value is None:
                assert node.less_equal is not None and node.greater is not None
                stack.extend(((node.less_equal, depth + 1), (node.greater, depth + 1)))

    def score(self, features: CheapAdmissionFeatures) -> int:
        index = 0
        while True:
            node = self.nodes[index]
            if node.value is not None:
                return int(node.value)
            assert node.feature is not None and node.threshold is not None
            assert node.less_equal is not None and node.greater is not None
            index = (
                node.less_equal
                if features.value(node.feature) <= node.threshold
                else node.greater
            )

    def to_dict(self) -> dict:
        return {
            "type": "decision-tree",
            "threshold": int(self.threshold),
            "nodes": [node.to_dict() for node in self.nodes],
        }


def admission_rule_from_dict(payload: dict) -> IntegerAdmissionRule:
    kind = payload.get("type")
    if kind == "quantized-linear":
        return QuantizedLinearAdmissionRule(
            feature_names=tuple(str(name) for name in payload["feature_names"]),
            weights=tuple(int(value) for value in payload["weights"]),
            bias=int(payload["bias"]),
            threshold=int(payload["threshold"]),
        )
    if kind == "decision-tree":
        nodes = []
        for raw in payload["nodes"]:
            nodes.append(
                DecisionTreeNode(value=int(raw["value"]))
                if "value" in raw
                else DecisionTreeNode(
                    feature=str(raw["feature"]),
                    threshold=int(raw["threshold"]),
                    less_equal=int(raw["less_equal"]),
                    greater=int(raw["greater"]),
                )
            )
        return CheapAdmissionDecisionTree(tuple(nodes), threshold=int(payload["threshold"]))
    raise ValueError(f"unknown admission rule type: {kind!r}")


def integer_admission_rule_feature_names(rule: IntegerAdmissionRule) -> tuple[str, ...]:
    if isinstance(rule, QuantizedLinearAdmissionRule):
        return rule.feature_names
    if isinstance(rule, CheapAdmissionDecisionTree):
        used = {node.feature for node in rule.nodes if node.feature is not None}
        return tuple(name for name in RICH_CHEAP_FEATURE_NAMES if name in used)
    raise TypeError(f"unsupported integer admission rule: {type(rule)!r}")


def rich_cheap_admission_decision(
    features: CheapAdmissionFeatures,
    rule: IntegerAdmissionRule,
    budget: AdmissionBudgetState,
    block_bytes: int,
) -> CheapAdmissionDecision:
    """The single authoritative integer admission decision used everywhere."""
    if block_bytes < 0 or budget.admitted_bytes < 0 or budget.max_admitted_bytes < 0:
        raise ValueError("admission byte counts must be non-negative")
    score = int(rule.score(features))
    rule_match = score >= int(rule.threshold)
    budget_allows = budget.admitted_bytes + block_bytes <= budget.max_admitted_bytes
    return CheapAdmissionDecision(
        score=score,
        threshold=int(rule.threshold),
        rule_match=rule_match,
        budget_allows=budget_allows,
        admitted=rule_match and budget_allows,
    )


def extract_cheap_admission_features(
    cheap_factory: Callable[[], object], probe: bytes | Sequence[int]
) -> CheapAdmissionFeatures:
    """Extract the deployed feature vector from an already-consumed probe."""
    values = [int(value) for value in probe]
    accumulator = CheapAdmissionFeatureAccumulator(len(values))
    provider = cheap_factory()
    prefix: list[int] = []
    for index, symbol in enumerate(values):
        cdf = provider(index, prefix)
        accumulator.observe(cdf, symbol)
        prefix.append(symbol)
    return accumulator.features()


class RichCheapAdmissionBlockCDFProvider:
    """Gate a block-local specialist with rich deterministic cheap-only evidence."""

    def __init__(
        self,
        cheap_factory: Callable[[], object],
        specialist_factory: Callable[[], object] | None,
        rule: IntegerAdmissionRule,
        *,
        stream_bytes: int,
        block_bytes: int,
        probe_bytes: int,
        max_admitted_bytes: int | None = None,
        cheap_name: str = "cheap",
        specialist_name: str = "specialist",
    ) -> None:
        if stream_bytes < 0:
            raise ValueError("stream_bytes must be non-negative")
        if block_bytes <= 0:
            raise ValueError("block_bytes must be positive")
        if probe_bytes <= 0 or probe_bytes >= block_bytes:
            raise ValueError("probe_bytes must be in [1, block_bytes)")
        if max_admitted_bytes is not None and not 0 <= max_admitted_bytes <= stream_bytes:
            raise ValueError("max_admitted_bytes must be within the stream")
        if not cheap_name or not specialist_name or cheap_name == specialist_name:
            raise ValueError("route names must be distinct non-empty strings")

        self.cheap_factory = cheap_factory
        self.specialist_factory = specialist_factory
        self.rule = rule
        self.feature_names = integer_admission_rule_feature_names(rule)
        self.stream_bytes = int(stream_bytes)
        self.block_bytes = int(block_bytes)
        self.probe_bytes = int(probe_bytes)
        self.max_admitted_bytes = (
            self.stream_bytes if max_admitted_bytes is None else int(max_admitted_bytes)
        )
        self.cheap_name = str(cheap_name)
        self.specialist_name = str(specialist_name)

        self._block_index: int | None = None
        self._block_start = 0
        self._cheap = None
        self._specialist = None
        self._probe_seen: list[int] = []
        self._last_probe_cdf: Sequence[int] | None = None
        self._features = CheapAdmissionFeatureAccumulator(
            self.probe_bytes, required_features=self.feature_names
        )
        self._decision: CheapAdmissionDecision | None = None
        self._admitted_bytes = 0
        self._completed: list[dict] = []
        self._last_prefix: list[int] = []
        self.specialist_output_calls = 0

    def _block_length(self, block_index: int) -> int:
        start = block_index * self.block_bytes
        return max(0, min(self.block_bytes, self.stream_bytes - start))

    def _snapshot(self) -> dict:
        assert self._block_index is not None
        length = self._block_length(self._block_index)
        decision = self._decision
        admitted = bool(decision and decision.admitted)
        row = {
            "block_index": self._block_index,
            "block_start": self._block_start,
            "block_bytes": length,
            "probe_bytes_observed": min(len(self._probe_seen), self.probe_bytes),
            "decision_byte": min(self.probe_bytes, length),
            "decision_global_byte": self._block_start + min(self.probe_bytes, length),
            "rule_match": bool(decision and decision.rule_match),
            "budget_allows": bool(decision and decision.budget_allows),
            "budget_limited": bool(decision and decision.rule_match and not decision.admitted),
            "admitted": admitted,
            "route": self.specialist_name if admitted else self.cheap_name,
            "selector_score": int(decision.score) if decision else 0,
            "selector_threshold": int(self.rule.threshold),
        }
        if len(self._probe_seen) == self.probe_bytes:
            row.update(self._features.features().as_dict())
        return row

    def _switch_block(self, block_index: int) -> None:
        if self._block_index is not None:
            self._completed.append(self._snapshot())
        self._block_index = block_index
        self._block_start = block_index * self.block_bytes
        self._cheap = self.cheap_factory()
        self._specialist = None
        self._probe_seen = []
        self._last_probe_cdf = None
        self._features = CheapAdmissionFeatureAccumulator(
            self.probe_bytes, required_features=self.feature_names
        )
        self._decision = None

    def _sync_probe(self, local_prefix: Sequence[int]) -> None:
        assert self._cheap is not None
        target = min(len(local_prefix), self.probe_bytes)
        if list(local_prefix[: len(self._probe_seen)]) != self._probe_seen:
            raise ValueError("admission router received a divergent block prefix")
        while len(self._probe_seen) < target:
            index = len(self._probe_seen)
            if self._last_probe_cdf is None:
                self._last_probe_cdf = self._cheap(index, self._probe_seen)
            symbol = int(local_prefix[index])
            self._features.observe(self._last_probe_cdf, symbol)
            self._probe_seen.append(symbol)
            self._last_probe_cdf = None

    def _maybe_decide(self, local_index: int) -> None:
        if self._decision is not None:
            return
        assert self._block_index is not None
        block_length = self._block_length(self._block_index)
        if local_index < min(self.probe_bytes, block_length):
            return
        if block_length <= self.probe_bytes or self.specialist_factory is None:
            self._decision = CheapAdmissionDecision(
                score=0,
                threshold=int(self.rule.threshold),
                rule_match=False,
                budget_allows=False,
                admitted=False,
            )
            return

        self._decision = rich_cheap_admission_decision(
            self._features.features(),
            self.rule,
            AdmissionBudgetState(self._admitted_bytes, self.max_admitted_bytes),
            block_length,
        )
        if self._decision.admitted:
            self._admitted_bytes += block_length
            self._specialist = self.specialist_factory()

    def __call__(self, index: int, prefix: Sequence[int]):
        if index != len(prefix):
            raise ValueError("index must equal prefix length")
        if index < 0 or index >= self.stream_bytes:
            raise ValueError("index outside configured stream")
        prefix_list = [int(value) for value in prefix]
        if (
            len(prefix_list) < len(self._last_prefix)
            or prefix_list[: len(self._last_prefix)] != self._last_prefix
        ):
            raise ValueError("admission router received a divergent stream prefix")
        self._last_prefix = prefix_list

        block_index = index // self.block_bytes
        if self._block_index != block_index:
            self._switch_block(block_index)
        assert self._cheap is not None

        local_prefix = prefix_list[self._block_start :]
        local_index = len(local_prefix)
        self._sync_probe(local_prefix)
        self._maybe_decide(local_index)

        if self._decision and self._decision.admitted:
            assert self._specialist is not None
            self.specialist_output_calls += 1
            return self._specialist(local_index, local_prefix)

        cheap_cdf = self._cheap(local_index, local_prefix)
        if local_index < self.probe_bytes:
            self._last_probe_cdf = cheap_cdf
        return cheap_cdf

    def block_summary(self) -> list[dict]:
        rows = list(self._completed)
        if self._block_index is not None:
            rows.append(self._snapshot())
        return rows

    @property
    def admitted_blocks(self) -> int:
        return sum(bool(row["admitted"]) for row in self.block_summary())

    @property
    def admitted_bytes(self) -> int:
        return self._admitted_bytes

    @property
    def admitted_byte_fraction(self) -> float:
        return self.admitted_bytes / self.stream_bytes if self.stream_bytes else 0.0


def rich_cheap_admission_fingerprint(
    *,
    cheap_fingerprint: bytes,
    specialist_fingerprint: bytes | None,
    stream_bytes: int,
    block_bytes: int,
    probe_bytes: int,
    rule: IntegerAdmissionRule,
    max_admitted_bytes: int | None = None,
) -> bytes:
    if len(cheap_fingerprint) != 32:
        raise ValueError("cheap fingerprint must be 32 bytes")
    if specialist_fingerprint is not None and len(specialist_fingerprint) != 32:
        raise ValueError("specialist fingerprint must be 32 bytes")
    if stream_bytes < 0 or block_bytes <= 0:
        raise ValueError("invalid stream/block size")
    if probe_bytes <= 0 or probe_bytes >= block_bytes:
        raise ValueError("invalid probe size")
    if max_admitted_bytes is not None and not 0 <= max_admitted_bytes <= stream_bytes:
        raise ValueError("max_admitted_bytes must be within the stream")
    payload = {
        "kind": "pollicino-rich-cheap-admission-v1",
        "feature_version": RICH_CHEAP_FEATURE_VERSION,
        "cheap_fingerprint": cheap_fingerprint.hex(),
        "specialist_fingerprint": specialist_fingerprint.hex() if specialist_fingerprint else None,
        "stream_bytes": int(stream_bytes),
        "block_bytes": int(block_bytes),
        "probe_bytes": int(probe_bytes),
        "rule": rule.to_dict(),
        "max_admitted_bytes": stream_bytes if max_admitted_bytes is None else int(max_admitted_bytes),
        "state_scope": "block-reset",
        "specialist_creation": "lazy-after-rich-cheap-probe",
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).digest()


class CheapCodelengthAdmissionBlockCDFProvider:
    """Gate expensive block-local specialization using cheap-only evidence.

    Every block starts with a fresh cheap provider. The first ``probe_bytes`` are
    coded by that provider while their exact quantized likelihood is accumulated.
    Once the probe is complete, the block is admitted to the specialist only when
    the cheap codelength lies inside the configured integer-bit band *and* the
    stream-level admitted-byte budget can still pay for the whole block.

    If a block is rejected, ``specialist_factory`` is never called for that block.
    If it is admitted, the specialist is created lazily and receives the complete
    local prefix. Stateful specialists may therefore replay/catch up the probe;
    experiments must count that work explicitly. This class intentionally does
    not expose a misleading generic ``compute_fraction`` property.

    ``max_admitted_bytes`` is a causal coverage cap, not a generic claim about the
    cost of an arbitrary specialist. For PILOT-013 the neural provider performs at
    most one uncached model evaluation per admitted source byte, so a 50% coverage
    cap is also a hard upper bound on normalized neural forward evaluations.

    The codelength comparisons are exact. For likelihood P = num / den,
    ``-log2(P) >= L`` iff ``num * 2**L <= den`` and
    ``-log2(P) <= U`` iff ``num * 2**U >= den``.
    """

    def __init__(
        self,
        cheap_factory: Callable[[], object],
        specialist_factory: Callable[[], object] | None,
        *,
        stream_bytes: int,
        block_bytes: int,
        probe_bytes: int,
        min_probe_code_bits: int,
        max_probe_code_bits: int,
        max_admitted_bytes: int | None = None,
        cheap_name: str = "cheap",
        specialist_name: str = "specialist",
    ) -> None:
        if stream_bytes < 0:
            raise ValueError("stream_bytes must be non-negative")
        if block_bytes <= 0:
            raise ValueError("block_bytes must be positive")
        if probe_bytes <= 0 or probe_bytes >= block_bytes:
            raise ValueError("probe_bytes must be in [1, block_bytes)")
        if min_probe_code_bits < 0 or max_probe_code_bits < min_probe_code_bits:
            raise ValueError("invalid probe codelength band")
        if max_admitted_bytes is not None and not 0 <= max_admitted_bytes <= stream_bytes:
            raise ValueError("max_admitted_bytes must be within the stream")
        if not cheap_name or not specialist_name or cheap_name == specialist_name:
            raise ValueError("route names must be distinct non-empty strings")

        self.cheap_factory = cheap_factory
        self.specialist_factory = specialist_factory
        self.stream_bytes = int(stream_bytes)
        self.block_bytes = int(block_bytes)
        self.probe_bytes = int(probe_bytes)
        self.min_probe_code_bits = int(min_probe_code_bits)
        self.max_probe_code_bits = int(max_probe_code_bits)
        self.max_admitted_bytes = (
            self.stream_bytes if max_admitted_bytes is None else int(max_admitted_bytes)
        )
        self.cheap_name = str(cheap_name)
        self.specialist_name = str(specialist_name)

        self._block_index: int | None = None
        self._block_start = 0
        self._cheap = None
        self._specialist = None
        self._probe_seen: list[int] = []
        self._last_probe_cdf: Sequence[int] | None = None
        self._probe_num = 1
        self._probe_den = 1
        self._band_match: bool | None = None
        self._admitted: bool | None = None
        self._admitted_bytes = 0
        self._completed: list[dict[str, int | str | bool]] = []
        self._last_prefix: list[int] = []
        self.specialist_output_calls = 0

    @staticmethod
    def _term(cdf: Sequence[int], symbol: int) -> tuple[int, int]:
        if not 0 <= symbol < len(cdf) - 1:
            raise ValueError("symbol outside provider alphabet")
        numerator = int(cdf[symbol + 1]) - int(cdf[symbol])
        denominator = int(cdf[-1])
        if numerator <= 0 or denominator <= 0 or numerator > denominator:
            raise ValueError("provider returned an invalid CDF")
        return numerator, denominator

    def _block_length(self, block_index: int) -> int:
        start = block_index * self.block_bytes
        return max(0, min(self.block_bytes, self.stream_bytes - start))

    def _snapshot(self) -> dict[str, int | str | bool]:
        assert self._block_index is not None
        length = self._block_length(self._block_index)
        admitted = bool(self._admitted)
        band_match = bool(self._band_match)
        decision = min(self.probe_bytes, length)
        return {
            "block_index": self._block_index,
            "block_start": self._block_start,
            "block_bytes": length,
            "probe_bytes_observed": min(len(self._probe_seen), self.probe_bytes),
            "decision_byte": decision,
            "decision_global_byte": self._block_start + decision,
            "band_match": band_match,
            "budget_limited": band_match and not admitted,
            "admitted": admitted,
            "route": self.specialist_name if admitted else self.cheap_name,
        }

    def _switch_block(self, block_index: int) -> None:
        if self._block_index is not None:
            self._completed.append(self._snapshot())
        self._block_index = block_index
        self._block_start = block_index * self.block_bytes
        self._cheap = self.cheap_factory()
        self._specialist = None
        self._probe_seen = []
        self._last_probe_cdf = None
        self._probe_num = 1
        self._probe_den = 1
        self._band_match = None
        self._admitted = None

    def _sync_probe(self, local_prefix: Sequence[int]) -> None:
        assert self._cheap is not None
        target = min(len(local_prefix), self.probe_bytes)
        if list(local_prefix[: len(self._probe_seen)]) != self._probe_seen:
            raise ValueError("admission router received a divergent block prefix")
        while len(self._probe_seen) < target:
            index = len(self._probe_seen)
            if self._last_probe_cdf is None:
                self._last_probe_cdf = self._cheap(index, self._probe_seen)
            symbol = int(local_prefix[index])
            num, den = self._term(self._last_probe_cdf, symbol)
            self._probe_num *= num
            self._probe_den *= den
            self._probe_seen.append(symbol)
            self._last_probe_cdf = None

    def _in_admission_band(self) -> bool:
        # min_bits <= -log2(P) <= max_bits, compared without floating point.
        at_least_min = self._probe_num * (1 << self.min_probe_code_bits) <= self._probe_den
        at_most_max = self._probe_num * (1 << self.max_probe_code_bits) >= self._probe_den
        return at_least_min and at_most_max

    def _maybe_decide(self, local_index: int) -> None:
        if self._admitted is not None:
            return
        assert self._block_index is not None
        block_length = self._block_length(self._block_index)
        if local_index < min(self.probe_bytes, block_length):
            return

        # No byte remains after the probe, so specialization cannot affect coding.
        if block_length <= self.probe_bytes or self.specialist_factory is None:
            self._band_match = False
            self._admitted = False
            return

        self._band_match = self._in_admission_band()
        budget_allows = self._admitted_bytes + block_length <= self.max_admitted_bytes
        self._admitted = self._band_match and budget_allows
        if self._admitted:
            self._admitted_bytes += block_length
            self._specialist = self.specialist_factory()

    def __call__(self, index: int, prefix: Sequence[int]):
        if index != len(prefix):
            raise ValueError("index must equal prefix length")
        if index < 0 or index >= self.stream_bytes:
            raise ValueError("index outside configured stream")
        prefix_list = [int(value) for value in prefix]
        if (
            len(prefix_list) < len(self._last_prefix)
            or prefix_list[: len(self._last_prefix)] != self._last_prefix
        ):
            raise ValueError("admission router received a divergent stream prefix")
        self._last_prefix = prefix_list

        block_index = index // self.block_bytes
        if self._block_index != block_index:
            self._switch_block(block_index)
        assert self._cheap is not None

        local_prefix = prefix_list[self._block_start :]
        local_index = len(local_prefix)
        self._sync_probe(local_prefix)
        self._maybe_decide(local_index)

        if self._admitted:
            assert self._specialist is not None
            self.specialist_output_calls += 1
            return self._specialist(local_index, local_prefix)

        cheap_cdf = self._cheap(local_index, local_prefix)
        if local_index < self.probe_bytes:
            self._last_probe_cdf = cheap_cdf
        return cheap_cdf

    def block_summary(self) -> list[dict[str, int | str | bool]]:
        rows = list(self._completed)
        if self._block_index is not None:
            rows.append(self._snapshot())
        return rows

    @property
    def admitted_blocks(self) -> int:
        return sum(bool(row["admitted"]) for row in self.block_summary())

    @property
    def admitted_bytes(self) -> int:
        return self._admitted_bytes

    @property
    def admission_fraction(self) -> float:
        rows = self.block_summary()
        if not rows:
            return 0.0
        return self.admitted_blocks / len(rows)

    @property
    def admitted_byte_fraction(self) -> float:
        if self.stream_bytes <= 0:
            return 0.0
        return self.admitted_bytes / self.stream_bytes


def cheap_codelength_admission_fingerprint(
    *,
    cheap_fingerprint: bytes,
    specialist_fingerprint: bytes | None,
    stream_bytes: int,
    block_bytes: int,
    probe_bytes: int,
    min_probe_code_bits: int,
    max_probe_code_bits: int,
    max_admitted_bytes: int | None = None,
) -> bytes:
    if len(cheap_fingerprint) != 32:
        raise ValueError("cheap fingerprint must be 32 bytes")
    if specialist_fingerprint is not None and len(specialist_fingerprint) != 32:
        raise ValueError("specialist fingerprint must be 32 bytes")
    if stream_bytes < 0 or block_bytes <= 0:
        raise ValueError("invalid stream/block size")
    if probe_bytes <= 0 or probe_bytes >= block_bytes:
        raise ValueError("invalid probe size")
    if min_probe_code_bits < 0 or max_probe_code_bits < min_probe_code_bits:
        raise ValueError("invalid probe codelength band")
    if max_admitted_bytes is not None and not 0 <= max_admitted_bytes <= stream_bytes:
        raise ValueError("max_admitted_bytes must be within the stream")
    payload = {
        "kind": "pollicino-cheap-codelength-admission-v1",
        "cheap_fingerprint": cheap_fingerprint.hex(),
        "specialist_fingerprint": specialist_fingerprint.hex() if specialist_fingerprint else None,
        "stream_bytes": int(stream_bytes),
        "block_bytes": int(block_bytes),
        "probe_bytes": int(probe_bytes),
        "min_probe_code_bits": int(min_probe_code_bits),
        "max_probe_code_bits": int(max_probe_code_bits),
        "max_admitted_bytes": stream_bytes if max_admitted_bytes is None else int(max_admitted_bytes),
        "state_scope": "block-reset",
        "specialist_creation": "lazy-after-cheap-probe",
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).digest()
