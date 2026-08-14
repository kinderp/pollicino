"""Information-theoretic metrics shared by all POLLICINO backends."""

from __future__ import annotations

import math
from collections.abc import Iterable


def nats_to_bits(value: float) -> float:
    """Convert natural-log information (nats) to base-2 information (bits)."""
    return value / math.log(2.0)


def mean_bits_per_symbol(negative_log_likelihoods_nats: Iterable[float]) -> float:
    """Return mean ideal code length in bits/symbol from NLL values in nats."""
    values = list(negative_log_likelihoods_nats)
    if not values:
        raise ValueError("at least one negative log-likelihood is required")
    return nats_to_bits(sum(values) / len(values))
