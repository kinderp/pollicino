from __future__ import annotations
from collections import Counter
import heapq
from pathlib import Path
from typing import Optional
Node=tuple[Optional[int],object,object]

def byte_frequencies(data:bytes)->dict[int,int]: return dict(Counter(data))

def huffman_code_lengths(data:bytes)->dict[int,int]:
    # TODO: costruisci l'albero combinando i due nodi meno frequenti e restituisci le profondita.
    raise NotImplementedError

def canonical_codes(lengths:dict[int,int])->dict[int,tuple[int,int]]:
    # TODO: ordina per (lunghezza, simbolo) e genera i codici canonici.
    raise NotImplementedError

def is_prefix_free(codes:dict[int,tuple[int,int]])->bool:
    values=[format(code,f"0{length}b") for code,length in codes.values()]
    return all(i==j or not b.startswith(a) for i,a in enumerate(values) for j,b in enumerate(values))

def encode_payload(data:bytes,codes:dict[int,tuple[int,int]])->tuple[bytes,int]:
    # TODO: impacchetta i codeword MSB-first e restituisci anche il numero di bit validi.
    raise NotImplementedError

def decode_payload(payload:bytes,bit_length:int,codes:dict[int,tuple[int,int]])->bytes:
    # TODO: riconosci progressivamente i codeword e ricostruisci i byte.
    raise NotImplementedError

def payload_bits(data:bytes,lengths:dict[int,int])->int:
    f=byte_frequencies(data); return sum(f[s]*lengths[s] for s in f)

def estimated_codebook_bits(lengths:dict[int,int])->int: return 16*len(lengths)

def analyze(path:Path)->dict[str,int|float|bool]:
    data=path.read_bytes(); lengths=huffman_code_lengths(data); codes=canonical_codes(lengths); payload,n=encode_payload(data,codes); decoded=decode_payload(payload,n,codes)
    return {"original_bits":len(data)*8,"payload_bits":n,"estimated_codebook_bits":estimated_codebook_bits(lengths),"payload_bpb":n/len(data) if data else 0.0,"roundtrip_ok":decoded==data}

if __name__=="__main__": print(analyze(Path("fixtures/corpus.txt")))
