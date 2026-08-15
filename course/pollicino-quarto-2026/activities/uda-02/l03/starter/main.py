from __future__ import annotations
import math
from pathlib import Path
ALPHABET_SIZE=256

def byte_counts(data:bytes)->list[int]:
    # TODO: conta le occorrenze di ciascuno dei 256 byte.
    raise NotImplementedError

def empirical_probabilities(data:bytes)->list[float]:
    # TODO: normalizza i conteggi.
    raise NotImplementedError

def smoothed_probabilities(data:bytes,alpha:float=1.0)->list[float]:
    # TODO: applica add-alpha smoothing.
    raise NotImplementedError

def entropy_bpb(data:bytes)->float:
    # TODO: H=-sum p*log2(p), ignorando p=0.
    raise NotImplementedError

def cross_entropy_bpb(data:bytes,model_probs:list[float])->float:
    # TODO: media di -log2(P(byte)) sui target osservati.
    raise NotImplementedError

def top_bytes(data:bytes,n:int=10)->list[tuple[int,int,float]]:
    if n<0: raise ValueError("n must be non-negative")
    counts=byte_counts(data); total=len(data); ranked=sorted(((v,c) for v,c in enumerate(counts) if c),key=lambda x:(-x[1],x[0]))[:n]
    return [(v,c,c/total if total else 0.0) for v,c in ranked]

def analyze_file(path:Path):
    data=path.read_bytes(); return {"bytes":len(data),"entropy_bpb":entropy_bpb(data),"top":top_bytes(data,10)}

if __name__=="__main__":
    for name in ("fixtures/italian.txt","fixtures/data.csv","fixtures/config.json","fixtures/pseudorandom.txt"): print(name,analyze_file(Path(name)))
