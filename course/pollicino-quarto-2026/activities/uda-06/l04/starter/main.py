from __future__ import annotations
REQUIRED={'id','dataset_hash','model','precision_bits','seed','bpb'}
CONTROLLED=('dataset_hash','model','precision_bits','seed')
def validate_run(run:dict)->bool:
    raise NotImplementedError
def changed_controls(a:dict,b:dict)->list[str]:
    raise NotImplementedError
def is_single_factor_ablation(a:dict,b:dict)->bool:
    raise NotImplementedError
def delta_bpb(base:dict,variant:dict)->float:
    raise NotImplementedError
