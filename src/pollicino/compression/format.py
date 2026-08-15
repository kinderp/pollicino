from __future__ import annotations
import struct
from dataclasses import dataclass
MAGIC=b"POL1"; FORMAT_VERSION=1; MODEL_UNIFORM=0; MODEL_STATIC_HISTOGRAM=1; MODEL_SHARED=2
_HEADER=struct.Struct(">4sBBBBQIQ32s32s")
@dataclass(frozen=True)
class PolHeader:
    model_kind:int; precision_bits:int; original_size:int; metadata_size:int; payload_bits:int; original_sha256:bytes; model_fingerprint:bytes; flags:int=0; version:int=FORMAT_VERSION
    def pack(self)->bytes:
        if self.model_kind not in {MODEL_UNIFORM,MODEL_STATIC_HISTOGRAM,MODEL_SHARED}: raise ValueError("unknown model kind")
        if not 8<=self.precision_bits<=20: raise ValueError("unsupported precision")
        if self.original_size<0 or self.metadata_size<0 or self.payload_bits<0: raise ValueError("sizes must be non-negative")
        if len(self.original_sha256)!=32 or len(self.model_fingerprint)!=32: raise ValueError("hashes must be exactly 32 bytes")
        return _HEADER.pack(MAGIC,self.version,self.model_kind,self.precision_bits,self.flags,self.original_size,self.metadata_size,self.payload_bits,self.original_sha256,self.model_fingerprint)
    @classmethod
    def unpack_from(cls,data:bytes):
        if len(data)<_HEADER.size: raise ValueError("truncated POL header")
        magic,version,model_kind,precision_bits,flags,original_size,metadata_size,payload_bits,sha,fingerprint=_HEADER.unpack_from(data)
        if magic!=MAGIC: raise ValueError("not a POLLICINO file")
        if version!=FORMAT_VERSION: raise ValueError(f"unsupported POL format version: {version}")
        h=cls(model_kind,precision_bits,original_size,metadata_size,payload_bits,sha,fingerprint,flags,version); h.pack(); return h,_HEADER.size

def header_size()->int: return _HEADER.size
