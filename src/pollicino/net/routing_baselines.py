from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .scheduling import ScheduledBundle
from .store_forward import ForwardPeer


def _require_strategy_id(value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError("strategy_id must be a non-empty string")


@dataclass(frozen=True, slots=True)
class DirectDeliveryStrategy:
    """Forward only when the encountered peer is a final destination.

    This is the simplest DTN baseline: no relay ever receives a copy merely to
    help future delivery. ``destination_ids`` is explicit scenario/application
    knowledge supplied to the strategy; it is not inferred from topology.
    """

    destination_ids: tuple[str, ...]
    strategy_id: str = "direct-delivery"

    def __post_init__(self) -> None:
        _require_strategy_id(self.strategy_id)
        if not isinstance(self.destination_ids, tuple) or not self.destination_ids:
            raise ValueError("destination_ids must be a non-empty tuple")
        if any(not isinstance(value, str) or not value for value in self.destination_ids):
            raise ValueError("destination_ids must contain non-empty strings")
        if len(set(self.destination_ids)) != len(self.destination_ids):
            raise ValueError("destination_ids must be unique")

    def select_bundles(
        self,
        bundles: Sequence[ScheduledBundle],
        *,
        target: ForwardPeer,
        **_: object,
    ) -> tuple[ScheduledBundle, ...]:
        if target.peer_id not in self.destination_ids:
            return ()
        return tuple(bundles)


@dataclass(frozen=True, slots=True)
class EpidemicStrategy:
    """Replicate every eligible bundle at every encounter.

    This implements the canonical Epidemic *forwarding eligibility* rule inside
    the existing PollicinoNet experiment harness. The underlying governed
    transfer remains Pollicino-specific: it suppresses chunks already present
    at the receiver and accounts PCM1/PNA1/PNB1/PNC1/ACK/retry bytes.

    Therefore this is a routing-behaviour baseline, not a claim to reproduce
    every control packet of the original Epidemic Routing implementation. A
    future protocol-overhead experiment may model an explicit summary-vector
    exchange separately if a research question requires it.
    """

    strategy_id: str = "epidemic"

    def __post_init__(self) -> None:
        _require_strategy_id(self.strategy_id)

    def select_bundles(
        self,
        bundles: Sequence[ScheduledBundle],
        **_: object,
    ) -> tuple[ScheduledBundle, ...]:
        return tuple(bundles)
