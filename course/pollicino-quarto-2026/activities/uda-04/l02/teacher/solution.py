import math
def dot(a,b):
 if len(a)!=len(b): raise ValueError("dimension mismatch")
 return sum(x*y for x,y in zip(a,b))
def linear(rows,w):
 if not rows:return []
 return [[sum(row[k]*w[k][j] for k in range(len(w))) for j in range(len(w[0]))] for row in rows]
def softmax(v):
 if not v:return []
 m=max(v);e=[math.exp(x-m) for x in v];s=sum(e);return [x/s for x in e]
def single_head_attention(x,wq,wk,wv):
 q=linear(x,wq);k=linear(x,wk);v=linear(x,wv)
 if not q:return [],[]
 scale=math.sqrt(len(q[0]));scores=[[dot(qi,kj)/scale for kj in k] for qi in q];weights=[softmax(r) for r in scores]
 out=[[sum(weights[i][j]*v[j][c] for j in range(len(v))) for c in range(len(v[0]))] for i in range(len(v))]
 return out,weights
