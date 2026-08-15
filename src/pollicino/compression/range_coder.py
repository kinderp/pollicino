from __future__ import annotations
from bisect import bisect_right
from collections.abc import Iterable, Sequence
_STATE_BITS=32; _FULL=1<<_STATE_BITS; _MASK=_FULL-1; _HALF=_FULL>>1; _QUARTER=_HALF>>1; _THREE_QUARTERS=_QUARTER*3
class _BitWriter:
    def __init__(self): self._buffer=bytearray(); self._current=0; self._used=0; self.bit_length=0
    def write(self,bit):
        if bit not in (0,1): raise ValueError('bit must be 0 or 1')
        self._current=(self._current<<1)|bit; self._used+=1; self.bit_length+=1
        if self._used==8: self._buffer.append(self._current); self._current=0; self._used=0
    def finish(self):
        if self._used: self._buffer.append(self._current<<(8-self._used)); self._current=0; self._used=0
        return bytes(self._buffer)
class _BitReader:
    def __init__(self,data): self.data=data; self.offset=0
    def read(self):
        if self.offset>=len(self.data)*8: self.offset+=1; return 0
        byte=self.data[self.offset//8]; shift=7-(self.offset%8); self.offset+=1; return (byte>>shift)&1

def validate_cdf(cdf:Sequence[int])->None:
    if len(cdf)<2: raise ValueError('cdf must contain at least two boundaries')
    if cdf[0]!=0: raise ValueError('cdf must start at zero')
    if cdf[-1]<=0: raise ValueError('cdf total must be positive')
    if any(a>=b for a,b in zip(cdf,cdf[1:])): raise ValueError('cdf boundaries must be strictly increasing')
    if cdf[-1]>_QUARTER: raise ValueError('cdf total is too large for 32-bit arithmetic state')

def encode_symbols(symbols:Iterable[int],cdfs:Iterable[Sequence[int]])->tuple[bytes,int]:
    writer=_BitWriter(); low=0; high=_MASK; pending=0
    def emit(bit):
        nonlocal pending
        writer.write(bit); opposite=1-bit
        for _ in range(pending): writer.write(opposite)
        pending=0
    for symbol,cdf in zip(symbols,cdfs,strict=True):
        validate_cdf(cdf)
        if not 0<=symbol<len(cdf)-1: raise ValueError('symbol outside cdf alphabet')
        total=cdf[-1]; width=high-low+1; old_low=low
        low=old_low+(width*cdf[symbol])//total; high=old_low+(width*cdf[symbol+1])//total-1
        if low>high: raise ArithmeticError('arithmetic interval collapsed')
        while True:
            if high<_HALF: emit(0)
            elif low>=_HALF: emit(1); low-=_HALF; high-=_HALF
            elif low>=_QUARTER and high<_THREE_QUARTERS: pending+=1; low-=_QUARTER; high-=_QUARTER
            else: break
            low=(low<<1)&_MASK; high=((high<<1)&_MASK)|1
    pending+=1; emit(0 if low<_QUARTER else 1)
    return writer.finish(),writer.bit_length

def decode_symbols(payload:bytes,symbol_count:int,cdf_provider)->list[int]:
    if symbol_count<0: raise ValueError('symbol_count must be non-negative')
    reader=_BitReader(payload); low=0; high=_MASK; code=0
    for _ in range(_STATE_BITS): code=((code<<1)|reader.read())&_MASK
    decoded=[]
    for index in range(symbol_count):
        cdf=cdf_provider(index,decoded); validate_cdf(cdf); total=cdf[-1]; width=high-low+1
        scaled=((code-low+1)*total-1)//width; symbol=bisect_right(cdf,scaled)-1
        if not 0<=symbol<len(cdf)-1: raise ArithmeticError('decoder could not locate symbol')
        old_low=low; low=old_low+(width*cdf[symbol])//total; high=old_low+(width*cdf[symbol+1])//total-1
        while True:
            if high<_HALF: pass
            elif low>=_HALF: low-=_HALF; high-=_HALF; code-=_HALF
            elif low>=_QUARTER and high<_THREE_QUARTERS: low-=_QUARTER; high-=_QUARTER; code-=_QUARTER
            else: break
            low=(low<<1)&_MASK; high=((high<<1)&_MASK)|1; code=((code<<1)&_MASK)|reader.read()
        decoded.append(symbol)
    return decoded
