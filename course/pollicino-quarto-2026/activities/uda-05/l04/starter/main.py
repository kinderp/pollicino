from __future__ import annotations

from dataclasses import dataclass
import math, random
try:
    import mlx.core as mx
    import mlx.nn as nn
    import mlx.optimizers as optim
except ModuleNotFoundError:
    mx=nn=optim=None

@dataclass(frozen=True)
class ModelConfig:
    vocab_size:int=256; context_length:int=32; d_model:int=32; n_heads:int=4; n_layers:int=2; d_ff:int=64
    def __post_init__(self):
        if self.d_model % self.n_heads != 0: raise ValueError('d_model must be divisible by n_heads')

def mlx_available()->bool: return mx is not None

def expected_parameter_count(cfg:ModelConfig)->int:
    # embeddings + each block(qkv/proj/2xLN/ff) + final LN + lm head
    emb=cfg.vocab_size*cfg.d_model + cfg.context_length*cfg.d_model
    block=(cfg.d_model*3*cfg.d_model + 3*cfg.d_model) + (cfg.d_model*cfg.d_model+cfg.d_model) + 4*cfg.d_model + (cfg.d_model*cfg.d_ff+cfg.d_ff) + (cfg.d_ff*cfg.d_model+cfg.d_model)
    tail=2*cfg.d_model + cfg.d_model*cfg.vocab_size + cfg.vocab_size
    return emb + cfg.n_layers*block + tail

if nn is not None:
    class CausalSelfAttention(nn.Module):
        def __init__(self,cfg):
            super().__init__(); self.n_heads=cfg.n_heads; self.head_dim=cfg.d_model//cfg.n_heads; self.qkv=nn.Linear(cfg.d_model,3*cfg.d_model); self.proj=nn.Linear(cfg.d_model,cfg.d_model)
        def __call__(self,x):
            # TODO: reproduce the same Q/K/V attention used in the PyTorch backend
            raise NotImplementedError
    class Block(nn.Module):
        def __init__(self,cfg):
            super().__init__(); self.ln1=nn.LayerNorm(cfg.d_model,eps=1e-5); self.attn=CausalSelfAttention(cfg); self.ln2=nn.LayerNorm(cfg.d_model,eps=1e-5); self.ff1=nn.Linear(cfg.d_model,cfg.d_ff); self.ff2=nn.Linear(cfg.d_ff,cfg.d_model)
        def __call__(self,x):
            x=x+self.attn(self.ln1(x)); return x+self.ff2(nn.gelu(self.ff1(self.ln2(x))))
    class ByteTransformer(nn.Module):
        def __init__(self,cfg):
            super().__init__(); self.cfg=cfg; self.token_embedding=nn.Embedding(cfg.vocab_size,cfg.d_model); self.position_embedding=nn.Embedding(cfg.context_length,cfg.d_model); self.blocks=[Block(cfg) for _ in range(cfg.n_layers)]; self.norm=nn.LayerNorm(cfg.d_model,eps=1e-5); self.lm_head=nn.Linear(cfg.d_model,cfg.vocab_size)
        def __call__(self,idx):
            b,t=idx.shape
            if t>self.cfg.context_length: raise ValueError('sequence exceeds context_length')
            x=self.token_embedding(idx)+self.position_embedding(mx.arange(t))[None,:,:]
            for block in self.blocks: x=block(x)
            return self.lm_head(self.norm(x))
else:
    class ByteTransformer:
        def __init__(self,*_args,**_kwargs): raise RuntimeError('MLX is not installed; run this lesson on Apple Silicon with MLX')

def make_windows(data:bytes,context_length:int):
    return [(list(data[i:i+context_length]),list(data[i+1:i+context_length+1])) for i in range(max(0,len(data)-context_length))]

def batch_iter(examples,batch_size,seed=0):
    ids=list(range(len(examples))); random.Random(seed).shuffle(ids)
    for s in range(0,len(ids),batch_size):
        chunk=[examples[i] for i in ids[s:s+batch_size]]; yield [x for x,_ in chunk],[y for _,y in chunk]

def loss_fn(model,x,y):
    logits=model(x); return nn.losses.cross_entropy(logits.reshape((-1,logits.shape[-1])), y.reshape((-1,)), reduction='mean')

def train_steps(data:bytes,cfg:ModelConfig,steps:int=20,batch_size:int=16,lr:float=3e-3,seed:int=1337):
    if not mlx_available(): raise RuntimeError('MLX is required')
    mx.random.seed(seed); model=ByteTransformer(cfg); mx.eval(model.parameters()); optimizer=optim.AdamW(learning_rate=lr); loss_and_grad=nn.value_and_grad(model,loss_fn)
    examples=make_windows(data,cfg.context_length)
    if not examples: raise ValueError('dataset is too short')
    history=[]; batches=list(batch_iter(examples,batch_size,seed=seed)); bi=0
    for _ in range(steps):
        xs,ys=batches[bi%len(batches)]; bi+=1; x=mx.array(xs); y=mx.array(ys)
        loss,grads=loss_and_grad(model,x,y); optimizer.update(model,grads); mx.eval(model.parameters(),optimizer.state,loss); history.append(float(loss.item()))
    return model,history
