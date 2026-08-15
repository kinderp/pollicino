import pytest
from pollicino.compression.codec import decode_pol,encode_shared,encode_static_histogram,encode_uniform,inspect_pol
from pollicino.compression.models import Order1CountModel
from pollicino.compression.format import header_size
@pytest.mark.parametrize('d',[b'',b'A',b'POLLICINO',bytes(range(256)),b'A'*1000])
def test_uniform_pol_roundtrip(d): assert decode_pol(encode_uniform(d))==d
@pytest.mark.parametrize('d',[b'',b'hello world'*50,b'A'*2000,bytes(range(256))*4])
def test_static_pol_roundtrip(d): assert decode_pol(encode_static_histogram(d))==d
def test_header_cost_visible():
 d=b'A'*5000+b'B'*500; info=inspect_pol(encode_static_histogram(d)); assert info['payload_bpb']<2 and info['realized_bpb']>info['payload_bpb']
def test_shared_roundtrip():
 train=b'abracadabra '*50; d=b'abracadabra abracadabra'; m=Order1CountModel(train); blob=encode_shared(d,m,m.fingerprint()); m2=Order1CountModel(train); assert decode_pol(blob,shared_provider=m2,expected_model_fingerprint=m2.fingerprint())==d
def test_wrong_model_rejected():
 a=Order1CountModel(b'aaaaabbbbb'); b=Order1CountModel(b'xyzxyzxyz'); blob=encode_shared(b'ababab',a,a.fingerprint())
 with pytest.raises(ValueError,match='fingerprint'): decode_pol(blob,shared_provider=b,expected_model_fingerprint=b.fingerprint())
def test_corruption_rejected():
 blob=bytearray(encode_uniform(b'POLLICINO'*20)); blob[header_size()+3]^=0x80
 with pytest.raises((ValueError,ArithmeticError)): decode_pol(bytes(blob))
