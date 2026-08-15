import math,unittest
from main import rms_norm_row,multi_head_attention,transformer_block,demo_params
class TestBlock(unittest.TestCase):
 def test_norm(self):
  r=rms_norm_row([3.,4.],eps=0.);self.assertAlmostEqual(math.sqrt(sum(x*x for x in r)/2),1.)
 def test_multihead_shape(self):
  h,wo,*_=demo_params();o=multi_head_attention([[1,0,0,0],[0,1,0,0]],h,wo);self.assertEqual((len(o),len(o[0])),(2,4))
 def test_block_shape(self):self.assertEqual(len(transformer_block([[1,0,0,0],[0,1,0,0]],*demo_params())[0]),4)
