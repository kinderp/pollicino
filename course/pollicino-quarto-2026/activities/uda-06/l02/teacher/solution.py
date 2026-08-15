from __future__ import annotations
import hashlib,struct
from collections import Counter
from support.pol_format import MODEL_STATIC_HISTOGRAM,PolHeader
from support.range_coder import encode_symbols,decode_symbols
_FREQS=struct.Struct('>256H')
def quantize_counts(data,precision_bits=15):
 total=1<<precision_bits; counts=Counter(data); raw=[counts[i] for i in range(256)]; mass=sum(raw)
 if mass==0: return [total//256]*256
 remaining=total-256; scaled=[c*remaining/mass for c in raw]; floors=[int(x) for x in scaled]; f=[1+x for x in floors]; left=total-sum(f); order=sorted(range(256),key=lambda i:(-(scaled[i]-floors[i]),i))
 for i in order[:left]: f[i]+=1
 return f
def frequencies_to_cdf(freqs):
 if len(freqs)!=256 or any((not isinstance(x,int)) or x<=0 for x in freqs): raise ValueError('need 256 positive frequencies')
 c=[0]; r=0
 for x in freqs: r+=x; c.append(r)
 return c
def encode_pol(data,precision_bits=15):
 f=quantize_counts(data,precision_bits); meta=_FREQS.pack(*f); cdf=frequencies_to_cdf(f); payload,bits=encode_symbols(data,[cdf]*len(data)); fp=hashlib.sha256(b'static-histogram-v1'+bytes([precision_bits])+meta).digest(); sha=hashlib.sha256(data).digest(); h=PolHeader(MODEL_STATIC_HISTOGRAM,precision_bits,len(data),len(meta),bits,sha,fp); return h.pack()+meta+payload
def decode_pol(blob):
 h,off=PolHeader.unpack_from(blob); end=off+h.metadata_size; payload_end=end+(h.payload_bits+7)//8
 if payload_end!=len(blob) or h.model_kind!=MODEL_STATIC_HISTOGRAM: raise ValueError('invalid POL file')
 meta=blob[off:end]; f=list(_FREQS.unpack(meta)); cdf=frequencies_to_cdf(f)
 if sum(f)!=(1<<h.precision_bits): raise ValueError('invalid frequency total')
 if hashlib.sha256(b'static-histogram-v1'+bytes([h.precision_bits])+meta).digest()!=h.model_fingerprint: raise ValueError('model fingerprint mismatch')
 out=bytes(decode_symbols(blob[end:payload_end],h.original_size,lambda i,p:cdf))
 if hashlib.sha256(out).digest()!=h.original_sha256: raise ValueError('SHA mismatch')
 return out
