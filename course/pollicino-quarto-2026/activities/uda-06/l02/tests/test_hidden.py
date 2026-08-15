import unittest
from main import encode_pol,decode_pol,frequencies_to_cdf
class T(unittest.TestCase):
 def test_long_roundtrip(self):
  d=b'A'*3000+b'BC'*400; self.assertEqual(decode_pol(encode_pol(d)),d)
 def test_bad_cdf_input(self):
  with self.assertRaises(ValueError): frequencies_to_cdf([1,2])
 def test_corrupt_header_hash(self):
  b=bytearray(encode_pol(b'POLLICINO'*30)); b[30]^=1
  with self.assertRaises(ValueError): decode_pol(bytes(b))
