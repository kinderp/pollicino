from __future__ import annotations
import math
def dot(a,b): raise NotImplementedError
def linear(rows,weight): raise NotImplementedError
def softmax(values): raise NotImplementedError
def single_head_attention(x,wq,wk,wv):
    # Q,K,V -> QK^T/sqrt(d) -> softmax -> weights V
    raise NotImplementedError
