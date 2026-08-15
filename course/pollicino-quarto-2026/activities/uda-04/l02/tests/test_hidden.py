import unittest
from main import dot,softmax,single_head_attention
class TestHidden(unittest.TestCase):
 def test_mismatch(self):
  with self.assertRaises(ValueError): dot([1],[1,2])
 def test_empty(self): self.assertEqual(softmax([]),[])
 def test_equal(self):
  _,w=single_head_attention([[1.],[1.]],[[1.]],[[1.]],[[1.]]);self.assertAlmostEqual(w[0][0],.5)
