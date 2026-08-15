import math
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def softmax(v):
 if not v:return []
 m=max(v);e=[math.exp(x-m) for x in v];s=sum(e);return [x/s for x in e]
def linear(rows,w,b=None):
 if not rows:return []
 o=len(w[0]);b=b or [0.]*o;return [[b[j]+sum(r[k]*w[k][j] for k in range(len(w))) for j in range(o)] for r in rows]
def rms_norm_row(row,eps=1e-6): raise NotImplementedError
def rms_norm(rows,eps=1e-6): return [rms_norm_row(r,eps) for r in rows]
def add_rows(a,b):return [[x+y for x,y in zip(ra,rb)] for ra,rb in zip(a,b)]
def causal_head(x,wq,wk,wv):
 q=linear(x,wq);k=linear(x,wk);v=linear(x,wv);scale=math.sqrt(len(q[0]));out=[]
 for i,qi in enumerate(q):
  p=softmax([dot(qi,kj)/scale for kj in k[:i+1]]);out.append([sum(p[j]*v[j][c] for j in range(i+1)) for c in range(len(v[0]))])
 return out
def multi_head_attention(x,heads,wo): raise NotImplementedError
def feed_forward(x,w1,b1,w2,b2):
 h=linear(x,w1,b1);h=[[max(0.,v) for v in r] for r in h];return linear(h,w2,b2)
def transformer_block(x,heads,wo,w1,b1,w2,b2): raise NotImplementedError
