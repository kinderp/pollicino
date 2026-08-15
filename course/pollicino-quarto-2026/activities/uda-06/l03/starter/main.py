from __future__ import annotations
import bz2,gzip,lzma,zlib
from support.reference_codec import encode_pol,decode_pol
def benchmark(data:bytes)->dict[str,dict[str,float|int|bool]]:
    # TODO: raw, POL static, gzip, bz2, lzma, zlib; bytes, bpb, roundtrip
    raise NotImplementedError
