from __future__ import annotations

import bz2, csv, gzip, hashlib, importlib.util, json, lzma, math, os, sys, time, urllib.request, zipfile, zlib
from pathlib import Path
from statistics import mean

import torch
import torch.nn.functional as F
import zstandard as zstd

ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent; OUT=HERE/'output'; OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'src'))
from pollicino.backends.pytorch.model import ByteTransformer,parameter_count
from pollicino.compression.codec import encode_shared,decode_pol,inspect_pol
from pollicino.compression.neural import PyTorchCDFProvider,torch_model_fingerprint

V2={'train':{'bytes':104189,'sha256':'6965b8665eaa4cfcf20703438adce522d6480401f0f608974a9f29ee9409a57c'},'validation':{'bytes':11742,'sha256':'575a1cbfd3544229a633408a23a86f5a72b006461cc443a8a7d82b7b11cfc5ec'},'test':{'bytes':15424,'sha256':'07c5a0a5c13a35a413a9eb0e94ee9926c8506754aafc5598e7e7e424a00d5d99'}}
P3_SHA='713aebe2b3bac94931060ff4fa09b3174b033d44913d43354f27ec2a568f7ff7'
MAX_EVAL=65536; BATCH=256; SLICE=2048; PRECISION=18
CAN_URL='https://corpus.canterbury.ac.nz/resources/cantrbry.zip'; ART_URL='https://corpus.canterbury.ac.nz/resources/artificl.zip'
CAN={'alice29.txt':('english-text',152089),'asyoulik.txt':('shakespeare-play',125179),'cp.html':('html-source',24603),'fields.c':('c-source',11150),'grammar.lsp':('lisp-source',3721),'kennedy.xls':('excel-spreadsheet',1029744),'lcet10.txt':('technical-writing',426754),'plrabn12.txt':('poetry',481861),'ptt5':('ccitt-fax',513216),'sum':('sparc-executable',38240),'xargs.1':('gnu-manual',4227)}
ART={'a.txt':('single-byte',1),'aaa.txt':('repetition',100000),'alphabet.txt':('periodic',100000),'random.txt':('random-64-symbol-alphabet',100000)}
REP=['alice29.txt','cp.html','fields.c','kennedy.xls','ptt5','sum']; ART_CODE=['aaa.txt','random.txt']

def sha(b): return hashlib.sha256(b).hexdigest()

def load_p3():
 p=ROOT/'experiments/pilot-003/run.py'; s=importlib.util.spec_from_file_location('pilot003',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def prepare_model():
 p3=load_p3(); manifest=p3.prepare_dataset(); data_dir=ROOT/'experiments/pilot-003/data'
 for split,exp in V2.items():
  b=(data_dir/f'{split}.bin').read_bytes(); got={'bytes':len(b),'sha256':sha(b)}
  if got!=exp: raise RuntimeError(f'self-v2 drift {split}: {got}')
 train=(data_dir/'train.bin').read_bytes(); val=(data_dir/'validation.bin').read_bytes(); cfg=p3.CANDIDATES['m80-l2']
 row=p3.train_once('m80-l2',cfg,1337,500,train,val,keep_state=True); state=row.pop('_state'); spec=p3.model_spec(cfg); model=ByteTransformer(spec); model.load_state_dict(state); model.eval()
 ck=OUT/'m80-l2-self-v2.pt'; torch.save(state,ck); row.update({'checkpoint_bytes':ck.stat().st_size,'checkpoint_sha256':sha(ck.read_bytes()),'matches_pilot003_checkpoint':sha(ck.read_bytes())==P3_SHA})
 return model,spec,row

def download(url,path):
 req=urllib.request.Request(url,headers={'User-Agent':'POLLICINO-PILOT-004/1.0'}); data=urllib.request.urlopen(req,timeout=60).read(); path.write_bytes(data); return data

def unpack(archive, expected):
 tmp=OUT/'tmp.zip'; tmp.write_bytes(archive); out={}
 with zipfile.ZipFile(tmp) as z:
  names={Path(n).name:n for n in z.namelist() if not n.endswith('/')}
  for f,(_,size) in expected.items():
   b=z.read(names[f]);
   if len(b)!=size: raise RuntimeError(f'{f}: {len(b)} != {size}')
   out[f]=b
 tmp.unlink(missing_ok=True); return out

def baselines(data):
 return {'raw':len(data),'zlib':len(zlib.compress(data,9)),'gzip':len(gzip.compress(data,9)),'bz2':len(bz2.compress(data,9)),'xz_lzma':len(lzma.compress(data,preset=9)),'zstd19':len(zstd.ZstdCompressor(level=19).compress(data))}

def zero_shot(model,spec,data):
 sample=data[:MAX_EVAL]; n=len(sample)
 if not n:return 0.,0
 bits=8.; model.eval()
 with torch.no_grad():
  for i in range(1,min(n,spec.context_length)):
   x=torch.tensor([list(sample[:i])],dtype=torch.long); lp=F.log_softmax(model(x)[0,-1],dim=-1); bits+=-float(lp[sample[i]])/math.log(2)
  pos=list(range(spec.context_length,n))
  for off in range(0,len(pos),BATCH):
   c=pos[off:off+BATCH]; x=torch.tensor([list(sample[i-spec.context_length:i]) for i in c],dtype=torch.long); y=torch.tensor([sample[i] for i in c]); lp=F.log_softmax(model(x)[:,-1,:],dim=-1); bits+=-float(lp[torch.arange(len(c)),y].sum())/math.log(2)
 return bits/n,n

def eval_file(model,spec,name,cat,data):
 bpb,n=zero_shot(model,spec,data); sample=data[:n]; base=baselines(sample); full=baselines(data); r={'file':name,'category':cat,'file_bytes':len(data),'sha256':sha(data),'eval_bytes':n,'model_zero_shot_bpb':bpb}
 for k,v in base.items():r[f'eval_{k}_bpb']=v*8/n if n else 0
 for k,v in full.items():r[f'full_{k}_bpb']=v*8/len(data) if data else 0
 return r

def code_file(model,spec,fp,name,cat,data,ckbytes):
 sample=data[:min(SLICE,len(data))]; p=PyTorchCDFProvider(model,spec,precision_bits=PRECISION,device='cpu'); t=time.perf_counter(); blob=encode_shared(sample,p,fp,precision_bits=PRECISION); enc=time.perf_counter()-t; p2=PyTorchCDFProvider(model,spec,precision_bits=PRECISION,device='cpu'); t=time.perf_counter(); restored=decode_pol(blob,shared_provider=p2,expected_model_fingerprint=fp); dec=time.perf_counter()-t; assert restored==sample; info=inspect_pol(blob); base=baselines(sample); r={'file':name,'category':cat,'sample_bytes':len(sample),'sample_sha256':sha(sample),'payload_bpb':info['payload_bpb'],'pol1_bpb':info['realized_bpb'],'encode_seconds':enc,'decode_seconds':dec,'self_contained_with_checkpoint_bpb':(len(blob)+ckbytes)*8/len(sample)}
 for k,v in base.items():r[f'{k}_bpb']=v*8/len(sample)
 return r

def weighted(rows,key):
 n=sum(r['eval_bytes'] for r in rows); return sum(r[key]*r['eval_bytes'] for r in rows)/n

def csvout(path,rows):
 fields=sorted({k for r in rows for k in r}); f=path.open('w',newline=''); w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows); f.close()

def main():
 torch.set_num_threads(1); torch.use_deterministic_algorithms(True); model,spec,training=prepare_model(); fp=torch_model_fingerprint(model,spec)
 canzip=download(CAN_URL,OUT/'cantrbry.zip'); artzip=download(ART_URL,OUT/'artificl.zip'); can=unpack(canzip,CAN); art=unpack(artzip,ART)
 canrows=[eval_file(model,spec,n,CAN[n][0],can[n]) for n in CAN]; artrows=[eval_file(model,spec,n,ART[n][0],art[n]) for n in ART]
 coding=[code_file(model,spec,fp,n,CAN[n][0],can[n],training['checkpoint_bytes']) for n in REP]+[code_file(model,spec,fp,n,ART[n][0],art[n],training['checkpoint_bytes']) for n in ART_CODE]
 total=sum(map(len,can.values())); agg={'canterbury_files':len(canrows),'canterbury_total_bytes':total,'weighted_zero_shot_bpb':weighted(canrows,'model_zero_shot_bpb'),'weighted_zlib_bpb':weighted(canrows,'eval_zlib_bpb'),'weighted_gzip_bpb':weighted(canrows,'eval_gzip_bpb'),'weighted_zstd19_bpb':weighted(canrows,'eval_zstd19_bpb'),'checkpoint_amortization_bpb_over_full_canterbury':training['checkpoint_bytes']*8/total}
 wins={'model_beats_zlib_eval':[r['file'] for r in canrows if r['model_zero_shot_bpb']<r['eval_zlib_bpb']],'pol1_beats_zlib_slice':[r['file'] for r in coding if r['pol1_bpb']<r['zlib_bpb']]}
 results={'experiment_id':'pilot-004-cross-domain-generalization','base_commit':os.getenv('GITHUB_SHA','local'),'training_domain':'pollicino-self-v2-clean-git only','fine_tuning_on_external':False,'training':training,'model_fingerprint':fp.hex(),'sources':{'canterbury':{'url':CAN_URL,'archive_bytes':len(canzip),'archive_sha256':sha(canzip)},'artificial':{'url':ART_URL,'archive_bytes':len(artzip),'archive_sha256':sha(artzip)}},'protocol':{'max_zero_shot_eval_bytes_per_file':MAX_EVAL,'coding_slice_bytes':SLICE,'precision_bits':PRECISION,'shared_model_weights_transmitted':False,'self_contained_metric_adds_checkpoint_bytes':True},'aggregate':agg,'wins':wins,'canterbury':canrows,'artificial_controls':artrows,'coding_checks':coding,'limits':['Canterbury is intentionally stable but old.','The model receives no external-domain fine-tuning.','Shared-model POL1 excludes checkpoint bytes; self-contained metric adds them explicitly.','Zero-shot model bpb uses exact sliding context on at most the first 65536 bytes per file.']}
 (OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n'); csvout(OUT/'canterbury.csv',canrows); csvout(OUT/'artificial.csv',artrows); csvout(OUT/'coding.csv',coding); manifest={'canterbury':[{'file':n,'category':CAN[n][0],'bytes':len(can[n]),'sha256':sha(can[n])} for n in CAN],'artificial':[{'file':n,'category':ART[n][0],'bytes':len(art[n]),'sha256':sha(art[n])} for n in ART]}; (OUT/'external-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n'); print(json.dumps({'aggregate':agg,'wins':wins,'checkpoint_match':training['matches_pilot003_checkpoint']},indent=2))
if __name__=='__main__':main()
