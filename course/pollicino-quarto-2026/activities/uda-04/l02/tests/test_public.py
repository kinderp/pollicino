import math,unittest
from main import dot,softmax,single_head_attention
class TestAttention(unittest.TestCase):
 def test_dot(self): self.assertEqual(dot([1,2],[3,4]),11)
 def test_softmax(self): self.assertAlmostEqual(sum(softmax([1,2,3])),1.0,places=12)
 def test_stable(self): self.assertTrue(all(math.isfinite(x) for x in softmax([1000,1001])))
 def test_shape(self):
  x=[[1.,0.],[0.,1.]];i=[[1.,0.],[0.,1.]];o,w=single_head_attention(x,i,i,i);self.assertEqual((len(o),len(o[0])),(2,2));self.assertAlmostEqual(sum(w[0]),1.0)
