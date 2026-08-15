import random,unittest
from main import compress,decompress
class T(unittest.TestCase):
 def test_random_binary(self):
  r=random.Random(1337); d=bytes(r.randrange(256) for _ in range(4096)); self.assertEqual(decompress(compress(d)),d)
 def test_deterministic_roundtrip_many(self):
  for d in [b'A'*5000,b'abc'*999,bytes(range(256))*5]: self.assertEqual(decompress(compress(d)),d)
