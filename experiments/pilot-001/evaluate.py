from __future__ import annotations

import hashlib,json,math,platform,subprocess,sys,time
from pathlib import Path
import torch
import torch.nn.functional as F

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'src'))
from pollicino.model_spec import ModelSpec
from pollicino.backends.pytorch.model import ByteTransformer,parameter_count
from pollicino.compression.codec import encode_shared,decode_pol,inspect_pol,encode_uniform,encode_static_histogram
from pollicino.compression.neural import PyTorchCDFProvider,torch_model_fingerprint


def eval_bpb(model,data,spec,max_windows=256):
    losses=[]; model.eval(); starts=list(range(0,max(0,len(data)-spec.context_length-1),spec.context_length))[:max_windows]
    with torch.no_grad():
        for s in starts:
            x=torch.tensor([list(data[s:s+spec.context_length])]); y=torch.tensor([list(data[s+1:s+spec.context_length+1])]); logits=model(x); losses.append(float(F.cross_entropy(logits.reshape(-1,256),y.reshape(-1))))
    return sum(losses)/len(losses)/math.log(2.0)


def exact_bpbs(model,data,spec):
    provider=PyTorchCDFProvider(model,spec,precision_bits=15,device='cpu'); prefix=[]; float_bits=0.; quant_bits=0.; model.eval()
    with torch.no_grad():
        for i,symbol in enumerate(data):
            if i==0: float_bits+=8.; quant_bits+=8.; prefix.append(symbol); continue
            context=prefix[-spec.context_length:]; logits=model(torch.tensor([context]))[0,-1]; probs=torch.softmax(logits,dim=-1)
            float_bits += -math.log2(float(probs[symbol])); cdf=provider(i,prefix); quant_bits += -math.log2((cdf[symbol+1]-cdf[symbol])/cdf[-1]); prefix.append(symbol)
    return float_bits/len(data),quant_bits/len(data)


def main():
    here=Path(__file__).resolve().parent; data_dir=here/'data'; torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
    manifest=json.loads((here/'dataset-manifest.json').read_text()); training=json.loads((here/'training-run.json').read_text()); spec=ModelSpec(); model=ByteTransformer(spec); checkpoint=here/'pilot-001-best.pt'; model.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True)); model.eval()
    val=(data_dir/'validation.bin').read_bytes(); test=(data_dir/'test.bin').read_bytes(); sample=test[:2048]; (data_dir/'encode-slice.bin').write_bytes(sample)
    float_bpb,quant_bpb=exact_bpbs(model,sample,spec); fp=torch_model_fingerprint(model,spec)
    p=PyTorchCDFProvider(model,spec,precision_bits=15,device='cpu'); t=time.perf_counter(); blob=encode_shared(sample,p,fp); enc=time.perf_counter()-t
    p2=PyTorchCDFProvider(model,spec,precision_bits=15,device='cpu'); t=time.perf_counter(); restored=decode_pol(blob,shared_provider=p2,expected_model_fingerprint=fp); dec=time.perf_counter()-t; assert restored==sample; info=inspect_pol(blob)
    import gzip,bz2,lzma,zlib
    bases={'raw':len(sample),'gzip':len(gzip.compress(sample,9)),'bz2':len(bz2.compress(sample,9)),'xz_lzma':len(lzma.compress(sample,preset=9)),'zlib':len(zlib.compress(sample,9)),'pol_uniform':len(encode_uniform(sample)),'pol_static':len(encode_static_histogram(sample)),'pol_shared':len(blob)}
    for name,cmd in [('zstd',['zstd','-q','-19','-c']),('xz_cli',['xz','-9e','-c'])]: bases[name]=len(subprocess.run(cmd,input=sample,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout)
    result={'experiment_id':'pilot-001-pollicino-self-v1','seed':training['seed'],'device':'cpu','torch_version':torch.__version__,'python':sys.version.split()[0],'platform':platform.platform(),'dataset':manifest['splits'],'model_spec':spec.__dict__,'parameter_count':parameter_count(model),'training':training|{'validation_bpb_256_windows':eval_bpb(model,val,spec,256),'test_bpb_256_windows':eval_bpb(model,test,spec,256)},'checkpoint':{'path':'pilot-001-best.pt','sha256':hashlib.sha256(checkpoint.read_bytes()).hexdigest(),'bytes':checkpoint.stat().st_size},'coding_slice':{'bytes':len(sample),'sha256':hashlib.sha256(sample).hexdigest(),'float_model_bpb':float_bpb,'quantized_cdf_ideal_bpb':quant_bpb,'range_payload_bpb':info['payload_bpb'],'pol_file_bpb':info['realized_bpb'],'encode_seconds':enc,'decode_seconds':dec,'model_fingerprint':fp.hex()},'baselines_bytes':bases,'baselines_bpb':{k:v*8/len(sample) for k,v in bases.items()}}
    (here/'results.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))

if __name__=='__main__': main()
