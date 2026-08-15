from __future__ import annotations
import struct
from dataclasses import dataclass
MAGIC=b'POL1'; FORMAT_VERSION=1; MODEL_UNIFORM=0; MODEL_STATIC_HISTOGRAM=1; MODEL_SHARED=2; _HEADER=struct.Struct('>4sBBBBQIQ32s32s')
@dataclass(frozen=True)
class PolHeader:
 model_kind:int; precision_bits:int; original_size:int; metadata_size:int; payload_bits:int; original_sha256:bytes; model_fingerprint:bytes; flags:int=0; version:int=FORMAT_VERSION
 def pack(self):
  if self.model_kind not in {0,1,2}: raise ValueError('unknown model kind')
  if not 8<=self.precision_bits<=20: raise ValueError('unsupported precision')
  if len(self.original_sha256)!=32 or len(self.model_fingerprint)!=32: raise ValueError('hashes must be 32 bytes')
  return _HEADER.pack(MAGIC,self.version,self.model_kind,self.precision_bits,self.flags,self.original_size,self.metadata_size,self.payload_bits,self.original_sha256,self.model_fingerprint)
 @classmethod
 def unpack_from(cls,data):
  if len(data)<_HEADER.size: raise ValueError('truncated POL header')
  m,v,k,p,f,n,ms,pb,sha,fp=_HEADER.unpack_from(data)
  if m!=MAGIC or v!=FORMAT_VERSION: raise ValueError('invalid POL header')
  h=cls(k,p,n,ms,pb,sha,fp,f,v); h.pack(); return h,_HEADER.size
