from bisect import bisect_right
_FULL=1<<32; _MASK=_FULL-1; _HALF=_FULL>>1; _Q=_HALF>>1; _TQ=_Q*3
class W:
 def __init__(self): self.b=bytearray(); self.c=0; self.u=0; self.bit_length=0
 def write(self,x):
  self.c=(self.c<<1)|x; self.u+=1; self.bit_length+=1
  if self.u==8: self.b.append(self.c); self.c=0; self.u=0
 def finish(self):
  if self.u:self.b.append(self.c<<(8-self.u))
  return bytes(self.b)
class R:
 def __init__(self,d): self.d=d; self.i=0
 def read(self):
  if self.i>=len(self.d)*8:self.i+=1;return 0
  x=(self.d[self.i//8]>>(7-self.i%8))&1;self.i+=1;return x
def valid(c):
 if len(c)<2 or c[0]!=0 or any(a>=b for a,b in zip(c,c[1:])): raise ValueError('invalid cdf')
def encode_symbols(symbols,cdfs):
 w=W();low=0;high=_MASK;pending=0
 def emit(bit):
  nonlocal pending
  w.write(bit)
  for _ in range(pending):w.write(1-bit)
  pending=0
 for s,c in zip(symbols,cdfs,strict=True):
  valid(c);total=c[-1];width=high-low+1;old=low;low=old+width*c[s]//total;high=old+width*c[s+1]//total-1
  while True:
   if high<_HALF:emit(0)
   elif low>=_HALF:emit(1);low-=_HALF;high-=_HALF
   elif low>=_Q and high<_TQ:pending+=1;low-=_Q;high-=_Q
   else:break
   low=(low<<1)&_MASK;high=((high<<1)&_MASK)|1
 pending+=1;emit(0 if low<_Q else 1);return w.finish(),w.bit_length
def decode_symbols(payload,n,provider):
 r=R(payload);low=0;high=_MASK;code=0
 for _ in range(32):code=((code<<1)|r.read())&_MASK
 out=[]
 for i in range(n):
  c=provider(i,out);valid(c);total=c[-1];width=high-low+1;scaled=((code-low+1)*total-1)//width;s=bisect_right(c,scaled)-1;old=low;low=old+width*c[s]//total;high=old+width*c[s+1]//total-1
  while True:
   if high<_HALF:pass
   elif low>=_HALF:low-=_HALF;high-=_HALF;code-=_HALF
   elif low>=_Q and high<_TQ:low-=_Q;high-=_Q;code-=_Q
   else:break
   low=(low<<1)&_MASK;high=((high<<1)&_MASK)|1;code=((code<<1)&_MASK)|r.read()
  out.append(s)
 return out
