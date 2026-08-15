import unittest
from main import is_single_factor_ablation,changed_controls
A={'id':'a','dataset_hash':'x','model':'m','precision_bits':15,'seed':1,'bpb':4.0}
class T(unittest.TestCase):
 def test_zero_changes_not_ablation(self): self.assertFalse(is_single_factor_ablation(A,{**A,'id':'b'}))
 def test_two_changes_not_ablation(self): self.assertFalse(is_single_factor_ablation(A,{**A,'model':'n','precision_bits':12}))
 def test_invalid_raises(self):
  with self.assertRaises(ValueError): changed_controls(A,{'id':'bad'})
