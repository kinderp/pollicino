import unittest
from main import quantize_counts,frequencies_to_cdf,encode_pol,decode_pol
class T(unittest.TestCase):
 def test_quantization(self):
  f=quantize_counts(b'AAAAB',12); self.assertEqual(len(f),256); self.assertEqual(sum(f),4096); self.assertGreater(min(f),0); self.assertGreater(f[65],f[66])
 def test_cdf(self): self.assertEqual(frequencies_to_cdf([1]*256)[-1],256)
 def test_roundtrip(self):
  for d in [b'',b'A',b'banana banana',bytes(range(256))]: self.assertEqual(decode_pol(encode_pol(d)),d)
 def test_deterministic(self): self.assertEqual(encode_pol(b'banana'*20),encode_pol(b'banana'*20))
