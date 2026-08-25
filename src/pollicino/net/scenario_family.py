from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import hashlib
import random
from typing import Callable, Mapping, Sequence

from .bearer import BearerProfile
from .bundle import CustodyLedger, ForwardBundle, seed_bundle_custody
from .contact_windows import SyntheticContactWindow
from .fair_scheduling import BearerSchedulingPolicy, FairSchedulerState
from .routing_benchmark import RoutingBenchmarkScenario, RoutingBenchmarkReport, run_synthetic_routing_benchmark
from .routing_compare import (
    EmergencyFloodProgressStrategy,
    FloodAllStrategy,
    GatewayProgressStrategy,
    RoutingStrategy,
)
from .scheduling import BundlePriority, ScheduledBundle
from .store import PollicinoStore
from .store_forward import ForwardPeer, seed_forwarding_object
from .wire import DiscoveryDescriptor


StrategyFactory = Callable[[Mapping[str, int]], Sequence[RoutingStrategy]]


def _require_non_negative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _require_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _require_id(name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class SyntheticBearerTemplate:
    """Explicit synthetic window template for one bearer.

    Durations and logical byte budgets are generated independently from the
    configured ranges. They are scenario inputs, not inferred radio capacity.
    No LoRa/BLE/Wi-Fi/Internet performance defaults live in this module.
    """

    profile: BearerProfile
    scheduling_policy: BearerSchedulingPolicy
    selection_weight: int
    min_duration_seconds: int
    max_duration_seconds: int
    min_logical_source_byte_budget: int
    max_logical_source_byte_budget: int

    def __post_init__(self) -> None:
        if not isinstance(self.profile, BearerProfile):
            raise TypeError("profile must be BearerProfile")
        if not isinstance(self.scheduling_policy, BearerSchedulingPolicy):
            raise TypeError("scheduling_policy must be BearerSchedulingPolicy")
        if self.scheduling_policy.bearer_id != self.profile.bearer_id:
            raise ValueError("scheduling policy bearer_id must match bearer profile")
        _require_positive_int("selection_weight", self.selection_weight)
        _require_non_negative_int("min_duration_seconds", self.min_duration_seconds)
        _require_non_negative_int("max_duration_seconds", self.max_duration_seconds)
        _require_non_negative_int(
            "min_logical_source_byte_budget", self.min_logical_source_byte_budget
        )
        _require_non_negative_int(
            "max_logical_source_byte_budget", self.max_logical_source_byte_budget
        )
        if self.max_duration_seconds < self.min_duration_seconds:
            raise ValueError("max_duration_seconds cannot be below min_duration_seconds")
        if self.max_logical_source_byte_budget < self.min_logical_source_byte_budget:
            raise ValueError(
                "max_logical_source_byte_budget cannot be below min_logical_source_byte_budget"
            )


@dataclass(frozen=True, slots=True)
class SyntheticScenarioFamilyConfig:
    family_id: str
    seed: int
    scenario_count: int
    peer_count: int
    gateway_count: int
    bundle_count: int
    windows_per_scenario: int
    start_s: int
    horizon_seconds: int
    chunk_size: int
    min_bundle_chunks: int
    max_bundle_chunks: int
    min_ttl_seconds: int
    max_ttl_seconds: int
    hop_limit: int = 16
    # BULK, NORMAL, HIGH, EMERGENCY. Values are relative synthetic traffic mix.
    priority_weights: tuple[int, int, int, int] = (1, 6, 2, 1)

    def __post_init__(self) -> None:
        _require_id("family_id", self.family_id)
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise ValueError("seed must be an integer")
        for name, value in (
            ("scenario_count", self.scenario_count),
            ("peer_count", self.peer_count),
            ("gateway_count", self.gateway_count),
            ("bundle_count", self.bundle_count),
            ("windows_per_scenario", self.windows_per_scenario),
            ("horizon_seconds", self.horizon_seconds),
            ("chunk_size", self.chunk_size),
            ("min_bundle_chunks", self.min_bundle_chunks),
            ("max_bundle_chunks", self.max_bundle_chunks),
            ("min_ttl_seconds", self.min_ttl_seconds),
            ("max_ttl_seconds", self.max_ttl_seconds),
            ("hop_limit", self.hop_limit),
        ):
            _require_positive_int(name, value)
        _require_non_negative_int("start_s", self.start_s)
        if self.gateway_count >= self.peer_count:
            raise ValueError("gateway_count must be smaller than peer_count")
        if self.max_bundle_chunks < self.min_bundle_chunks:
            raise ValueError("max_bundle_chunks cannot be below min_bundle_chunks")
        if self.max_ttl_seconds < self.min_ttl_seconds:
            raise ValueError("max_ttl_seconds cannot be below min_ttl_seconds")
        if self.hop_limit > 0xFF:
            raise ValueError("hop_limit must fit in the PND1 unsigned 8-bit field")
        if (
            not isinstance(self.priority_weights, tuple)
            or len(self.priority_weights) != 4
        ):
            raise ValueError("priority_weights must be a 4-tuple")
        for value in self.priority_weights:
            _require_non_negative_int("priority_weight", value)
        if sum(self.priority_weights) <= 0:
            raise ValueError("at least one priority weight must be positive")


@dataclass(frozen=True, slots=True)
class GeneratedScenarioSummary:
    scenario_id: str
    scenario_seed: int
    gateway_ids: tuple[str, ...]
    static_gateway_rank: tuple[tuple[str, int], ...]
    priority_counts: tuple[tuple[str, int], ...]
    bearer_window_counts: tuple[tuple[str, int], ...]

    def rank_for(self, peer_id: str) -> int:
        for key, value in self.static_gateway_rank:
            if key == peer_id:
                return value
        raise KeyError(f"peer {peer_id!r} is not present in generated summary")


@dataclass(frozen=True, slots=True)
class SyntheticScenarioFamily:
    family_id: str
    seed: int
    scenarios: tuple[RoutingBenchmarkScenario, ...]
    summaries: tuple[GeneratedScenarioSummary, ...]

    def run_benchmark(self) -> RoutingBenchmarkReport:
        return run_synthetic_routing_benchmark(self.scenarios)


def core_strategy_factory(peer_rank: Mapping[str, int]) -> tuple[RoutingStrategy, ...]:
    """Common benchmark strategies using scenario-local static synthetic ranks."""

    return (
        FloodAllStrategy(),
        GatewayProgressStrategy(dict(peer_rank)),
        EmergencyFloodProgressStrategy(dict(peer_rank)),
    )


def _weighted_choice(rng: random.Random, values: Sequence[object], weights: Sequence[int]):
    return rng.choices(list(values), weights=list(weights), k=1)[0]


def _content_bytes(
    family_id: str,
    scenario_index: int,
    bundle_index: int,
    *,
    chunk_count: int,
    chunk_size: int,
) -> bytes:
    pieces: list[bytes] = []
    for chunk_index in range(chunk_count):
        digest = hashlib.sha256(
            f"{family_id}:{scenario_index}:{bundle_index}:{chunk_index}".encode("utf-8")
        ).digest()
        repeats = (chunk_size + len(digest) - 1) // len(digest)
        pieces.append((digest * repeats)[:chunk_size])
    return b"".join(pieces)


def _static_gateway_rank(
    peer_ids: Sequence[str],
    gateway_ids: Sequence[str],
    windows: Sequence[SyntheticContactWindow],
) -> dict[str, int]:
    """Whole-scenario undirected hop rank used only as synthetic benchmark metadata.

    This deliberately sees the complete generated contact graph, so it is an
    oracle-like static scenario hint rather than information a live relay can be
    assumed to know. Disconnected peers receive ``len(peer_ids) + 1``.
    """

    adjacency: dict[str, set[str]] = {peer_id: set() for peer_id in peer_ids}
    for window in windows:
        adjacency[window.source_id].add(window.target_id)
        adjacency[window.target_id].add(window.source_id)
    unreachable = len(peer_ids) + 1
    rank = {peer_id: unreachable for peer_id in peer_ids}
    queue: deque[str] = deque()
    for gateway_id in gateway_ids:
        rank[gateway_id] = 0
        queue.append(gateway_id)
    while queue:
        current = queue.popleft()
        next_rank = rank[current] + 1
        for neighbor in sorted(adjacency[current]):
            if next_rank >= rank[neighbor]:
                continue
            rank[neighbor] = next_rank
            queue.append(neighbor)
    return rank


def _make_windows(
    rng: random.Random,
    *,
    config: SyntheticScenarioFamilyConfig,
    scenario_index: int,
    peer_ids: Sequence[str],
    bearer_templates: Sequence[SyntheticBearerTemplate],
) -> tuple[SyntheticContactWindow, ...]:
    weights = [item.selection_weight for item in bearer_templates]
    result: list[SyntheticContactWindow] = []
    for index in range(config.windows_per_scenario):
        source_id, target_id = rng.sample(list(peer_ids), 2)
        template = _weighted_choice(rng, bearer_templates, weights)
        assert isinstance(template, SyntheticBearerTemplate)
        start_offset = rng.randint(1, config.horizon_seconds)
        duration = rng.randint(
            template.min_duration_seconds, template.max_duration_seconds
        )
        budget = rng.randint(
            template.min_logical_source_byte_budget,
            template.max_logical_source_byte_budget,
        )
        # Transfer IDs are deterministic synthetic identifiers. A random 32-bit
        # value avoids coupling the generated capacity to the window index.
        transfer_id_base = rng.getrandbits(32)
        result.append(
            SyntheticContactWindow(
                encounter_id=f"{config.family_id}-s{scenario_index:04d}-w{index:05d}",
                source_id=source_id,
                target_id=target_id,
                bearer_id=template.profile.bearer_id,
                start_s=config.start_s + start_offset,
                duration_seconds=duration,
                logical_source_byte_budget=budget,
                transfer_id_base=transfer_id_base,
            )
        )
    return tuple(sorted(result, key=lambda item: (item.start_s, item.encounter_id)))


def _make_bundles(
    rng: random.Random,
    *,
    config: SyntheticScenarioFamilyConfig,
    scenario_index: int,
    origin_ids: Sequence[str],
    peers: Mapping[str, ForwardPeer],
    ledger: CustodyLedger,
) -> tuple[ScheduledBundle, ...]:
    priorities = (
        BundlePriority.BULK,
        BundlePriority.NORMAL,
        BundlePriority.HIGH,
        BundlePriority.EMERGENCY,
    )
    result: list[ScheduledBundle] = []
    for index in range(config.bundle_count):
        origin_id = rng.choice(list(origin_ids))
        chunk_count = rng.randint(config.min_bundle_chunks, config.max_bundle_chunks)
        ttl_seconds = rng.randint(config.min_ttl_seconds, config.max_ttl_seconds)
        priority = _weighted_choice(rng, priorities, config.priority_weights)
        assert isinstance(priority, BundlePriority)
        data = _content_bytes(
            config.family_id,
            scenario_index,
            index,
            chunk_count=chunk_count,
            chunk_size=config.chunk_size,
        )
        manifest = seed_forwarding_object(
            data,
            chunk_size=config.chunk_size,
            store=peers[origin_id].store,
        )
        descriptor = DiscoveryDescriptor(
            object_class=1,
            rendezvous_key=(
                f"family:{config.family_id}:scenario:{scenario_index}:bundle:{index}"
            ).encode("utf-8"),
            ttl_seconds=ttl_seconds,
            hop_limit=config.hop_limit,
            nonce=rng.getrandbits(64),
        )
        bundle = ForwardBundle.from_descriptor(
            manifest,
            descriptor,
            created_at_s=config.start_s,
        )
        seed_bundle_custody(
            bundle,
            manifest,
            origin=peers[origin_id],
            ledger=ledger,
            now_s=config.start_s,
        )
        result.append(
            ScheduledBundle(
                bundle=bundle,
                manifest=manifest,
                priority=priority,
                label=f"bundle-{index:04d}",
            )
        )
    return tuple(result)


def generate_synthetic_scenario_family(
    config: SyntheticScenarioFamilyConfig,
    *,
    bearer_templates: Sequence[SyntheticBearerTemplate],
    strategy_factory: StrategyFactory = core_strategy_factory,
) -> SyntheticScenarioFamily:
    """Generate a reproducible family of independent synthetic routing scenarios.

    Reusing the same config, bearer templates and strategy factory with the same
    seed produces byte-for-byte stable bundle identities and contact metadata.
    The generator never derives logical byte budget from contact duration and
    never labels generated values as physical measurements.
    """

    if not isinstance(config, SyntheticScenarioFamilyConfig):
        raise TypeError("config must be SyntheticScenarioFamilyConfig")
    if not bearer_templates:
        raise ValueError("at least one explicit synthetic bearer template is required")
    if len({item.profile.bearer_id for item in bearer_templates}) != len(bearer_templates):
        raise ValueError("bearer template IDs must be unique")
    if not callable(strategy_factory):
        raise TypeError("strategy_factory must be callable")

    family_rng = random.Random(config.seed)
    scenarios: list[RoutingBenchmarkScenario] = []
    summaries: list[GeneratedScenarioSummary] = []

    for scenario_index in range(config.scenario_count):
        scenario_seed = family_rng.getrandbits(64)
        rng = random.Random(scenario_seed)
        peer_ids = tuple(f"node-{index:03d}" for index in range(config.peer_count))
        gateway_ids = tuple(peer_ids[-config.gateway_count :])
        origin_ids = tuple(peer_id for peer_id in peer_ids if peer_id not in gateway_ids)
        peers = {
            peer_id: ForwardPeer(peer_id, PollicinoStore()) for peer_id in peer_ids
        }
        ledger = CustodyLedger()
        windows = _make_windows(
            rng,
            config=config,
            scenario_index=scenario_index,
            peer_ids=peer_ids,
            bearer_templates=bearer_templates,
        )
        bundles = _make_bundles(
            rng,
            config=config,
            scenario_index=scenario_index,
            origin_ids=origin_ids,
            peers=peers,
            ledger=ledger,
        )
        ranks = _static_gateway_rank(peer_ids, gateway_ids, windows)
        strategies = tuple(strategy_factory(ranks))
        if not strategies:
            raise ValueError("strategy_factory must return at least one strategy")

        bearers = {item.profile.bearer_id: item.profile for item in bearer_templates}
        policies = {
            item.profile.bearer_id: item.scheduling_policy
            for item in bearer_templates
        }
        scenario_id = f"{config.family_id}-s{scenario_index:04d}"
        scenarios.append(
            RoutingBenchmarkScenario(
                scenario_id=scenario_id,
                strategies=strategies,
                bundles=bundles,
                peers=peers,
                ledger=ledger,
                windows=windows,
                bearers=bearers,
                scheduling_policies=policies,
                scheduler_states={},
                destination_ids=gateway_ids,
                tags=("generated", f"family:{config.family_id}"),
            )
        )

        priority_counts = tuple(
            (priority.name.lower(), sum(item.priority is priority for item in bundles))
            for priority in BundlePriority
        )
        bearer_counts = tuple(
            (
                template.profile.bearer_id,
                sum(window.bearer_id == template.profile.bearer_id for window in windows),
            )
            for template in sorted(
                bearer_templates, key=lambda item: item.profile.bearer_id
            )
        )
        summaries.append(
            GeneratedScenarioSummary(
                scenario_id=scenario_id,
                scenario_seed=scenario_seed,
                gateway_ids=gateway_ids,
                static_gateway_rank=tuple(sorted(ranks.items())),
                priority_counts=priority_counts,
                bearer_window_counts=bearer_counts,
            )
        )

    return SyntheticScenarioFamily(
        family_id=config.family_id,
        seed=config.seed,
        scenarios=tuple(scenarios),
        summaries=tuple(summaries),
    )
