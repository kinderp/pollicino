from __future__ import annotations

def add_vectors(a,b):
    if len(a)!=len(b): raise ValueError("vectors must have the same length")
    return [x+y for x,y in zip(a,b)]

def combine_embeddings(token_rows,position_rows):
    if len(token_rows)!=len(position_rows): raise ValueError("token and position sequences must have the same length")
    return [add_vectors(t,p) for t,p in zip(token_rows,position_rows)]

def causal_mask(length):
    if length<0: raise ValueError("length must be non-negative")
    return [[j<=i for j in range(length)] for i in range(length)]

def context_windows(data,context_length):
    if context_length<=0: raise ValueError("context_length must be positive")
    return [(data[max(0,i-context_length):i],data[i]) for i in range(len(data))]
