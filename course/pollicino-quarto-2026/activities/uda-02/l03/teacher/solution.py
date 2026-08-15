from __future__ import annotations
import math
from pathlib import Path
ALPHABET_SIZE=256

def byte_counts(data):
    counts=[0]*256
    for v in data: counts[v]+=1
    return counts

def empirical_probabilities(data):
    counts=byte_counts(data); total=len(data)
    return [0.0]*256 if total==0 else [c/total for c in counts]

def smoothed_probabilities(data,alpha=1.0):
    if alpha<0: raise ValueError("alpha must be non-negative")
    counts=byte_counts(data); den=len(data)+alpha*256
    if den==0:return [1/256]*256
    return [(c+alpha)/den for c in counts]

def entropy_bpb(data):
    return -sum(p*math.log2(p) for p in empirical_probabilities(data) if p>0)

def cross_entropy_bpb(data,model_probs):
    if len(model_probs)!=256: raise ValueError("model_probs must contain 256 probabilities")
    if not data:return 0.0
    bits=0.0
    for v in data:
        p=model_probs[v]
        if p<=0:return math.inf
        bits+=-math.log2(p)
    return bits/len(data)

def top_bytes(data,n=10):
    if n<0:raise ValueError("n must be non-negative")
    counts=byte_counts(data); total=len(data); ranked=sorted(((v,c) for v,c in enumerate(counts) if c),key=lambda x:(-x[1],x[0]))[:n]
    return [(v,c,c/total if total else 0.0) for v,c in ranked]

def analyze_file(path):
    data=Path(path).read_bytes(); return {"bytes":len(data),"entropy_bpb":entropy_bpb(data),"top":top_bytes(data,10)}
if __name__=="__main__":
    for name in ("fixtures/italian.txt","fixtures/data.csv","fixtures/config.json","fixtures/pseudorandom.txt"): print(name,analyze_file(name))
