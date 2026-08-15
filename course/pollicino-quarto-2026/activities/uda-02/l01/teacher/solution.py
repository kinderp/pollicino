from __future__ import annotations

from pathlib import Path


def rle_encode(data: bytes) -> bytes:
    if not data: return b""
    out=bytearray(); run_value=data[0]; run_count=1
    for value in data[1:]:
        if value==run_value and run_count<255: run_count+=1
        else: out.extend((run_count,run_value)); run_value=value; run_count=1
    out.extend((run_count,run_value)); return bytes(out)


def rle_decode(encoded: bytes) -> bytes:
    if len(encoded)%2: raise ValueError("RLE stream length must be even")
    out=bytearray()
    for i in range(0,len(encoded),2):
        count,value=encoded[i],encoded[i+1]
        if count==0: raise ValueError("RLE count must be in 1..255")
        out.extend([value]*count)
    return bytes(out)


def compression_ratio(original: bytes, encoded: bytes) -> float:
    return 1.0 if not original else len(encoded)/len(original)


def savings_percent(original: bytes, encoded: bytes) -> float:
    return 0.0 if not original else 100.0*(1.0-compression_ratio(original,encoded))


def analyze_file(path: Path) -> dict[str,float|int|bool]:
    data=path.read_bytes(); encoded=rle_encode(data); decoded=rle_decode(encoded)
    return {"original_bytes":len(data),"encoded_bytes":len(encoded),"ratio":compression_ratio(data,encoded),"savings_percent":savings_percent(data,encoded),"roundtrip_ok":decoded==data}


def main() -> None:
    for filename in ("fixtures/repetitive.txt","fixtures/mixed.txt","fixtures/nonrepetitive.txt"):
        print(filename, analyze_file(Path(filename)))


if __name__=="__main__": main()
