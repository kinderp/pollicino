import unittest, torch
from main import ModelConfig, ByteTransformer, count_parameters, loss_nats
class TestTorchPublic(unittest.TestCase):
    def test_shape(self):
        m=ByteTransformer(ModelConfig(context_length=8,d_model=16,n_heads=4,n_layers=1,d_ff=32))
        x=torch.tensor([[1,2,3,4]],dtype=torch.long); self.assertEqual(tuple(m(x).shape),(1,4,256))
    def test_parameter_count(self):
        m=ByteTransformer(ModelConfig(context_length=8,d_model=16,n_heads=4,n_layers=1,d_ff=32)); self.assertGreater(count_parameters(m),5000)
    def test_loss_scalar(self):
        m=ByteTransformer(ModelConfig(context_length=4,d_model=8,n_heads=2,n_layers=1,d_ff=16)); x=torch.tensor([[1,2,3,4]]); y=torch.tensor([[2,3,4,5]])
        self.assertEqual(loss_nats(m(x),y).ndim,0)
if __name__=='__main__': unittest.main()
