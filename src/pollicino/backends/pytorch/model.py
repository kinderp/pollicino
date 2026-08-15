from __future__ import annotations
import math
import torch
from torch import nn
import torch.nn.functional as F
from pollicino.model_spec import ModelSpec

class CausalSelfAttention(nn.Module):
    def __init__(self,spec:ModelSpec)->None:
        super().__init__(); self.n_heads=spec.n_heads; self.head_dim=spec.head_dim; self.qkv=nn.Linear(spec.d_model,3*spec.d_model); self.proj=nn.Linear(spec.d_model,spec.d_model)
    def forward(self,x:torch.Tensor)->torch.Tensor:
        b,t,c=x.shape; q,k,v=self.qkv(x).chunk(3,dim=-1)
        def split(z): return z.view(b,t,self.n_heads,self.head_dim).transpose(1,2)
        q,k,v=(split(z) for z in (q,k,v)); scores=(q@k.transpose(-2,-1))/math.sqrt(self.head_dim)
        future=torch.triu(torch.ones(t,t,dtype=torch.bool,device=x.device),diagonal=1); scores=scores.masked_fill(future,float('-inf'))
        out=F.softmax(scores,dim=-1)@v; out=out.transpose(1,2).contiguous().view(b,t,c); return self.proj(out)

class Block(nn.Module):
    def __init__(self,spec:ModelSpec)->None:
        super().__init__(); self.norm1=nn.LayerNorm(spec.d_model,eps=spec.layer_norm_eps); self.attention=CausalSelfAttention(spec); self.norm2=nn.LayerNorm(spec.d_model,eps=spec.layer_norm_eps); self.feed_forward=nn.Sequential(nn.Linear(spec.d_model,spec.d_ff),nn.GELU(),nn.Linear(spec.d_ff,spec.d_model))
    def forward(self,x): x=x+self.attention(self.norm1(x)); return x+self.feed_forward(self.norm2(x))

class ByteTransformer(nn.Module):
    def __init__(self,spec:ModelSpec=ModelSpec())->None:
        super().__init__(); self.spec=spec; self.token_embedding=nn.Embedding(spec.vocab_size,spec.d_model); self.position_embedding=nn.Embedding(spec.context_length,spec.d_model); self.blocks=nn.ModuleList([Block(spec) for _ in range(spec.n_layers)]); self.norm=nn.LayerNorm(spec.d_model,eps=spec.layer_norm_eps); self.lm_head=nn.Linear(spec.d_model,spec.vocab_size)
    def forward(self,indices):
        _,t=indices.shape
        if t>self.spec.context_length: raise ValueError('sequence exceeds context_length')
        pos=torch.arange(t,device=indices.device); x=self.token_embedding(indices)+self.position_embedding(pos)[None,:,:]
        for block in self.blocks: x=block(x)
        return self.lm_head(self.norm(x))

def loss_nats(logits,targets): return F.cross_entropy(logits.reshape(-1,logits.shape[-1]),targets.reshape(-1))
def bits_per_byte(loss_value:float)->float: return float(loss_value)/math.log(2.0)
def parameter_count(model:nn.Module)->int: return sum(p.numel() for p in model.parameters())
