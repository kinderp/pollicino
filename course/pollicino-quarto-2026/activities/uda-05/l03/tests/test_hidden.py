import unittest, torch
from main import ModelConfig, ByteTransformer, evaluate_bpb, select_best_epoch
class TestValidationHidden(unittest.TestCase):
    def test_eval_is_deterministic_and_restores_mode(self):
        cfg=ModelConfig(context_length=4,d_model=8,n_heads=2,n_layers=1,d_ff=16); m=ByteTransformer(cfg); m.train()
        data=b'ABCD'*40; a=evaluate_bpb(m,data,4); b=evaluate_bpb(m,data,4)
        self.assertAlmostEqual(a,b,places=7); self.assertTrue(m.training)
    def test_empty_curve(self):
        with self.assertRaises(ValueError): select_best_epoch([])
if __name__=='__main__': unittest.main()
