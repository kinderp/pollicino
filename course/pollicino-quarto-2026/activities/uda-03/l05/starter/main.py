from __future__ import annotations
import math, random

VOCAB_SIZE=256


def softmax(logits: list[float]) -> list[float]:
    m=max(logits); e=[math.exp(x-m) for x in logits]; s=sum(e); return [x/s for x in e]


def make_examples(data: bytes, context_size: int=2) -> list[tuple[list[int],int]]:
    if context_size <= 0: raise ValueError("context_size must be positive")
    raise NotImplementedError


def init_model(context_size: int=2, embedding_dim: int=4, hidden_dim: int=8, seed: int=0, scale: float=0.08) -> dict:
    if min(context_size,embedding_dim,hidden_dim) <= 0: raise ValueError("dimensions must be positive")
    raise NotImplementedError


def forward(model: dict, context: list[int]) -> tuple[list[float],dict]:
    if len(context) != model['context_size']: raise ValueError("wrong context length")
    raise NotImplementedError


def loss_bits(model: dict, examples: list[tuple[list[int],int]]) -> float:
    if not examples: return 0.0
    raise NotImplementedError


def train_step(model: dict, context: list[int], target: int, learning_rate: float=0.05) -> float:
    """One SGD step. Complete this after deriving the gradients in class."""
    raise NotImplementedError


def train(model: dict, data: bytes, epochs: int=5, learning_rate: float=0.05) -> list[float]:
    examples=make_examples(data,model['context_size'])
    history=[]
    for _ in range(epochs):
        for context,target in examples: train_step(model,context,target,learning_rate)
        history.append(loss_bits(model,examples))
    return history


def uniform_bpb() -> float: return 8.0


def bigram_bpb(train_data: bytes, test_data: bytes, alpha: float=1.0) -> float:
    if alpha <= 0: raise ValueError("alpha must be positive")
    counts=[[0]*VOCAB_SIZE for _ in range(VOCAB_SIZE)]
    totals=[0]*VOCAB_SIZE
    for a,b in zip(train_data,train_data[1:]): counts[a][b]+=1; totals[a]+=1
    if len(test_data)<2: return 0.0
    bits=0.0
    for a,b in zip(test_data,test_data[1:]):
        p=(counts[a][b]+alpha)/(totals[a]+alpha*VOCAB_SIZE)
        bits += -math.log2(p)
    return bits/(len(test_data)-1)
