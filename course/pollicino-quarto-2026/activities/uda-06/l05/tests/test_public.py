import unittest
from main import compress,decompress
class T(unittest.TestCase):
 def test_roundtrip_text(self):
  d=b'POLLICINO '*100; self.assertEqual(decompress(compress(d)),d)
 def test_empty(self): self.assertEqual(decompress(compress(b'')),b'')
 def test_bytes(self):
  d=bytes(range(256)); self.assertEqual(decompress(compress(d)),d)
