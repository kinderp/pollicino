import math
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def softmax(v):
 if not v:return []
 m=max(v);e=[math.exp(x-m) for x in v];s=sum(e);return [x/s for x in e]
def causal_attention(q,k,v):
 if not(len(q)==len(k)==len(v)): raise ValueError("q, k and v must have the same sequence length")
 if not q:return [],[]
 scale=math.sqrt(len(q[0]));outs=[];rows=[]
 for i,qi in enumerate(q):
  visible=softmax([dot(qi,kj)/scale for kj in k[:i+1]]);weights=visible+[0.0]*(len(k)-i-1)
  outs.append([sum(weights[j]*v[j][c] for j in range(len(v))) for c in range(len(v[0]))]);rows.append(weights)
 return outs,rows
def future_leakage_check(a,b,projector,prefix_length):
 if a[:prefix_length]!=b[:prefix_length]: raise ValueError("sequences must share the tested prefix")
 oa,_=causal_attention(*projector(a));ob,_=causal_attention(*projector(b))
 return all(all(abs(x-y)<1e-12 for x,y in zip(oa[i],ob[i])) for i in range(prefix_length))
def identity_projector(sequence):
 rows=[[float(x)] for x in sequence];return rows,rows,rows
