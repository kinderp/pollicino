from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import math


def _require_id(name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _edge_key(node_a: str, node_b: str) -> tuple[str, str]:
    _require_id("node_a", node_a)
    _require_id("node_b", node_b)
    if node_a == node_b:
        raise ValueError("meeting edge endpoints must differ")
    return tuple(sorted((node_a, node_b)))  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class RapidMeetingEdge:
    node_a: str
    node_b: str
    mean_intermeeting_seconds: float
    sample_count: int
    observed_at_s: int

    def __post_init__(self) -> None:
        canonical = _edge_key(self.node_a, self.node_b)
        if (self.node_a, self.node_b) != canonical:
            raise ValueError("meeting edge endpoints must be in canonical sorted order")
        if (
            isinstance(self.mean_intermeeting_seconds, bool)
            or not isinstance(self.mean_intermeeting_seconds, (int, float))
            or not math.isfinite(float(self.mean_intermeeting_seconds))
            or self.mean_intermeeting_seconds <= 0
        ):
            raise ValueError("mean_intermeeting_seconds must be finite and positive")
        if (
            isinstance(self.sample_count, bool)
            or not isinstance(self.sample_count, int)
            or self.sample_count <= 0
        ):
            raise ValueError("sample_count must be a positive integer")
        if (
            isinstance(self.observed_at_s, bool)
            or not isinstance(self.observed_at_s, int)
            or self.observed_at_s < 0
        ):
            raise ValueError("observed_at_s must be a non-negative integer")

    @property
    def key(self) -> tuple[str, str]:
        return self.node_a, self.node_b


@dataclass(frozen=True, slots=True)
class RapidMeetingMetadataExchangeReport:
    left_id: str
    right_id: str
    left_sent_entry_count: int
    right_sent_entry_count: int
    left_learned_entry_count: int
    right_learned_entry_count: int

    @property
    def total_sent_entry_count(self) -> int:
        return self.left_sent_entry_count + self.right_sent_entry_count


@dataclass(slots=True)
class RapidMeetingControlState:
    """Local, gossipable meeting-time knowledge for a RAPID prototype.

    Direct encounter intervals are measured only from this node's own history.
    Gossip can add newer estimates for other edges. Per-peer generation cursors
    let metadata exchange send only locally changed knowledge since the previous
    exchange with that peer.

    Entry counts are observable control work. No wire-byte cost is inferred.
    """

    node_id: str
    _last_direct_meeting_s: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    _direct_mean_s: dict[str, float] = field(default_factory=dict, init=False, repr=False)
    _direct_sample_count: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    _edges: dict[tuple[str, str], RapidMeetingEdge] = field(default_factory=dict, init=False, repr=False)
    _generation: int = field(default=0, init=False, repr=False)
    _edge_generation: dict[tuple[str, str], int] = field(default_factory=dict, init=False, repr=False)
    _last_sent_generation: dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        _require_id("node_id", self.node_id)

    @property
    def edges(self) -> tuple[RapidMeetingEdge, ...]:
        return tuple(self._edges[key] for key in sorted(self._edges))

    def edge(self, node_a: str, node_b: str) -> RapidMeetingEdge | None:
        return self._edges.get(_edge_key(node_a, node_b))

    def _learn_edge(self, edge: RapidMeetingEdge) -> bool:
        previous = self._edges.get(edge.key)
        if previous is not None:
            previous_freshness = (previous.observed_at_s, previous.sample_count)
            candidate_freshness = (edge.observed_at_s, edge.sample_count)
            if candidate_freshness <= previous_freshness:
                return False
        self._edges[edge.key] = edge
        self._generation += 1
        self._edge_generation[edge.key] = self._generation
        return True

    def observe_direct_encounter(self, peer_id: str, *, now_s: int) -> RapidMeetingEdge | None:
        _require_id("peer_id", peer_id)
        if peer_id == self.node_id:
            raise ValueError("a node cannot encounter itself")
        if isinstance(now_s, bool) or not isinstance(now_s, int) or now_s < 0:
            raise ValueError("now_s must be a non-negative integer")

        previous_s = self._last_direct_meeting_s.get(peer_id)
        if previous_s is not None and now_s <= previous_s:
            raise ValueError("direct encounter times must increase for each peer")
        self._last_direct_meeting_s[peer_id] = now_s
        if previous_s is None:
            return None

        interval = now_s - previous_s
        previous_count = self._direct_sample_count.get(peer_id, 0)
        previous_mean = self._direct_mean_s.get(peer_id, 0.0)
        count = previous_count + 1
        mean = interval if previous_count == 0 else previous_mean + (interval - previous_mean) / count
        self._direct_sample_count[peer_id] = count
        self._direct_mean_s[peer_id] = float(mean)

        node_a, node_b = _edge_key(self.node_id, peer_id)
        edge = RapidMeetingEdge(
            node_a=node_a,
            node_b=node_b,
            mean_intermeeting_seconds=float(mean),
            sample_count=count,
            observed_at_s=now_s,
        )
        self._learn_edge(edge)
        return edge

    def _delta_for(self, peer_id: str) -> tuple[RapidMeetingEdge, ...]:
        _require_id("peer_id", peer_id)
        watermark = self._last_sent_generation.get(peer_id, 0)
        return tuple(
            self._edges[key]
            for key in sorted(self._edges)
            if self._edge_generation[key] > watermark
        )

    def _merge(self, edges: tuple[RapidMeetingEdge, ...]) -> int:
        learned = 0
        for edge in edges:
            if not isinstance(edge, RapidMeetingEdge):
                raise TypeError("meeting metadata must contain RapidMeetingEdge values")
            learned += self._learn_edge(edge)
        return learned

    def _mark_synchronized_with(self, peer_id: str) -> None:
        _require_id("peer_id", peer_id)
        self._last_sent_generation[peer_id] = self._generation

    def expected_meeting_seconds(
        self,
        source_id: str,
        destination_id: str,
        *,
        max_hops: int = 3,
    ) -> float | None:
        """Shortest expected meeting-time path through current local knowledge."""

        _require_id("source_id", source_id)
        _require_id("destination_id", destination_id)
        if (
            isinstance(max_hops, bool)
            or not isinstance(max_hops, int)
            or max_hops <= 0
        ):
            raise ValueError("max_hops must be a positive integer")
        if source_id == destination_id:
            return 0.0

        adjacency: dict[str, list[tuple[str, float]]] = {}
        for edge in self._edges.values():
            weight = float(edge.mean_intermeeting_seconds)
            adjacency.setdefault(edge.node_a, []).append((edge.node_b, weight))
            adjacency.setdefault(edge.node_b, []).append((edge.node_a, weight))

        queue: list[tuple[float, int, str]] = [(0.0, 0, source_id)]
        best: dict[tuple[str, int], float] = {(source_id, 0): 0.0}
        while queue:
            cost, hops, node_id = heapq.heappop(queue)
            if cost != best.get((node_id, hops)):
                continue
            if node_id == destination_id:
                return cost
            if hops >= max_hops:
                continue
            for neighbor, weight in adjacency.get(node_id, ()):
                next_state = (neighbor, hops + 1)
                next_cost = cost + weight
                if next_cost >= best.get(next_state, math.inf):
                    continue
                best[next_state] = next_cost
                heapq.heappush(queue, (next_cost, hops + 1, neighbor))
        return None


def exchange_rapid_meeting_metadata(
    left: RapidMeetingControlState,
    right: RapidMeetingControlState,
) -> RapidMeetingMetadataExchangeReport:
    """Exchange changed meeting estimates without assigning a wire encoding."""

    if not isinstance(left, RapidMeetingControlState) or not isinstance(
        right, RapidMeetingControlState
    ):
        raise TypeError("left and right must be RapidMeetingControlState values")
    if left.node_id == right.node_id:
        raise ValueError("metadata exchange requires two distinct nodes")

    left_delta = left._delta_for(right.node_id)
    right_delta = right._delta_for(left.node_id)
    left_learned = left._merge(right_delta)
    right_learned = right._merge(left_delta)

    # After the exchange, both peers already know every entry that was sent in
    # either direction, so do not echo freshly learned entries straight back on
    # their next meeting unless those entries are updated again.
    left._mark_synchronized_with(right.node_id)
    right._mark_synchronized_with(left.node_id)

    return RapidMeetingMetadataExchangeReport(
        left_id=left.node_id,
        right_id=right.node_id,
        left_sent_entry_count=len(left_delta),
        right_sent_entry_count=len(right_delta),
        left_learned_entry_count=left_learned,
        right_learned_entry_count=right_learned,
    )
