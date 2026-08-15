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


from pathlib import Path
from torch.utils.data import Dataset, DataLoader

class ByteWindowDataset(Dataset):
    def __init__(self,data:bytes,context_length:int):
        self.data=torch.tensor(list(data),dtype=torch.long); self.context_length=context_length
    def __len__(self): return max(0,len(self.data)-self.context_length)
    def __getitem__(self,i):
        return self.data[i:i+self.context_length], self.data[i+1:i+self.context_length+1]

def resolve_device(preferred:str|None=None):
    if preferred is not None: return torch.device(preferred)
    if torch.cuda.is_available(): return torch.device('cuda')
    if torch.backends.mps.is_available(): return torch.device('mps')
    return torch.device('cpu')

def train_steps(data:bytes,cfg:ModelConfig,steps:int=30,batch_size:int=16,lr:float=3e-3,device:str|None='cpu',seed:int=1337):
    torch.manual_seed(seed); dev=resolve_device(device)
    model=ByteTransformer(cfg).to(dev); ds=ByteWindowDataset(data,cfg.context_length)
    if len(ds)==0: raise ValueError('dataset is too short')
    g=torch.Generator().manual_seed(seed)
    loader=DataLoader(ds,batch_size=batch_size,shuffle=True,num_workers=0,generator=g)
    opt=torch.optim.AdamW(model.parameters(),lr=lr)
    history=[]; it=iter(loader)
    model.train()
    for _ in range(steps):
        try: x,y=next(it)
        except StopIteration: it=iter(loader); x,y=next(it)
        x,y=x.to(dev),y.to(dev); opt.zero_grad(set_to_none=True)
        loss=loss_nats(model(x),y); loss.backward(); opt.step(); history.append(float(loss.detach().cpu()))
    return model,history

def main():
    data=Path('fixtures/corpus.txt').read_bytes(); cfg=ModelConfig()
    model,h=train_steps(data,cfg,steps=20)
    print('device',next(model.parameters()).device,'params',count_parameters(model),'loss',h[-1],'bpb',bits_per_byte(h[-1]))

if __name__=='__main__': main()
