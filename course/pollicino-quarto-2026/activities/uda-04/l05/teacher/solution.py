from __future__ import annotations
import math,random

def softmax(v):
 if not v:return []
 m=max(v);e=[math.exp(x-m) for x in v];s=sum(e);return [x/s for x in e]
def linear(rows,w,b=None):
 if not rows:return []
 o=len(w[0]);b=b or [0.]*o;return [[b[j]+sum(r[k]*w[k][j] for k in range(len(w))) for j in range(o)] for r in rows]
def rms_norm(rows,eps=1e-6):
 out=[]
 for r in rows:
  s=math.sqrt(sum(x*x for x in r)/len(r)+eps);out.append([x/s for x in r])
 return out
def add_rows(a,b):return [[x+y for x,y in zip(ra,rb)] for ra,rb in zip(a,b)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def causal_head(x,wq,wk,wv):
 q=linear(x,wq);k=linear(x,wk);v=linear(x,wv);scale=math.sqrt(len(q[0]));out=[]
 for i,qi in enumerate(q):
  p=softmax([dot(qi,kj)/scale for kj in k[:i+1]]);out.append([sum(p[j]*v[j][c] for j in range(i+1)) for c in range(len(v[0]))])
 return out
def mha(x,heads,wo):
 outs=[causal_head(x,*h) for h in heads];joined=[]
 for i in range(len(x)):
  row=[]
  for h in outs:row.extend(h[i])
  joined.append(row)
 return linear(joined,wo)
def ffn(x,w1,b1,w2,b2):
 h=linear(x,w1,b1);h=[[max(0.,v) for v in r] for r in h];return linear(h,w2,b2)
def block(x,p):
 a=mha(rms_norm(x),p['heads'],p['wo']);x=add_rows(x,a);f=ffn(rms_norm(x),p['w1'],p['b1'],p['w2'],p['b2']);return add_rows(x,f)
class TinyByteTransformer:
 def __init__(self,d_model=8,n_heads=2,d_ff=16,n_layers=1,context_length=8,seed=7):
  if d_model%n_heads:raise ValueError('d_model must be divisible by n_heads')
  self.d_model=d_model;self.n_heads=n_heads;self.d_ff=d_ff;self.n_layers=n_layers;self.context_length=context_length;rng=random.Random(seed)
  def matrix(a,b,scale=.08):return [[rng.gauss(0.,scale) for _ in range(b)] for _ in range(a)]
  self.token_embedding=matrix(256,d_model);self.position_embedding=matrix(context_length,d_model);self.layers=[];dh=d_model//n_heads
  for _ in range(n_layers):
   heads=[(matrix(d_model,dh),matrix(d_model,dh),matrix(d_model,dh)) for _ in range(n_heads)];self.layers.append({'heads':heads,'wo':matrix(d_model,d_model),'w1':matrix(d_model,d_ff),'b1':[0.]*d_ff,'w2':matrix(d_ff,d_model),'b2':[0.]*d_model})
  self.lm_head=matrix(d_model,256)
 def embed(self,tokens):
  if len(tokens)>self.context_length:raise ValueError('sequence exceeds context_length')
  if any(not 0<=t<=255 for t in tokens):raise ValueError('tokens must be bytes')
  return [[self.token_embedding[t][j]+self.position_embedding[i][j] for j in range(self.d_model)] for i,t in enumerate(tokens)]
 def forward(self,tokens):
  x=self.embed(tokens)
  for p in self.layers:x=block(x,p)
  return linear(rms_norm(x),self.lm_head)
 def probabilities(self,tokens):return [softmax(r) for r in self.forward(tokens)]
 def next_byte_bpb(self,data):
  if len(data)<2:return 0.
  tok=list(data);total=0.;count=0
  for end in range(1,len(tok)):
   start=max(0,end-self.context_length);p=softmax(self.forward(tok[start:end])[-1])[tok[end]];total+=-math.log2(p);count+=1
  return total/count
 def parameter_count(self):
  total=256*self.d_model+self.context_length*self.d_model+self.d_model*256;dh=self.d_model//self.n_heads;per=self.n_heads*3*self.d_model*dh+self.d_model*self.d_model+self.d_model*self.d_ff+self.d_ff+self.d_ff*self.d_model+self.d_model;return total+self.n_layers*per
def causal_prefix_equal(model,a,b,prefix_length,tol=1e-12):
 if a[:prefix_length]!=b[:prefix_length]:raise ValueError('prefixes differ')
 la=model.forward(a);lb=model.forward(b);return all(abs(x-y)<=tol for i in range(prefix_length) for x,y in zip(la[i],lb[i]))
