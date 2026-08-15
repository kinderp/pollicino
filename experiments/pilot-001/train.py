from __future__ import annotations

import argparse
import copy
import json
import math
import random
import sys
from pathlib import Path

import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from pollicino.model_spec import ModelSpec, expected_parameter_count
from pollicino.backends.pytorch.model import ByteTransformer, parameter_count


def random_batch(data: bytes, spec: ModelSpec, batch_size: int, rng: random.Random):
    max_start = len(data) - spec.context_length - 1
    if max_start < 0:
        raise ValueError('dataset too small')
    xs=[]; ys=[]
    for _ in range(batch_size):
        start=rng.randint(0,max_start)
        xs.append(list(data[start:start+spec.context_length]))
        ys.append(list(data[start+1:start+spec.context_length+1]))
    return torch.tensor(xs,dtype=torch.long),torch.tensor(ys,dtype=torch.long)


def eval_bpb(model, data: bytes, spec: ModelSpec, max_windows: int) -> float:
    losses=[]; model.eval(); stride=spec.context_length
    starts=list(range(0,max(0,len(data)-spec.context_length-1),stride))[:max_windows]
    with torch.no_grad():
        for start in starts:
            x=torch.tensor([list(data[start:start+spec.context_length])],dtype=torch.long)
            y=torch.tensor([list(data[start+1:start+spec.context_length+1])],dtype=torch.long)
            logits=model(x)
            losses.append(float(F.cross_entropy(logits.reshape(-1,256),y.reshape(-1))))
    return (sum(losses)/len(losses))/math.log(2.0)


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--steps',type=int,default=300); p.add_argument('--batch-size',type=int,default=32); p.add_argument('--lr',type=float,default=0.003); p.add_argument('--eval-every',type=int,default=50); args=p.parse_args()
    here=Path(__file__).resolve().parent; data_dir=here/'data'; train=(data_dir/'train.bin').read_bytes(); val=(data_dir/'validation.bin').read_bytes()
    seed=1337; random.seed(seed); torch.manual_seed(seed); torch.set_num_threads(1); torch.use_deterministic_algorithms(True); rng=random.Random(seed)
    spec=ModelSpec(); model=ByteTransformer(spec); assert parameter_count(model)==expected_parameter_count(spec)
    optimizer=torch.optim.AdamW(model.parameters(),lr=args.lr)
    history=[]; best_bpb=float('inf'); best_state=None; best_step=None
    initial_bpb=eval_bpb(model,val,spec,128)
    for step in range(1,args.steps+1):
        model.train(); x,y=random_batch(train,spec,args.batch_size,rng); optimizer.zero_grad(set_to_none=True); logits=model(x); loss=F.cross_entropy(logits.reshape(-1,256),y.reshape(-1)); loss.backward(); optimizer.step()
        if step==1 or step%args.eval_every==0 or step==args.steps:
            vb=eval_bpb(model,val,spec,128); row={'step':step,'train_bpb':float(loss.detach())/math.log(2.0),'validation_bpb_128_windows':vb}; history.append(row); print(row,flush=True)
            if vb<best_bpb:
                best_bpb=vb; best_step=step; best_state=copy.deepcopy(model.state_dict())
    assert best_state is not None
    torch.save(best_state,here/'pilot-001-best.pt')
    run={'seed':seed,'deterministic_algorithms':True,'torch_num_threads':1,'steps':args.steps,'batch_size':args.batch_size,'learning_rate':args.lr,'initial_validation_bpb_128_windows':initial_bpb,'best_step':best_step,'best_validation_bpb_128_windows':best_bpb,'history':history}
    (here/'training-run.json').write_text(json.dumps(run,indent=2)+'\n')

if __name__=='__main__': main()
