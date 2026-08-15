from __future__ import annotations


def affine_scalar(x: float, weight: float, bias: float) -> float:
    return x * weight + bias


def dot(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("vectors must have the same length")
    return sum(x * y for x, y in zip(a, b))


def linear_logits(features: list[float], weights: list[list[float]], biases: list[float]) -> list[float]:
    if len(weights) != len(biases):
        raise ValueError("one bias is required per output")
    logits = []
    for row in weights:
        if len(row) != len(features):
            raise ValueError("each weight row must match the feature dimension")
        logits.append(dot(features, row))
    return [value + bias for value, bias in zip(logits, biases)]


def parameter_count(input_dim: int, output_dim: int) -> int:
    if input_dim < 0 or output_dim < 0:
        raise ValueError("dimensions must be non-negative")
    return input_dim * output_dim + output_dim
