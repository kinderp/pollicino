from __future__ import annotations
from collections import Counter
import heapq
from pathlib import Path
from typing import Optional
Node=tuple[Optional[int],object,object]

def byte_frequencies(data:bytes)->dict[int,int]: return dict(Counter(data))

def huffman_code_lengths(data:bytes)->dict[int,int]:
    f=byte_frequencies(data)
    if not f:return {}
    if len(f)==1:return {next(iter(f)):1}
    heap=[]; serial=0
    for s,n in sorted(f.items()): heapq.heappush(heap,(n,s,serial,(s,None,None))); serial+=1
    while len(heap)>1:
        f1,m1,_,a=heapq.heappop(heap); f2,m2,_,b=heapq.heappop(heap); heapq.heappush(heap,(f1+f2,min(m1,m2),serial,(None,a,b))); serial+=1
    lengths={}
    def visit(node,depth):
        s,l,r=node
        if s is not None:lengths[s]=max(1,depth); return
        visit(l,depth+1); visit(r,depth+1)
    visit(heap[0][3],0); return lengths

def canonical_codes(lengths):
    if not lengths:return {}
    ordered=sorted(lengths.items(),key=lambda x:(x[1],x[0])); code=0; prev=ordered[0][1]; out={}
    for s,l in ordered: code<<=l-prev; out[s]=(code,l); code+=1; prev=l
    return out

def is_prefix_free(codes):
    values=[format(c,f"0{l}b") for c,l in codes.values()]; return all(i==j or not b.startswith(a) for i,a in enumerate(values) for j,b in enumerate(values))

def encode_payload(data,codes):
    acc=0; nbits=0; total=0; out=bytearray()
    for s in data:
        c,l=codes[s]; acc=(acc<<l)|c; nbits+=l; total+=l
        while nbits>=8:
            shift=nbits-8; out.append((acc>>shift)&255); acc=acc&((1<<shift)-1) if shift else 0; nbits=shift
    if nbits: out.append((acc<<(8-nbits))&255)
    return bytes(out),total

def decode_payload(payload,bit_length,codes):
    if bit_length<0 or bit_length>len(payload)*8: raise ValueError("invalid bit length")
    if bit_length==0:return b""
    rev={(c,l):s for s,(c,l) in codes.items()}; out=bytearray(); cur=0; clen=0
    for i in range(bit_length):
        bit=(payload[i//8]>>(7-i%8))&1; cur=(cur<<1)|bit; clen+=1
        if (cur,clen) in rev: out.append(rev[(cur,clen)]); cur=0; clen=0
    if clen: raise ValueError("payload ended inside a codeword")
    return bytes(out)

def payload_bits(data,lengths):
    f=byte_frequencies(data); return sum(f[s]*lengths[s] for s in f)

def estimated_codebook_bits(lengths): return 16*len(lengths)

def analyze(path):
    data=Path(path).read_bytes(); lengths=huffman_code_lengths(data); codes=canonical_codes(lengths); payload,n=encode_payload(data,codes); decoded=decode_payload(payload,n,codes)
    return {"original_bits":len(data)*8,"payload_bits":n,"estimated_codebook_bits":estimated_codebook_bits(lengths),"payload_bpb":n/len(data) if data else 0.0,"roundtrip_ok":decoded==data}

if __name__=="__main__": print(analyze("fixtures/corpus.txt"))
