from __future__ import annotations
import bz2,gzip,hashlib,json,lzma,math,subprocess,sys,time,zlib
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'src'))
from pollicino.model_spec import ModelSpec
from pollicino.backends.pytorch.model import ByteTransformer
from pollicino.compression.codec import encode_shared,decode_pol,inspect_pol
from pollicino.compression.neural import PyTorchCDFProvider,torch_model_fingerprint
SPEC=ModelSpec(context_length=32,d_model=48,n_heads=4,n_layers=2,d_ff=96)

def exact_bpbs(model,data):
 p=PyTorchCDFProvider(model,SPEC,precision_bits=15,device='cpu'); prefix=[]; fb=qb=0.; model.eval()
 with torch.no_grad():
  for i,sym in enumerate(data):
   if i==0: fb+=8; qb+=8; prefix.append(sym); continue
   ctx=prefix[-SPEC.context_length:]; logits=model(torch.tensor([ctx]))[0,-1]; probs=torch.softmax(logits,dim=-1); fb+=-math.log2(float(probs[sym])); cdf=p(i,prefix); qb+=-math.log2((cdf[sym+1]-cdf[sym])/cdf[-1]); prefix.append(sym)
 return fb/len(data),qb/len(data)

def main():
 here=Path(__file__).resolve().parent; test=(here/'data/test.bin').read_bytes(); sample=test[:2048]
 torch.set_num_threads(1); torch.use_deterministic_algorithms(True); model=ByteTransformer(SPEC); ck=here/'winner-medium-c32-s1337.pt'; model.load_state_dict(torch.load(ck,map_location='cpu',weights_only=True)); model.eval()
 f,q=exact_bpbs(model,sample); fp=torch_model_fingerprint(model,SPEC); p=PyTorchCDFProvider(model,SPEC,precision_bits=15,device='cpu'); t=time.perf_counter(); blob=encode_shared(sample,p,fp); enc=time.perf_counter()-t; p2=PyTorchCDFProvider(model,SPEC,precision_bits=15,device='cpu'); t=time.perf_counter(); restored=decode_pol(blob,shared_provider=p2,expected_model_fingerprint=fp); dec=time.perf_counter()-t; assert restored==sample; info=inspect_pol(blob)
 bases={'raw':len(sample),'zlib':len(zlib.compress(sample,9)),'gzip':len(gzip.compress(sample,9)),'bz2':len(bz2.compress(sample,9)),'xz_lzma':len(lzma.compress(sample,preset=9))}
 for n,cmd in [('zstd',['zstd','-q','-19','-c']),('xz_cli',['xz','-9e','-c'])]: bases[n]=len(subprocess.run(cmd,input=sample,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout)
 out={'sample_bytes':len(sample),'sample_sha256':hashlib.sha256(sample).hexdigest(),'float_model_bpb':f,'quantized_cdf_ideal_bpb':q,'range_payload_bpb':info['payload_bpb'],'pol_file_bpb':info['realized_bpb'],'encode_seconds':enc,'decode_seconds':dec,'model_fingerprint':fp.hex(),'baselines_bytes':bases,'baselines_bpb':{k:v*8/len(sample) for k,v in bases.items()}}
 (here/'winner-coding.json').write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
