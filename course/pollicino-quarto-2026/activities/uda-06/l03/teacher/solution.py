from __future__ import annotations
import bz2,gzip,lzma,zlib
from support.reference_codec import encode_pol,decode_pol
def benchmark(data):
 codecs={'pol-static':(encode_pol,decode_pol),'gzip':(gzip.compress,gzip.decompress),'bz2':(bz2.compress,bz2.decompress),'lzma':(lzma.compress,lzma.decompress),'zlib':(zlib.compress,zlib.decompress)}; out={'raw':{'bytes':len(data),'bpb':8.0 if data else 0.0,'roundtrip':True}}
 for name,(enc,dec) in codecs.items():
  blob=enc(data); restored=dec(blob); out[name]={'bytes':len(blob),'bpb':len(blob)*8/len(data) if data else 0.0,'roundtrip':restored==data}
 return out
