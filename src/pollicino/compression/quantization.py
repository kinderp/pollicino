from __future__ import annotations
import math
from collections.abc import Sequence

def probabilities_to_frequencies(probabilities:Sequence[float],precision_bits:int=15)->list[int]:
    if not probabilities: raise ValueError("probabilities cannot be empty")
    if not 8<=precision_bits<=20: raise ValueError("precision_bits must be between 8 and 20")
    total=1<<precision_bits; n=len(probabilities)
    if total<=n: raise ValueError("precision is too small to give every symbol positive mass")
    if any((not math.isfinite(p)) or p<0 for p in probabilities): raise ValueError("probabilities must be finite and non-negative")
    mass=math.fsum(probabilities)
    if mass<=0: raise ValueError("probabilities must have positive total mass")
    normalized=[p/mass for p in probabilities]; remaining=total-n; raw=[p*remaining for p in normalized]; floors=[math.floor(v) for v in raw]; frequencies=[1+v for v in floors]
    leftover=total-sum(frequencies); ranking=sorted(range(n),key=lambda i:(-(raw[i]-floors[i]),i))
    for i in ranking[:leftover]: frequencies[i]+=1
    assert sum(frequencies)==total and all(v>0 for v in frequencies); return frequencies

def frequencies_to_cdf(frequencies:Sequence[int])->list[int]:
    if not frequencies or any((not isinstance(v,int)) or v<=0 for v in frequencies): raise ValueError("frequencies must be positive integers")
    cdf=[0]; running=0
    for value in frequencies: running+=value; cdf.append(running)
    return cdf
