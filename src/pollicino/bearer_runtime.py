from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .node_runtime import NodeMode, PollicinoNodeRuntime


@dataclass(frozen=True, slots=True)
class BearerObservation:
    adapter_id: str
    mode: NodeMode
    available: bool
    ready: bool
    detail: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.adapter_id, str) or not self.adapter_id:
            raise ValueError("adapter_id must be a non-empty string")
        if not isinstance(self.mode, NodeMode):
            raise TypeError("mode must be NodeMode")
        if not isinstance(self.available, bool) or not isinstance(self.ready, bool):
            raise TypeError("available and ready must be booleans")
        if not isinstance(self.detail, str):
            raise TypeError("detail must be a string")

    @property
    def usable(self) -> bool:
        return self.available and self.ready


class BearerProbe(Protocol):
    adapter_id: str
    mode: NodeMode

    def probe(self) -> BearerObservation:
        """Return one current local observation without changing node state."""


@dataclass(frozen=True, slots=True)
class BearerSelectionPolicy:
    """Small lifecycle policy, independent from network routing policy."""

    priority: tuple[NodeMode, ...] = (
        NodeMode.RICH_HOME,
        NodeMode.CONNECTED_MESH,
        NodeMode.OPPORTUNISTIC_DTN,
    )
    loss_confirmations: int = 2

    def __post_init__(self) -> None:
        if not isinstance(self.priority, tuple) or not self.priority:
            raise ValueError("priority must be a non-empty tuple")
        if len(self.priority) != len(set(self.priority)):
            raise ValueError("priority modes must be unique")
        if NodeMode.DISCOVERING in self.priority:
            raise ValueError("DISCOVERING is fallback state, not a bearer priority")
        if (
            isinstance(self.loss_confirmations, bool)
            or not isinstance(self.loss_confirmations, int)
            or self.loss_confirmations < 1
        ):
            raise ValueError("loss_confirmations must be a positive integer")


@dataclass(frozen=True, slots=True)
class BearerEvaluationReport:
    previous_mode: NodeMode
    selected_mode: NodeMode
    selected_adapter_id: str | None
    observations: tuple[BearerObservation, ...]
    changed: bool
    pending_loss_mode: NodeMode | None
    pending_loss_count: int


class NodeBearerController:
    """Choose node lifecycle mode from adapter-local readiness observations.

    This controller does not route bundles and does not estimate radio quality.
    It only answers which runtime context is currently usable. Switching to a
    newly available *higher-priority* context is immediate. Falling back after
    losing the current context requires repeated confirmation so one missed
    mesh/status observation does not flap the node into another mode.
    """

    def __init__(
        self,
        node: PollicinoNodeRuntime,
        probes: Sequence[BearerProbe],
        *,
        policy: BearerSelectionPolicy = BearerSelectionPolicy(),
    ) -> None:
        if not isinstance(node, PollicinoNodeRuntime):
            raise TypeError("node must be PollicinoNodeRuntime")
        if not probes:
            raise ValueError("at least one bearer probe is required")
        self.node = node
        self.probes = tuple(probes)
        self.policy = policy
        ids = [probe.adapter_id for probe in self.probes]
        if len(ids) != len(set(ids)) or any(not item for item in ids):
            raise ValueError("bearer adapter IDs must be unique and non-empty")
        self._pending_loss_mode: NodeMode | None = None
        self._pending_loss_count = 0

    def evaluate(self) -> BearerEvaluationReport:
        observations = tuple(probe.probe() for probe in self.probes)
        by_mode: dict[NodeMode, list[BearerObservation]] = {}
        for observation in observations:
            if not isinstance(observation, BearerObservation):
                raise TypeError("bearer probe must return BearerObservation")
            by_mode.setdefault(observation.mode, []).append(observation)

        previous = self.node.mode
        desired, adapter_id = self._best_usable(by_mode)
        current_usable = any(
            observation.usable for observation in by_mode.get(previous, ())
        )

        changed = False
        selected = previous
        selected_adapter = self._first_usable_adapter(by_mode.get(previous, ()))

        if previous is NodeMode.DISCOVERING:
            if desired is not NodeMode.DISCOVERING:
                self.node.transition(desired)
                selected = desired
                selected_adapter = adapter_id
                changed = True
            self._clear_pending()
        elif current_usable:
            # A richer context (e.g. home Wi-Fi or school mesh) can be entered
            # as soon as it is positively observed. Equal/lower candidates do
            # not displace a still-healthy current bearer.
            if self._rank(desired) < self._rank(previous):
                self.node.transition(desired)
                selected = desired
                selected_adapter = adapter_id
                changed = True
            self._clear_pending()
        else:
            if desired is previous:
                self._clear_pending()
                selected_adapter = adapter_id
            else:
                if desired != self._pending_loss_mode:
                    self._pending_loss_mode = desired
                    self._pending_loss_count = 1
                else:
                    self._pending_loss_count += 1
                if self._pending_loss_count >= self.policy.loss_confirmations:
                    self.node.transition(desired)
                    selected = desired
                    selected_adapter = adapter_id
                    changed = True
                    self._clear_pending()

        return BearerEvaluationReport(
            previous_mode=previous,
            selected_mode=selected,
            selected_adapter_id=selected_adapter,
            observations=observations,
            changed=changed,
            pending_loss_mode=self._pending_loss_mode,
            pending_loss_count=self._pending_loss_count,
        )

    def _best_usable(
        self,
        by_mode: dict[NodeMode, list[BearerObservation]],
    ) -> tuple[NodeMode, str | None]:
        for mode in self.policy.priority:
            adapter_id = self._first_usable_adapter(by_mode.get(mode, ()))
            if adapter_id is not None:
                return mode, adapter_id
        return NodeMode.DISCOVERING, None

    @staticmethod
    def _first_usable_adapter(observations: Sequence[BearerObservation]) -> str | None:
        for observation in observations:
            if observation.usable:
                return observation.adapter_id
        return None

    def _rank(self, mode: NodeMode) -> int:
        if mode is NodeMode.DISCOVERING:
            return len(self.policy.priority)
        try:
            return self.policy.priority.index(mode)
        except ValueError:
            return len(self.policy.priority)

    def _clear_pending(self) -> None:
        self._pending_loss_mode = None
        self._pending_loss_count = 0
