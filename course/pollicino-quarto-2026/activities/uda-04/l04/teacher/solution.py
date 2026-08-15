import math
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def softmax(v):
 if not v:return []
 m=max(v);e=[math.exp(x-m) for x in v];s=sum(e);return [x/s for x in e]
def linear(rows,w,b=None):
 if not rows:return []
 o=len(w[0]);b=b or [0.]*o;return [[b[j]+sum(r[k]*w[k][j] for k in range(len(w))) for j in range(o)] for r in rows]
def rms_norm_row(row,eps=1e-6):
 if not row:return []
 rms=math.sqrt(sum(x*x for x in row)/len(row)+eps);return [x/rms for x in row]
def rms_norm(rows,eps=1e-6):return [rms_norm_row(r,eps) for r in rows]
def add_rows(a,b):return [[x+y for x,y in zip(ra,rb)] for ra,rb in zip(a,b)]
def causal_head(x,wq,wk,wv):
 q=linear(x,wq);k=linear(x,wk);v=linear(x,wv);scale=math.sqrt(len(q[0]));out=[]
 for i,qi in enumerate(q):
  p=softmax([dot(qi,kj)/scale for kj in k[:i+1]]);out.append([sum(p[j]*v[j][c] for j in range(i+1)) for c in range(len(v[0]))])
 return out
def multi_head_attention(x,heads,wo):
 outs=[causal_head(x,*h) for h in heads];joined=[]
 for i in range(len(x)):
  row=[]
  for h in outs:row.extend(h[i])
  joined.append(row)
 return linear(joined,wo)
def feed_forward(x,w1,b1,w2,b2):
 h=linear(x,w1,b1);h=[[max(0.,v) for v in r] for r in h];return linear(h,w2,b2)
def transformer_block(x,heads,wo,w1,b1,w2,b2):
 a=multi_head_attention(rms_norm(x),heads,wo);x=add_rows(x,a);f=feed_forward(rms_norm(x),w1,b1,w2,b2);return add_rows(x,f)
def identity_matrix(n):return [[1. if i==j else 0. for j in range(n)] for i in range(n)]
def demo_params():
 wq1=[[1,0],[0,1],[0,0],[0,0]];wq2=[[0,0],[0,0],[1,0],[0,1]];heads=[(wq1,wq1,wq1),(wq2,wq2,wq2)];wo=identity_matrix(4);w1=[[.1*(1+i+j) for j in range(6)] for i in range(4)];w2=[[.03*(1+i+j) for j in range(4)] for i in range(6)];return heads,wo,w1,[0.]*6,w2,[0.]*4
