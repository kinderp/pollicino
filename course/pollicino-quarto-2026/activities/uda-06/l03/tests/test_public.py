import unittest
from main import benchmark
class T(unittest.TestCase):
 def test_keys(self): self.assertEqual(set(benchmark(b'hello '*50)),{'raw','pol-static','gzip','bz2','lzma','zlib'})
 def test_roundtrip(self): self.assertTrue(all(v['roundtrip'] for v in benchmark(b'A'*1000).values()))
 def test_bpb(self): self.assertEqual(benchmark(b'abc')['raw']['bpb'],8.0)
