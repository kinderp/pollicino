from __future__ import annotations

import argparse
import json
import math
import random
import resource
import sys
import time
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
    starts = [rng.randint(0, max_start) for _ in range(batch_size)]
    xs = [list(data[s:s+spec.context_length]) for s in starts]
    ys = [list(data[s+1:s+spec.context_length+1]) for s in starts]
    return torch.tensor(xs, dtype=torch.long), torch.tensor(ys, dtype=torch.long)


def eval_bpb(model, data: bytes, spec: ModelSpec, max_windows: int = 64) -> float:
    losses=[]
    model.eval()
    starts = list(range(0, max(0, len(data)-spec.context_length-1), spec.context_length))[:max_windows]
    if not starts:
        raise ValueError('not enough evaluation data')
    with torch.no_grad():
        for s in starts:
            x = torch.tensor([list(data[s:s+spec.context_length])], dtype=torch.long)
            y = torch.tensor([list(data[s+1:s+spec.context_length+1])], dtype=torch.long)
            logits = model(x)
            losses.append(float(F.cross_entropy(logits.reshape(-1, 256), y.reshape(-1))))
    return sum(losses)/len(losses)/math.log(2.0)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--name', required=True)
    p.add_argument('--context', type=int, required=True)
    p.add_argument('--d-model', type=int, required=True)
    p.add_argument('--heads', type=int, required=True)
    p.add_argument('--layers', type=int, required=True)
    p.add_argument('--d-ff', type=int, required=True)
    p.add_argument('--steps', type=int, default=120)
    p.add_argument('--batch-size', type=int, default=32)
    p.add_argument('--lr', type=float, default=0.003)
    p.add_argument('--seed', type=int, default=1337)
    p.add_argument('--eval-windows', type=int, default=64)
    p.add_argument('--output', required=True)
    args=p.parse_args()

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    rng=random.Random(args.seed)

    here=Path(__file__).resolve().parent
    train=(here/'data/train.bin').read_bytes()
    val=(here/'data/validation.bin').read_bytes()
    test=(here/'data/test.bin').read_bytes()

    spec=ModelSpec(context_length=args.context,d_model=args.d_model,n_heads=args.heads,n_layers=args.layers,d_ff=args.d_ff)
    model=ByteTransformer(spec)
    params=parameter_count(model)
    assert params == expected_parameter_count(spec)
    optimizer=torch.optim.AdamW(model.parameters(), lr=args.lr)

    init_val=eval_bpb(model,val,spec,args.eval_windows)
    history=[]
    best_val=float('inf')
    best_step=0
    start=time.perf_counter()
    for step in range(1,args.steps+1):
        model.train()
        x,y=random_batch(train,spec,args.batch_size,rng)
        optimizer.zero_grad(set_to_none=True)
        logits=model(x)
        loss=F.cross_entropy(logits.reshape(-1,256),y.reshape(-1))
        loss.backward(); optimizer.step()
        if step in {1, args.steps//2, args.steps}:
            vb=eval_bpb(model,val,spec,args.eval_windows)
            history.append({'step':step,'train_bpb':float(loss.detach())/math.log(2.0),'validation_bpb':vb})
            if vb<best_val:
                best_val=vb; best_step=step
    train_seconds=time.perf_counter()-start
    final_val=eval_bpb(model,val,spec,args.eval_windows)
    test_bpb=eval_bpb(model,test,spec,args.eval_windows)
    peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result={
        'name':args.name,
        'seed':args.seed,
        'spec':spec.__dict__,
        'parameter_count':params,
        'steps':args.steps,
        'batch_size':args.batch_size,
        'learning_rate':args.lr,
        'initial_validation_bpb':init_val,
        'final_validation_bpb':final_val,
        'test_bpb':test_bpb,
        'best_validation_bpb':best_val if best_step else final_val,
        'best_step':best_step,
        'train_seconds':train_seconds,
        'steps_per_second':args.steps/train_seconds,
        'peak_rss_mib':peak_rss_kib/1024.0,
        'history':history,
        'torch_version':torch.__version__,
    }
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':
    main()
