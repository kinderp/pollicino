from __future__ import annotations
import math


def softmax(logits: list[float]) -> list[float]:
    m=max(logits)
    e=[math.exp(x-m) for x in logits]
    s=sum(e)
    return [x/s for x in e]


def cross_entropy(logits: list[float], target: int) -> float:
    if not 0 <= target < len(logits):
        raise IndexError("invalid target")
    raise NotImplementedError


def cross_entropy_gradient(logits: list[float], target: int) -> list[float]:
    raise NotImplementedError


def numerical_gradient(function, x: float, eps: float=1e-6) -> float:
    if eps <= 0: raise ValueError("eps must be positive")
    raise NotImplementedError


def gradient_descent(start: float, gradient, learning_rate: float, steps: int) -> list[float]:
    if learning_rate <= 0: raise ValueError("learning_rate must be positive")
    if steps < 0: raise ValueError("steps must be non-negative")
    raise NotImplementedError
