import unittest
from main import causal_attention,future_leakage_check,identity_projector
class TestHidden(unittest.TestCase):
 def test_first(self): self.assertAlmostEqual(causal_attention(*identity_projector([7,2,3]))[0][0][0],7.0)
 def test_mismatch(self):
  with self.assertRaises(ValueError): causal_attention([[1]],[[1],[2]],[[1]])
 def test_prefix(self):
  with self.assertRaises(ValueError): future_leakage_check([1,2],[1,9],identity_projector,2)
