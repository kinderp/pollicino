from __future__ import annotations
import math
VOCAB_SIZE=256

def train_counts(data:bytes,order:int):
 contexts={}; global_counts=[0]*256
 for v in data: global_counts[v]+=1
 for i in range(order,len(data)):
  ctx=data[i-order:i] if order else b""; contexts.setdefault(ctx,[0]*256)[data[i]]+=1
 return contexts,global_counts

def evaluate_ngram_bpb(train:bytes,test:bytes,order:int,alpha:float=0.5)->float:
 if order<0: raise ValueError("order must be >= 0")
 if len(test)<=order:return 0.0
 contexts,global_counts=train_counts(train,order); bits=0.0; n=0
 for i in range(order,len(test)):
  ctx=test[i-order:i] if order else b""; counts=contexts.get(ctx,global_counts); den=sum(counts)+alpha*256
  p=1/256 if den==0 else (counts[test[i]]+alpha)/den
  bits+=-math.log2(p); n+=1
 return bits/n
