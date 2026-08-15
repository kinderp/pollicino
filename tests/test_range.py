import random
from pollicino.compression.models import Order1CountModel,uniform_cdf
from pollicino.compression.quantization import frequencies_to_cdf,probabilities_to_frequencies
from pollicino.compression.range_coder import decode_symbols,encode_symbols

def test_uniform_roundtrip():
 d=bytes(range(256))+b'POLLICINO'*10; cdf=uniform_cdf(); p,b=encode_symbols(d,[cdf]*len(d)); assert bytes(decode_symbols(p,len(d),lambda i,x:cdf))==d; assert b>0

def test_random_roundtrip_many_lengths():
 r=random.Random(123); cdf=uniform_cdf()
 for n in [0,1,2,7,31,257,1000]:
  d=bytes(r.randrange(256) for _ in range(n)); p,_=encode_symbols(d,[cdf]*len(d)); assert bytes(decode_symbols(p,len(d),lambda i,x:cdf))==d

def test_skewed_static_roundtrip():
 f=probabilities_to_frequencies([.8,.15,.05],12); cdf=frequencies_to_cdf(f); d=[0]*100+[1]*20+[2]*5; p,b=encode_symbols(d,[cdf]*len(d)); assert decode_symbols(p,len(d),lambda i,x:cdf)==d; assert b<len(d)*2

def test_order1_provider_roundtrip():
 train=b'abracadabra abracadabra '*10; d=b'abracadabra abracadabra'; m=Order1CountModel(train); cdfs=[m(i,d[:i]) for i in range(len(d))]; p,_=encode_symbols(d,cdfs); m2=Order1CountModel(train); assert bytes(decode_symbols(p,len(d),m2))==d; assert m.fingerprint()==m2.fingerprint()
