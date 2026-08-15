import unittest
from main import add_vectors,causal_mask,context_windows
class TestHidden(unittest.TestCase):
 def test_mismatch(self):
  with self.assertRaises(ValueError): add_vectors([1],[1,2])
 def test_negative(self):
  with self.assertRaises(ValueError): causal_mask(-1)
 def test_context_positive(self):
  with self.assertRaises(ValueError): context_windows(b"abc",0)
 def test_empty(self): self.assertEqual(causal_mask(0),[])
