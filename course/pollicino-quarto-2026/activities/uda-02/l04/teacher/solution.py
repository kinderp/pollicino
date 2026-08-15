from __future__ import annotations
from dataclasses import dataclass
import math
from pathlib import Path
VOCAB_SIZE=256
@dataclass
class NGramModel:
 order:int; context_counts:dict[bytes,list[int]]; global_counts:list[int]

def train_ngram(data,order=1):
 if order<0: raise ValueError("order must be >= 0")
 g=[0]*256
 for v in data:g[v]+=1
 c={}
 for i in range(order,len(data)):
  ctx=data[i-order:i] if order else b""; c.setdefault(ctx,[0]*256)[data[i]]+=1
 return NGramModel(order,c,g)

def context_distribution(model,context,alpha=0.5):
 if alpha<0: raise ValueError("alpha must be non-negative")
 ctx=context[-model.order:] if model.order else b""; counts=model.context_counts.get(ctx,model.global_counts); total=sum(counts); den=total+alpha*256
 if den==0:return [1/256]*256
 if alpha==0:return [x/total for x in counts]
 return [(x+alpha)/den for x in counts]

def next_byte_probability(model,context,target,alpha=0.5): return context_distribution(model,context,alpha)[target]

def evaluate_bpb(model,data,alpha=0.5):
 if len(data)<=model.order:return 0.0
 bits=0.0; n=0
 for i in range(model.order,len(data)):
  ctx=data[i-model.order:i] if model.order else b""; p=next_byte_probability(model,ctx,data[i],alpha)
  if p<=0:return math.inf
  bits+=-math.log2(p); n+=1
 return bits/n

def most_likely_next(model,context,alpha=0.5):
 probs=context_distribution(model,context,alpha); s=max(range(256),key=lambda v:(probs[v],-v)); return s,probs[s]

def compare_orders(train,test,max_order=3,alpha=0.5): return [(o,evaluate_bpb(train_ngram(train,o),test,alpha)) for o in range(max_order+1)]
if __name__=="__main__":
 train=Path("fixtures/train.txt").read_bytes(); test=Path("fixtures/test.txt").read_bytes()
 for o,bpb in compare_orders(train,test): print(f"order={o} test_bpb={bpb:.4f}")
