import unittest
from main import rms_norm_row,transformer_block,demo_params
class TestHidden(unittest.TestCase):
 def test_zero(self):self.assertEqual(rms_norm_row([0.,0.]),[0.,0.])
 def test_causal(self):
  p=demo_params();a=[[1,0,0,0],[0,1,0,0],[1,1,0,0]];b=[[1,0,0,0],[0,1,0,0],[9,9,9,9]];oa=transformer_block(a,*p);ob=transformer_block(b,*p)
  for i in range(2):
   for x,y in zip(oa[i],ob[i]):self.assertAlmostEqual(x,y,places=12)
