import unittest
from main import TinyByteTransformer,causal_prefix_equal
class TestTinyTransformer(unittest.TestCase):
 def test_forward_shape(self):
  m=TinyByteTransformer(d_model=8,n_heads=2,d_ff=12,n_layers=1,context_length=6,seed=1);o=m.forward([65,66,67]);self.assertEqual((len(o),len(o[0])),(3,256))
 def test_probabilities(self):self.assertAlmostEqual(sum(TinyByteTransformer(seed=1).probabilities([65,66])[-1]),1.0,places=12)
 def test_parameter_count(self):self.assertGreater(TinyByteTransformer().parameter_count(),4096)
 def test_causality(self):self.assertTrue(causal_prefix_equal(TinyByteTransformer(seed=3),[1,2,3,4,5],[1,2,3,99,100],3))
