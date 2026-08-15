from __future__ import annotations
import hashlib,time
def evaluate(compress,decompress,cases:dict[str,bytes]):
 rows=[]
 for name,data in cases.items():
  t=time.perf_counter(); blob=compress(data); enc=time.perf_counter()-t; t=time.perf_counter(); restored=decompress(blob); dec=time.perf_counter()-t; ok=(restored==data and hashlib.sha256(restored).digest()==hashlib.sha256(data).digest()); rows.append({'name':name,'input_bytes':len(data),'compressed_bytes':len(blob),'bpb':len(blob)*8/len(data) if data else 0.0,'encode_seconds':enc,'decode_seconds':dec,'roundtrip':ok})
 return rows
