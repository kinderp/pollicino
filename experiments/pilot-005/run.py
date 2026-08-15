from __future__ import annotations

import csv, hashlib, importlib.util, json, math, os, subprocess, sys, tarfile, tempfile, time
from pathlib import Path

import torch

ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent; OUT=HERE/'output'; OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'src'))
from pollicino.compression.adaptive import AdaptiveNGramCDFProvider,NeuralPriorAdaptiveCDFProvider,adaptive_fingerprint
from pollicino.compression.codec import decode_pol,encode_shared,inspect_pol
from pollicino.compression.neural import PyTorchCDFProvider,torch_model_fingerprint

TRAINING_COMMIT='9c833cfb119fdfc941977abafc3fcb75e9e9c7ec'
V2={'train':{'bytes':104189,'sha256':'6965b8665eaa4cfcf20703438adce522d6480401f0f608974a9f29ee9409a57c'},'validation':{'bytes':11742,'sha256':'575a1cbfd3544229a633408a23a86f5a72b006461cc443a8a7d82b7b11cfc5ec'},'test':{'bytes':15424,'sha256':'07c5a0a5c13a35a413a9eb0e94ee9926c8506754aafc5598e7e7e424a00d5d99'}}
ADAPTIVE_CONFIGS={'adaptive-o2':dict(max_order=2,order_weights=(1,4,16),base_count=1),'adaptive-o3':dict(max_order=3,order_weights=(1,4,16,64),base_count=1)}
PRIOR_STRENGTHS=(64,256,1024); REPRESENTATIVE=['alice29.txt','fields.c','kennedy.xls','ptt5','sum']; ARTIFICIAL_REP=['aaa.txt','random.txt']; PRECISION=18; SLICE=2048

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def load_module(path:Path,name:str):
 spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(module); return module

def prepare_frozen_model():
 p3=load_module(ROOT/'experiments/pilot-003/run.py','pilot003_for_p5')
 with tempfile.TemporaryDirectory() as td:
  td=Path(td); archive=td/'base.tar'; frozen=td/'repo'; frozen.mkdir()
  subprocess.run(['git','archive',TRAINING_COMMIT,'-o',str(archive)],check=True)
  with tarfile.open(archive) as tar: tar.extractall(frozen)
  prep=load_module(frozen/'experiments/pilot-001/prepare_data.py','frozen_prepare'); data_dir=td/'data'; prep.write_dataset(frozen,data_dir)
  for split,expected in V2.items():
   blob=(data_dir/f'{split}.bin').read_bytes(); got={'bytes':len(blob),'sha256':sha(blob)}
   if got!=expected: raise RuntimeError(f'frozen self-v2 drift {split}: {got}')
  train=(data_dir/'train.bin').read_bytes(); val=(data_dir/'validation.bin').read_bytes()
  cfg=p3.CANDIDATES['m80-l2']; row=p3.train_once('m80-l2',cfg,1337,500,train,val,keep_state=True); state=row.pop('_state'); spec=p3.model_spec(cfg); model=p3.ByteTransformer(spec); model.load_state_dict(state); model.eval()
 ck=OUT/'m80-l2-frozen.pt'; torch.save(state,ck); row.update({'checkpoint_bytes':ck.stat().st_size,'checkpoint_sha256':sha(ck.read_bytes()),'training_commit':TRAINING_COMMIT})
 return model,spec,row

def adaptive_bpb(data:bytes,n:int,cfg:dict)->float:
 sample=data[:n]; p=AdaptiveNGramCDFProvider(**cfg); prefix=[]; bits=0.0
 for i,symbol in enumerate(sample):
  num,den=p.symbol_mass(i,prefix,symbol); bits+=math.log2(den)-math.log2(num); prefix.append(symbol)
 return bits/len(sample) if sample else 0.0

def roundtrip(data:bytes,factory,fingerprint:bytes)->dict:
 t=time.perf_counter(); blob=encode_shared(data,factory(),fingerprint,precision_bits=PRECISION); enc=time.perf_counter()-t
 t=time.perf_counter(); restored=decode_pol(blob,shared_provider=factory(),expected_model_fingerprint=fingerprint); dec=time.perf_counter()-t; assert restored==data; info=inspect_pol(blob)
 return {'payload_bpb':info['payload_bpb'],'pol1_bpb':info['realized_bpb'],'file_bytes':info['file_bytes'],'encode_seconds':enc,'decode_seconds':dec}
def csvout(path,rows):
 fields=sorted({k for r in rows for k in r}); f=path.open('w',newline=''); w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows); f.close()

def main():
 torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
 p4=load_module(ROOT/'experiments/pilot-004/run.py','pilot004_for_p5'); p4r=json.loads((ROOT/'experiments/pilot-004/results.json').read_text())
 model,spec,training=prepare_frozen_model(); neural_fp=torch_model_fingerprint(model,spec)
 if neural_fp.hex()!=p4r['model_fingerprint']: raise RuntimeError('frozen training did not reproduce PILOT-004 model')
 canzip=p4.download(p4.CAN_URL,OUT/'cantrbry.zip'); artzip=p4.download(p4.ART_URL,OUT/'artificl.zip'); can=p4.unpack(canzip,p4.CAN); art=p4.unpack(artzip,p4.ART)
 frozen_can={r['file']:r for r in p4r['canterbury']}; frozen_art={r['file']:r for r in p4r['artificial_controls']}; frozen_coding={r['file']:r for r in p4r['coding_checks']}
 can_rows=[]
 for name,data in can.items():
  fr=frozen_can[name]; n=int(fr['eval_bytes']); row={'file':name,'category':p4.CAN[name][0],'eval_bytes':n,'frozen_neural_bpb':fr['model_zero_shot_bpb'],'zlib_bpb':fr['eval_zlib_bpb'],'zstd19_bpb':fr['eval_zstd19_bpb']}
  for method,cfg in ADAPTIVE_CONFIGS.items(): row[f'{method}_bpb']=adaptive_bpb(data,n,cfg)
  can_rows.append(row); print('CANTERBURY',name,row['frozen_neural_bpb'],row['adaptive-o3_bpb'],row['zlib_bpb'],flush=True)
 art_rows=[]
 for name,data in art.items():
  fr=frozen_art[name]; n=int(fr['eval_bytes']); row={'file':name,'category':p4.ART[name][0],'eval_bytes':n,'frozen_neural_bpb':fr['model_zero_shot_bpb'],'zlib_bpb':fr['eval_zlib_bpb'],'zstd19_bpb':fr['eval_zstd19_bpb']}
  for method,cfg in ADAPTIVE_CONFIGS.items(): row[f'{method}_bpb']=adaptive_bpb(data,n,cfg)
  art_rows.append(row); print('ARTIFICIAL',name,row['frozen_neural_bpb'],row['adaptive-o3_bpb'],row['zlib_bpb'],flush=True)
 def af(cfg): return lambda:AdaptiveNGramCDFProvider(**cfg)
 def pf(strength): return lambda:NeuralPriorAdaptiveCDFProvider(PyTorchCDFProvider(model,spec,precision_bits=PRECISION,device='cpu'),prior_strength=strength,max_order=3,order_weights=(1,4,16,64),base_count=1)
 coding=[]; sources={**can,**art}
 for name in REPRESENTATIVE+ARTIFICIAL_REP:
  data=sources[name][:SLICE]; cat=p4.CAN[name][0] if name in p4.CAN else p4.ART[name][0]; base=frozen_coding.get(name); common={'file':name,'category':cat,'sample_bytes':len(data),'sample_sha256':sha(data),'zlib_bpb':base['zlib_bpb'] if base else len(__import__('zlib').compress(data,9))*8/len(data),'frozen_neural_pol1_bpb':base['pol1_bpb'] if base else None}
  for method,cfg in ADAPTIVE_CONFIGS.items():
   fp=adaptive_fingerprint(max_order=cfg['max_order'],order_weights=cfg['order_weights'],base_count=cfg['base_count']); coding.append({**common,'method':method,'requires_neural_checkpoint':False,**roundtrip(data,af(cfg),fp)})
  for strength in PRIOR_STRENGTHS:
   fp=adaptive_fingerprint(max_order=3,order_weights=(1,4,16,64),base_count=1,prior_strength=strength,neural_fingerprint=neural_fp); coding.append({**common,'method':f'neural-prior-{strength}','requires_neural_checkpoint':True,**roundtrip(data,pf(strength),fp)})
  print('CODED',name,flush=True)
 def weighted(rows,key):
  total=sum(r['eval_bytes'] for r in rows); return sum(r[key]*r['eval_bytes'] for r in rows)/total
 agg={'weighted_frozen_neural_bpb':weighted(can_rows,'frozen_neural_bpb'),'weighted_adaptive_o2_bpb':weighted(can_rows,'adaptive-o2_bpb'),'weighted_adaptive_o3_bpb':weighted(can_rows,'adaptive-o3_bpb'),'weighted_zlib_bpb':weighted(can_rows,'zlib_bpb'),'weighted_zstd19_bpb':weighted(can_rows,'zstd19_bpb'),'adaptive_o3_beats_frozen_count':sum(r['adaptive-o3_bpb']<r['frozen_neural_bpb'] for r in can_rows),'adaptive_o3_beats_zlib_count':sum(r['adaptive-o3_bpb']<r['zlib_bpb'] for r in can_rows),'adaptive_o3_below_8_count':sum(r['adaptive-o3_bpb']<8 for r in can_rows)}
 results={'experiment_id':'pilot-005-adaptive-pollicino','base_commit':os.getenv('GITHUB_SHA','local'),'training_commit':TRAINING_COMMIT,'training_domain':'pollicino-self-v2-clean-git frozen at training_commit','external_fine_tuning':False,'neural_model':{'spec':spec.__dict__,'canonical_fingerprint':neural_fp.hex(),'checkpoint_bytes':training['checkpoint_bytes'],'best_validation_bpb':training['best_validation_bpb']},'adaptive_configs':{n:{**c,'order_weights':list(c['order_weights'])} for n,c in ADAPTIVE_CONFIGS.items()},'prior_strengths':list(PRIOR_STRENGTHS),'aggregate':agg,'canterbury':can_rows,'artificial_controls':art_rows,'coding_checks':coding,'protocol':{'adaptive_state_source':'decoded prefix only','adaptive_state_transmitted':False,'gradient_updates':False,'coding_slice_bytes':SLICE,'neural_prior_precision_bits':PRECISION},'sources':{'canterbury_archive_sha256':sha(canzip),'artificial_archive_sha256':sha(artzip)}}
 (OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n'); csvout(OUT/'canterbury.csv',can_rows); csvout(OUT/'artificial.csv',art_rows); csvout(OUT/'coding.csv',coding); print(json.dumps(agg,indent=2))
if __name__=='__main__':main()
