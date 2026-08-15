from __future__ import annotations
import copy,json,math,random,sys,time,hashlib
from pathlib import Path
import torch
import torch.nn.functional as F
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'src'))
from pollicino.model_spec import ModelSpec,expected_parameter_count
from pollicino.backends.pytorch.model import ByteTransformer,parameter_count

SPEC=ModelSpec(context_length=32,d_model=48,n_heads=4,n_layers=2,d_ff=96)
SEED=1337; STEPS=300; BATCH=32; LR=0.003

def random_batch(data,rng):
 m=len(data)-SPEC.context_length-1
 starts=[rng.randint(0,m) for _ in range(BATCH)]
 x=torch.tensor([list(data[s:s+SPEC.context_length]) for s in starts],dtype=torch.long)
 y=torch.tensor([list(data[s+1:s+SPEC.context_length+1]) for s in starts],dtype=torch.long)
 return x,y

def eval_bpb(model,data,max_windows=128):
 starts=list(range(0,max(0,len(data)-SPEC.context_length-1),SPEC.context_length))[:max_windows]; losses=[]; model.eval()
 with torch.no_grad():
  for s in starts:
   x=torch.tensor([list(data[s:s+SPEC.context_length])]); y=torch.tensor([list(data[s+1:s+SPEC.context_length+1])]); logits=model(x); losses.append(float(F.cross_entropy(logits.reshape(-1,256),y.reshape(-1))))
 return sum(losses)/len(losses)/math.log(2)

def main():
 here=Path(__file__).resolve().parent; train=(here/'data/train.bin').read_bytes(); val=(here/'data/validation.bin').read_bytes()
 torch.set_num_threads(1); torch.use_deterministic_algorithms(True); random.seed(SEED); torch.manual_seed(SEED); rng=random.Random(SEED)
 model=ByteTransformer(SPEC); assert parameter_count(model)==expected_parameter_count(SPEC); opt=torch.optim.AdamW(model.parameters(),lr=LR)
 best=float('inf'); best_state=None; best_step=0; hist=[]; t0=time.perf_counter()
 for step in range(1,STEPS+1):
  model.train(); x,y=random_batch(train,rng); opt.zero_grad(set_to_none=True); logits=model(x); loss=F.cross_entropy(logits.reshape(-1,256),y.reshape(-1)); loss.backward(); opt.step()
  if step==1 or step%50==0:
   vb=eval_bpb(model,val); row={'step':step,'train_bpb':float(loss.detach())/math.log(2),'validation_bpb':vb}; hist.append(row); print(row,flush=True)
   if vb<best: best=vb; best_step=step; best_state=copy.deepcopy(model.state_dict())
 path=here/'winner-medium-c32-s1337.pt'; torch.save(best_state,path)
 out={'spec':SPEC.__dict__,'parameter_count':parameter_count(model),'seed':SEED,'steps':STEPS,'batch_size':BATCH,'lr':LR,'best_step':best_step,'best_validation_bpb':best,'train_seconds':time.perf_counter()-t0,'checkpoint_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'checkpoint_bytes':path.stat().st_size,'history':hist}
 (here/'winner-training.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__': main()
