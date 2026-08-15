from __future__ import annotations


def affine_scalar(x: float, weight: float, bias: float) -> float:
    raise NotImplementedError


def dot(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("vectors must have the same length")
    raise NotImplementedError


def linear_logits(features: list[float], weights: list[list[float]], biases: list[float]) -> list[float]:
    if len(weights) != len(biases):
        raise ValueError("one bias is required per output")
    raise NotImplementedError


def parameter_count(input_dim: int, output_dim: int) -> int:
    if input_dim < 0 or output_dim < 0:
        raise ValueError("dimensions must be non-negative")
    raise NotImplementedError
