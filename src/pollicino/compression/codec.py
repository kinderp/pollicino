from __future__ import annotations
import hashlib,struct
from .format import MODEL_SHARED,MODEL_STATIC_HISTOGRAM,MODEL_UNIFORM,PolHeader
from .models import CDFProvider,static_histogram_frequencies,uniform_cdf
from .quantization import frequencies_to_cdf
from .range_coder import decode_symbols,encode_symbols
_STATIC_FREQS=struct.Struct('>256H')
def _sha(data): return hashlib.sha256(data).digest()
def _assemble(header,metadata,payload):
    if len(metadata)!=header.metadata_size: raise ValueError('metadata size does not match header')
    if len(payload)!=(header.payload_bits+7)//8: raise ValueError('payload size does not match header bit length')
    return header.pack()+metadata+payload
def _split(blob):
    header,offset=PolHeader.unpack_from(blob); metadata_end=offset+header.metadata_size; payload_bytes=(header.payload_bits+7)//8; payload_end=metadata_end+payload_bytes
    if payload_end!=len(blob): raise ValueError('POL file size does not match header')
    return header,blob[offset:metadata_end],blob[metadata_end:payload_end]
def encode_uniform(data:bytes,precision_bits:int=15)->bytes:
    cdf=uniform_cdf(256,precision_bits); payload,bits=encode_symbols(data,[cdf]*len(data)); fp=_sha(f'uniform-v1:{precision_bits}'.encode())
    return _assemble(PolHeader(MODEL_UNIFORM,precision_bits,len(data),0,bits,_sha(data),fp),b'',payload)
def encode_static_histogram(data:bytes,precision_bits:int=15)->bytes:
    frequencies=static_histogram_frequencies(data,precision_bits)
    if max(frequencies)>0xffff: raise ValueError('frequency does not fit static metadata representation')
    metadata=_STATIC_FREQS.pack(*frequencies); cdf=frequencies_to_cdf(frequencies); payload,bits=encode_symbols(data,[cdf]*len(data)); fp=_sha(b'static-histogram-v1'+bytes([precision_bits])+metadata)
    return _assemble(PolHeader(MODEL_STATIC_HISTOGRAM,precision_bits,len(data),len(metadata),bits,_sha(data),fp),metadata,payload)
def encode_shared(data:bytes,provider:CDFProvider,model_fingerprint:bytes,precision_bits:int=15)->bytes:
    if len(model_fingerprint)!=32: raise ValueError('model fingerprint must be 32 bytes')
    prefix=[]
    def cdf_stream():
        for index,symbol in enumerate(data): yield provider(index,prefix); prefix.append(symbol)
    payload,bits=encode_symbols(data,cdf_stream())
    return _assemble(PolHeader(MODEL_SHARED,precision_bits,len(data),0,bits,_sha(data),model_fingerprint),b'',payload)
def decode_pol(blob:bytes,*,shared_provider:CDFProvider|None=None,expected_model_fingerprint:bytes|None=None)->bytes:
    header,metadata,payload=_split(blob)
    if header.model_kind==MODEL_UNIFORM:
        cdf=uniform_cdf(256,header.precision_bits); provider=lambda _i,_p:cdf
    elif header.model_kind==MODEL_STATIC_HISTOGRAM:
        if len(metadata)!=_STATIC_FREQS.size: raise ValueError('invalid static histogram metadata')
        frequencies=list(_STATIC_FREQS.unpack(metadata))
        if sum(frequencies)!=1<<header.precision_bits: raise ValueError('static frequencies do not match precision')
        cdf=frequencies_to_cdf(frequencies)
        if _sha(b'static-histogram-v1'+bytes([header.precision_bits])+metadata)!=header.model_fingerprint: raise ValueError('static model fingerprint mismatch')
        provider=lambda _i,_p:cdf
    elif header.model_kind==MODEL_SHARED:
        if shared_provider is None or expected_model_fingerprint is None: raise ValueError('shared-model POL file requires provider and expected fingerprint')
        if expected_model_fingerprint!=header.model_fingerprint: raise ValueError('shared model fingerprint mismatch')
        provider=shared_provider
    else: raise ValueError('unsupported model kind')
    decoded=bytes(decode_symbols(payload,header.original_size,provider))
    if _sha(decoded)!=header.original_sha256: raise ValueError('decoded SHA-256 does not match original')
    return decoded
def inspect_pol(blob:bytes)->dict:
    header,metadata,payload=_split(blob); name={MODEL_UNIFORM:'uniform',MODEL_STATIC_HISTOGRAM:'static-histogram',MODEL_SHARED:'shared-model'}[header.model_kind]; total_bits=len(blob)*8
    return {'model':name,'original_bytes':header.original_size,'header_and_metadata_bytes':len(blob)-len(payload),'payload_bytes':len(payload),'payload_bits':header.payload_bits,'file_bytes':len(blob),'realized_bpb':total_bits/header.original_size if header.original_size else 0.0,'payload_bpb':header.payload_bits/header.original_size if header.original_size else 0.0,'precision_bits':header.precision_bits,'model_fingerprint':header.model_fingerprint.hex(),'sha256':header.original_sha256.hex()}
