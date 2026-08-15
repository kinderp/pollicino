from __future__ import annotations

import math


def information_bits(probability: float) -> float:
    if not 0 < probability <= 1:
        raise ValueError("probability must satisfy 0 < p <= 1")
    return -math.log2(probability)


def sequence_information(probabilities: list[float]) -> float:
    return sum(information_bits(probability) for probability in probabilities)


def most_surprising(probabilities: list[float]) -> tuple[int, float]:
    if not probabilities:
        raise ValueError("probabilities cannot be empty")
    values = [information_bits(probability) for probability in probabilities]
    index = max(range(len(values)), key=values.__getitem__)
    return index, values[index]


if __name__ == "__main__":
    for p in (1, 1/2, 1/4, 1/16, 1/256):
        print(f"p={p:8.6f} -> {information_bits(p):5.2f} bit")
