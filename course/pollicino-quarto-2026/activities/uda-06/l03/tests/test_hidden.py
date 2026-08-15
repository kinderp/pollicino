import unittest
from main import benchmark
class T(unittest.TestCase):
 def test_empty(self): self.assertTrue(all(v['roundtrip'] for v in benchmark(b'').values()))
 def test_repetitive(self): self.assertLess(benchmark(b'A'*5000)['zlib']['bpb'],1.0)
