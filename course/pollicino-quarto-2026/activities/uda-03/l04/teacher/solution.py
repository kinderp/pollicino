from __future__ import annotations
import random


def init_embedding(vocab_size: int=256, dim: int=4, seed: int=0, scale: float=0.1) -> list[list[float]]:
    if vocab_size <= 0 or dim <= 0: raise ValueError("dimensions must be positive")
    rng=random.Random(seed)
    return [[rng.uniform(-scale,scale) for _ in range(dim)] for _ in range(vocab_size)]


def lookup(table: list[list[float]], token: int) -> list[float]:
    if not 0 <= token < len(table): raise IndexError("token outside embedding table")
    return table[token].copy()


def lookup_sequence(table: list[list[float]], tokens: bytes | list[int]) -> list[list[float]]:
    return [lookup(table,int(token)) for token in tokens]


def parameter_count(table: list[list[float]]) -> int:
    return sum(len(row) for row in table)


def sgd_update_row(table: list[list[float]], token: int, gradient: list[float], learning_rate: float) -> None:
    row=lookup(table,token)
    if len(row) != len(gradient): raise ValueError("gradient dimension mismatch")
    if learning_rate <= 0: raise ValueError("learning rate must be positive")
    for i,g in enumerate(gradient):
        table[token][i] -= learning_rate*g
