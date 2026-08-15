from __future__ import annotations

import math


def information_bits(probability: float) -> float:
    """Return self-information I(x) = -log2(p).

    Probability must satisfy 0 < p <= 1.
    """
    # TODO
    raise NotImplementedError


def sequence_information(probabilities: list[float]) -> float:
    """Return the sum of self-information values."""
    # TODO
    raise NotImplementedError


def most_surprising(probabilities: list[float]) -> tuple[int, float]:
    """Return (index, information_bits) for the least probable event."""
    # TODO
    raise NotImplementedError


if __name__ == "__main__":
    for p in (1, 1/2, 1/4, 1/16, 1/256):
        print(f"p={p:8.6f} -> {information_bits(p):5.2f} bit")
