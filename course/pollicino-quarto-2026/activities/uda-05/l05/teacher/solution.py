from __future__ import annotations
import json, math, platform
from pathlib import Path

def result_record(*,backend,device,framework_version,parameter_count,train_seconds,validation_loss_nats,seed,steps,notes=''):
    return {'backend':backend,'device':device,'framework_version':framework_version,'parameter_count':int(parameter_count),'train_seconds':float(train_seconds),'validation_loss_nats':float(validation_loss_nats),'validation_bpb':float(validation_loss_nats)/math.log(2.0),'seed':int(seed),'steps':int(steps),'python':platform.python_version(),'notes':notes}

def validate_record(record):
    required={'backend','device','framework_version','parameter_count','train_seconds','validation_loss_nats','validation_bpb','seed','steps','python','notes'}
    missing=required-record.keys()
    if missing: raise ValueError(f'missing fields: {sorted(missing)}')
    if record['parameter_count']<=0 or record['train_seconds']<0 or record['validation_bpb']<0: raise ValueError('invalid non-negative metric')
    return True

def save_jsonl(path,records):
    for r in records: validate_record(r)
    Path(path).write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in records),encoding='utf-8')

def compare_records(a,b):
    validate_record(a); validate_record(b)
    if a['parameter_count']!=b['parameter_count']:
        return {'comparable':False,'reason':'parameter_count differs'}
    return {'comparable':True,'bpb_delta':b['validation_bpb']-a['validation_bpb'],'speed_ratio_b_over_a':(b['train_seconds']/a['train_seconds']) if a['train_seconds'] else None}
