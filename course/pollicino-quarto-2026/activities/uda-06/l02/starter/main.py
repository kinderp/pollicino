from __future__ import annotations
import hashlib,struct
from collections import Counter
from support.pol_format import MODEL_STATIC_HISTOGRAM,PolHeader
from support.range_coder import encode_symbols,decode_symbols
_FREQS=struct.Struct('>256H')
def quantize_counts(data:bytes,precision_bits:int=15)->list[int]:
    # TODO: 256 frequenze positive, somma 2**precision_bits
    raise NotImplementedError
def frequencies_to_cdf(freqs:list[int])->list[int]:
    # TODO
    raise NotImplementedError
def encode_pol(data:bytes,precision_bits:int=15)->bytes:
    # TODO: metadata + payload + header POL1 + SHA256
    raise NotImplementedError
def decode_pol(blob:bytes)->bytes:
    # TODO: parse, range-decode, SHA256
    raise NotImplementedError
