from __future__ import annotations

from dataclasses import asdict
import math
from pathlib import Path
import torch
from torch.utils.data import Dataset, DataLoader
from reference_model import ModelConfig, ByteTransformer, loss_nats

class ByteWindowDataset(Dataset):
    def __init__(self,data:bytes,context_length:int):
        self.data=torch.tensor(list(data),dtype=torch.long); self.context_length=context_length
    def __len__(self): return max(0,len(self.data)-self.context_length)
    def __getitem__(self,i): return self.data[i:i+self.context_length], self.data[i+1:i+self.context_length+1]

def evaluate_bpb(model,data:bytes,context_length:int,batch_size:int=32,device:str='cpu')->float:
    ds=ByteWindowDataset(data,context_length); loader=DataLoader(ds,batch_size=batch_size,shuffle=False,num_workers=0)
    if len(ds)==0: raise ValueError('dataset is too short')
    was_training=model.training; model.eval(); total_loss=0.0; total_tokens=0
    with torch.no_grad():
        for x,y in loader:
            x,y=x.to(device),y.to(device); loss=loss_nats(model(x),y)
            tokens=y.numel(); total_loss += float(loss.cpu())*tokens; total_tokens += tokens
    model.train(was_training)
    return (total_loss/total_tokens)/math.log(2.0)

def save_checkpoint(path,model,optimizer,step:int,config:ModelConfig,metrics:dict[str,float]):
    torch.save({'model_state':model.state_dict(),'optimizer_state':optimizer.state_dict() if optimizer else None,'step':step,'config':asdict(config),'metrics':metrics},path)

def load_checkpoint(path,model,optimizer=None,map_location='cpu'):
    payload=torch.load(path,map_location=map_location,weights_only=False); model.load_state_dict(payload['model_state'])
    if optimizer is not None and payload.get('optimizer_state') is not None: optimizer.load_state_dict(payload['optimizer_state'])
    return {'step':payload['step'],'config':payload['config'],'metrics':payload['metrics']}

def select_best_epoch(validation_bpb:list[float])->int:
    if not validation_bpb: raise ValueError('at least one validation value is required')
    return min(range(len(validation_bpb)),key=validation_bpb.__getitem__)
