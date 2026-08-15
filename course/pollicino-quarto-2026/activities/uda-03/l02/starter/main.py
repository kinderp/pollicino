from __future__ import annotations
import math


def softmax(logits: list[float]) -> list[float]:
    if not logits:
        raise ValueError("softmax needs at least one logit")
    raise NotImplementedError


def predicted_class(logits: list[float]) -> int:
    if not logits:
        raise ValueError("at least one logit is required")
    raise NotImplementedError


def probability_of(logits: list[float], target: int) -> float:
    if not 0 <= target < len(logits):
        raise IndexError("target outside logits")
    raise NotImplementedError


def entropy_bits(probabilities: list[float]) -> float:
    total = sum(probabilities)
    if not math.isclose(total, 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError("probabilities must sum to one")
    if any(p < 0 for p in probabilities):
        raise ValueError("probabilities cannot be negative")
    raise NotImplementedError
