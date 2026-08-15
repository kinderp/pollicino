import ast, pathlib, unittest
from main import ModelConfig, expected_parameter_count
class TestMLXHidden(unittest.TestCase):
    def test_config_rejects_bad_heads(self):
        with self.assertRaises(ValueError): ModelConfig(d_model=10,n_heads=4)
    def test_source_uses_current_mlx_training_contract(self):
        src=pathlib.Path('main.py').read_text();
        for token in ['nn.value_and_grad','optim.AdamW','optimizer.update','mx.eval']:
            self.assertIn(token,src)
        ast.parse(src)
if __name__=='__main__': unittest.main()
