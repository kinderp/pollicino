from __future__ import annotations
import json, math, platform
from pathlib import Path

def result_record(*,backend,device,framework_version,parameter_count,train_seconds,validation_loss_nats,seed,steps,notes=''):
    return {'backend':backend,'device':device,'framework_version':framework_version,'parameter_count':int(parameter_count),'train_seconds':float(train_seconds),'validation_loss_nats':float(validation_loss_nats),'validation_bpb':float(validation_loss_nats)/math.log(2.0),'seed':int(seed),'steps':int(steps),'python':platform.python_version(),'notes':notes}

def validate_record(record):
    # TODO: validate the experiment record contract
    raise NotImplementedError

def save_jsonl(path,records):
    for r in records: validate_record(r)
    Path(path).write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in records),encoding='utf-8')

def compare_records(a,b):
    # TODO: only compare equal parameter counts; report bpb delta and time ratio
    raise NotImplementedError
