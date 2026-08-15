from __future__ import annotations
REQUIRED={'id','dataset_hash','model','precision_bits','seed','bpb'}; CONTROLLED=('dataset_hash','model','precision_bits','seed')
def validate_run(run): return REQUIRED<=set(run) and isinstance(run['bpb'],(int,float)) and run['precision_bits']>0
def changed_controls(a,b):
 if not validate_run(a) or not validate_run(b): raise ValueError('invalid run')
 return [k for k in CONTROLLED if a[k]!=b[k]]
def is_single_factor_ablation(a,b): return len(changed_controls(a,b))==1
def delta_bpb(base,variant):
 if not validate_run(base) or not validate_run(variant): raise ValueError('invalid run')
 return float(variant['bpb'])-float(base['bpb'])
