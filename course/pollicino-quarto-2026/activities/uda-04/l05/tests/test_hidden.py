import math,unittest
from main import TinyByteTransformer
class TestHidden(unittest.TestCase):
 def test_seed(self):self.assertEqual(TinyByteTransformer(seed=9).forward([1,2,3]),TinyByteTransformer(seed=9).forward([1,2,3]))
 def test_limit(self):
  with self.assertRaises(ValueError):TinyByteTransformer(context_length=2).forward([1,2,3])
 def test_invalid(self):
  with self.assertRaises(ValueError):TinyByteTransformer().forward([256])
 def test_bpb(self):
  b=TinyByteTransformer(seed=4).next_byte_bpb(b'POLLICINO POLLICINO');self.assertTrue(math.isfinite(b));self.assertGreater(b,7.0);self.assertLess(b,9.0)
 def test_one(self):self.assertEqual(TinyByteTransformer().next_byte_bpb(b'A'),0.0)
