import unittest
from main import causal_attention,future_leakage_check,identity_projector
class TestCausalAttention(unittest.TestCase):
 def test_future_weights_are_zero(self):
  q,k,v=identity_projector([1,2,3,4]);_,w=causal_attention(q,k,v);self.assertEqual(w[0][1:],[0.,0.,0.]);self.assertEqual(w[1][2:],[0.,0.])
 def test_visible_weights_sum_to_one(self):
  _,w=causal_attention(*identity_projector([1,2,3]));[self.assertAlmostEqual(sum(r),1.0,places=12) for r in w]
 def test_future_change_does_not_change_prefix(self): self.assertTrue(future_leakage_check([1,2,3,4,5],[1,2,3,99,100],identity_projector,3))
