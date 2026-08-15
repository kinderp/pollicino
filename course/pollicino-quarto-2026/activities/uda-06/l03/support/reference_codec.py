from __future__ import annotations
import hashlib,struct
from collections import Counter
from support.pol_format import MODEL_STATIC_HISTOGRAM,PolHeader
from support.range_coder import encode_symbols,decode_symbols
_FREQS=struct.Struct('>256H')
def quantize_counts(data,precision_bits=15):
 total=1<<precision_bits;c=Counter(data);raw=[c[i] for i in range(256)];mass=sum(raw)
 if mass==0:return [total//256]*256
 rem=total-256;scaled=[x*rem/mass for x in raw];floors=[int(x) for x in scaled];f=[1+x for x in floors];left=total-sum(f);order=sorted(range(256),key=lambda i:(-(scaled[i]-floors[i]),i))
 for i in order[:left]:f[i]+=1
 return f
def cdf(f):
 out=[0];r=0
 for x in f:r+=x;out.append(r)
 return out
def encode_pol(data,precision_bits=15):
 f=quantize_counts(data,precision_bits);meta=_FREQS.pack(*f);C=cdf(f);payload,bits=encode_symbols(data,[C]*len(data));fp=hashlib.sha256(b'static-histogram-v1'+bytes([precision_bits])+meta).digest();sha=hashlib.sha256(data).digest();h=PolHeader(MODEL_STATIC_HISTOGRAM,precision_bits,len(data),len(meta),bits,sha,fp);return h.pack()+meta+payload
def decode_pol(blob):
 h,o=PolHeader.unpack_from(blob);e=o+h.metadata_size;pe=e+(h.payload_bits+7)//8;meta=blob[o:e];f=list(_FREQS.unpack(meta));C=cdf(f);out=bytes(decode_symbols(blob[e:pe],h.original_size,lambda i,p:C));
 if hashlib.sha256(out).digest()!=h.original_sha256:raise ValueError('SHA mismatch')
 return out
