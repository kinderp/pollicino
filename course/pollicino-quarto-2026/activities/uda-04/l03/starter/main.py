import math
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def softmax(v):
 if not v:return []
 m=max(v);e=[math.exp(x-m) for x in v];s=sum(e);return [x/s for x in e]
def causal_attention(q,k,v):
 # TODO: per riga i rendi visibili solo posizioni j<=i.
 raise NotImplementedError
def future_leakage_check(a,b,projector,prefix_length):
 # TODO: gli output del prefisso devono rimanere identici se cambia solo il futuro.
 raise NotImplementedError
def identity_projector(sequence):
 rows=[[float(x)] for x in sequence];return rows,rows,rows
