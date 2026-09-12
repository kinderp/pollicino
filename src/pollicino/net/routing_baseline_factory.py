from __future__ import annotations

from typing import Mapping

from .routing_baselines import (
    BinarySprayAndWaitStrategy,
    DirectDeliveryStrategy,
    EpidemicStrategy,
    ProphetStrategy,
)


def canonical_dtn_strategy_factory(
    peer_rank: Mapping[str, int],
) -> tuple[
    DirectDeliveryStrategy,
    EpidemicStrategy,
    BinarySprayAndWaitStrategy,
    ProphetStrategy,
]:
    """Build the canonical DTN baseline set for one generated scenario.

    ``scenario_family`` passes a static gateway-rank mapping to strategy
    factories. This helper uses only the peers whose rank is zero to identify
    final gateway destinations; it does not use the oracle-like non-zero ranks
    for forwarding decisions.
    """

    if not isinstance(peer_rank, Mapping) or not peer_rank:
        raise ValueError("peer_rank must be a non-empty mapping")
    destinations = tuple(
        sorted(
            peer_id
            for peer_id, rank in peer_rank.items()
            if rank == 0
        )
    )
    if not destinations:
        raise ValueError("canonical DTN baselines require at least one rank-zero destination")
    return (
        DirectDeliveryStrategy(destinations),
        EpidemicStrategy(),
        BinarySprayAndWaitStrategy(destinations, initial_copies=4),
        ProphetStrategy(destinations),
    )
