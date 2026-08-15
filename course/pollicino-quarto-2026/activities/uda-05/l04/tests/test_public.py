import unittest
from main import ModelConfig, expected_parameter_count, mlx_available
class TestMLXPublic(unittest.TestCase):
    def test_same_model_spec(self):
        cfg=ModelConfig(); self.assertEqual((cfg.vocab_size,cfg.d_model,cfg.n_heads,cfg.n_layers),(256,32,4,2))
    def test_parameter_formula(self): self.assertGreater(expected_parameter_count(ModelConfig()),30000)
    def test_availability_is_boolean(self): self.assertIsInstance(mlx_available(),bool)
if __name__=='__main__': unittest.main()
