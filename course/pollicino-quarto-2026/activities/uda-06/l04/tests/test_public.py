import unittest
from main import validate_run,changed_controls,is_single_factor_ablation,delta_bpb
A={'id':'a','dataset_hash':'x','model':'m','precision_bits':15,'seed':1,'bpb':4.0}
class T(unittest.TestCase):
 def test_validate(self): self.assertTrue(validate_run(A)); self.assertFalse(validate_run({'id':'x'}))
 def test_one_change(self):
  b={**A,'precision_bits':12}; self.assertEqual(changed_controls(A,b),['precision_bits']); self.assertTrue(is_single_factor_ablation(A,b))
 def test_delta(self): self.assertAlmostEqual(delta_bpb(A,{**A,'bpb':3.5}),-0.5)
