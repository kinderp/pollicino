from __future__ import annotations
import math
import mlx.core as mx
import mlx.nn as nn
from pollicino.model_spec import ModelSpec

class CausalSelfAttention(nn.Module):
    def __init__(self,spec:ModelSpec)->None:
        super().__init__(); self.n_heads=spec.n_heads; self.head_dim=spec.head_dim; self.qkv=nn.Linear(spec.d_model,3*spec.d_model); self.proj=nn.Linear(spec.d_model,spec.d_model)
    def __call__(self,x):
        b,t,c=x.shape; q,k,v=mx.split(self.qkv(x),3,axis=-1)
        def split(z): return mx.transpose(mx.reshape(z,(b,t,self.n_heads,self.head_dim)),(0,2,1,3))
        q,k,v=(split(z) for z in (q,k,v)); scores=(q@mx.swapaxes(k,-1,-2))/math.sqrt(self.head_dim)
        future=mx.arange(t)[None,:]>mx.arange(t)[:,None]; scores=mx.where(future[None,None,:,:],-1e9,scores)
        out=mx.softmax(scores,axis=-1)@v; out=mx.reshape(mx.transpose(out,(0,2,1,3)),(b,t,c)); return self.proj(out)

class Block(nn.Module):
    def __init__(self,spec:ModelSpec)->None:
        super().__init__(); self.norm1=nn.LayerNorm(spec.d_model,eps=spec.layer_norm_eps); self.attention=CausalSelfAttention(spec); self.norm2=nn.LayerNorm(spec.d_model,eps=spec.layer_norm_eps); self.ff1=nn.Linear(spec.d_model,spec.d_ff); self.ff2=nn.Linear(spec.d_ff,spec.d_model)
    def __call__(self,x): x=x+self.attention(self.norm1(x)); return x+self.ff2(nn.gelu(self.ff1(self.norm2(x))))

class ByteTransformer(nn.Module):
    def __init__(self,spec:ModelSpec=ModelSpec())->None:
        super().__init__(); self.spec=spec; self.token_embedding=nn.Embedding(spec.vocab_size,spec.d_model); self.position_embedding=nn.Embedding(spec.context_length,spec.d_model); self.blocks=[Block(spec) for _ in range(spec.n_layers)]; self.norm=nn.LayerNorm(spec.d_model,eps=spec.layer_norm_eps); self.lm_head=nn.Linear(spec.d_model,spec.vocab_size)
    def __call__(self,indices):
        _,t=indices.shape
        if t>self.spec.context_length: raise ValueError('sequence exceeds context_length')
        x=self.token_embedding(indices)+self.position_embedding(mx.arange(t))[None,:,:]
        for block in self.blocks: x=block(x)
        return self.lm_head(self.norm(x))

def loss_nats(model:ByteTransformer,indices,targets):
    logits=model(indices); return nn.losses.cross_entropy(logits.reshape((-1,logits.shape[-1])),targets.reshape((-1,)),reduction='mean')
