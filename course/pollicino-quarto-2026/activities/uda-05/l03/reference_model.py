from __future__ import annotations

from dataclasses import dataclass
import math
import torch
from torch import nn
import torch.nn.functional as F

@dataclass(frozen=True)
class ModelConfig:
    vocab_size: int = 256
    context_length: int = 32
    d_model: int = 32
    n_heads: int = 4
    n_layers: int = 2
    d_ff: int = 64
    dropout: float = 0.0

    def __post_init__(self):
        if self.d_model % self.n_heads != 0:
            raise ValueError("d_model must be divisible by n_heads")
        if self.context_length <= 0:
            raise ValueError("context_length must be positive")

class CausalSelfAttention(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.n_heads=cfg.n_heads
        self.head_dim=cfg.d_model//cfg.n_heads
        self.qkv=nn.Linear(cfg.d_model,3*cfg.d_model)
        self.proj=nn.Linear(cfg.d_model,cfg.d_model)

    def forward(self,x):
        b,t,c=x.shape
        q,k,v=self.qkv(x).chunk(3,dim=-1)
        def split(z): return z.view(b,t,self.n_heads,self.head_dim).transpose(1,2)
        q,k,v=map(split,(q,k,v))
        scores=(q @ k.transpose(-2,-1))/math.sqrt(self.head_dim)
        mask=torch.triu(torch.ones(t,t,dtype=torch.bool,device=x.device),diagonal=1)
        scores=scores.masked_fill(mask,float('-inf'))
        weights=F.softmax(scores,dim=-1)
        out=weights @ v
        out=out.transpose(1,2).contiguous().view(b,t,c)
        return self.proj(out)

class Block(nn.Module):
    def __init__(self,cfg:ModelConfig):
        super().__init__()
        self.ln1=nn.LayerNorm(cfg.d_model,eps=1e-5)
        self.attn=CausalSelfAttention(cfg)
        self.ln2=nn.LayerNorm(cfg.d_model,eps=1e-5)
        self.ff=nn.Sequential(nn.Linear(cfg.d_model,cfg.d_ff),nn.GELU(),nn.Linear(cfg.d_ff,cfg.d_model))
    def forward(self,x):
        x=x+self.attn(self.ln1(x))
        return x+self.ff(self.ln2(x))

class ByteTransformer(nn.Module):
    def __init__(self,cfg:ModelConfig):
        super().__init__(); self.cfg=cfg
        self.token_embedding=nn.Embedding(cfg.vocab_size,cfg.d_model)
        self.position_embedding=nn.Embedding(cfg.context_length,cfg.d_model)
        self.blocks=nn.ModuleList([Block(cfg) for _ in range(cfg.n_layers)])
        self.norm=nn.LayerNorm(cfg.d_model,eps=1e-5)
        self.lm_head=nn.Linear(cfg.d_model,cfg.vocab_size)
    def forward(self,idx):
        b,t=idx.shape
        if t>self.cfg.context_length: raise ValueError("sequence exceeds context_length")
        pos=torch.arange(t,device=idx.device)
        x=self.token_embedding(idx)+self.position_embedding(pos)[None,:,:]
        for block in self.blocks: x=block(x)
        return self.lm_head(self.norm(x))

def loss_nats(logits,targets):
    return F.cross_entropy(logits.reshape(-1,logits.shape[-1]), targets.reshape(-1))

def bits_per_byte(loss_value): return float(loss_value)/math.log(2.0)
def count_parameters(model): return sum(p.numel() for p in model.parameters())
