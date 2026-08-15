from __future__ import annotations
import hashlib,json
from collections import Counter,defaultdict
from collections.abc import Callable,Sequence
from .quantization import frequencies_to_cdf
CDFProvider=Callable[[int,Sequence[int]],Sequence[int]]
def uniform_cdf(alphabet_size:int=256,precision_bits:int=15)->list[int]:
    if alphabet_size<=0: raise ValueError('alphabet_size must be positive')
    total=1<<precision_bits; base,extra=divmod(total,alphabet_size)
    if base<=0: raise ValueError('precision too small for alphabet')
    return frequencies_to_cdf([base+(1 if i<extra else 0) for i in range(alphabet_size)])
def static_histogram_frequencies(data:bytes,precision_bits:int=15)->list[int]:
    total=1<<precision_bits; counts=Counter(data); raw=[counts[i] for i in range(256)]; mass=sum(raw)
    if mass==0: return [total//256]*256
    remaining=total-256; scaled=[v*remaining/mass for v in raw]; floors=[int(v) for v in scaled]; frequencies=[1+v for v in floors]
    leftover=total-sum(frequencies); order=sorted(range(256),key=lambda i:(-(scaled[i]-floors[i]),i))
    for i in order[:leftover]: frequencies[i]+=1
    return frequencies
class Order1CountModel:
    def __init__(self,training_data:bytes,precision_bits:int=15):
        self.precision_bits=precision_bits; self.total=1<<precision_bits; self.global_counts=[1]*256; self.transitions=defaultdict(lambda:[1]*256)
        for value in training_data: self.global_counts[value]+=1
        for a,b in zip(training_data,training_data[1:]): self.transitions[a][b]+=1
        self._global_cdf=frequencies_to_cdf(self._quantize_counts(self.global_counts)); self._cache={}
    def _quantize_counts(self,counts):
        mass=sum(counts); scaled=[v*self.total/mass for v in counts]; floors=[max(1,int(v)) for v in scaled]; current=sum(floors)
        if current>self.total:
            order=sorted(range(256),key=lambda i:(floors[i]<=1,-(floors[i]-scaled[i]),i))
            for i in order:
                while current>self.total and floors[i]>1: floors[i]-=1; current-=1
        elif current<self.total:
            order=sorted(range(256),key=lambda i:(-(scaled[i]-int(scaled[i])),i))
            for i in range(self.total-current): floors[order[i%256]]+=1
        assert sum(floors)==self.total and min(floors)>0; return floors
    def __call__(self,_index,prefix):
        if not prefix: return self._global_cdf
        previous=prefix[-1]
        if previous not in self._cache: self._cache[previous]=frequencies_to_cdf(self._quantize_counts(self.transitions[previous]))
        return self._cache[previous]
    def fingerprint(self)->bytes:
        payload={'type':'order1-count-v1','precision_bits':self.precision_bits,'global_counts':self.global_counts,'transitions':{str(k):v for k,v in sorted(self.transitions.items())}}
        return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).digest()
