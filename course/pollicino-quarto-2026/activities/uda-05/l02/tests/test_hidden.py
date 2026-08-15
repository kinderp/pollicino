import unittest, torch
from main import ModelConfig, ByteTransformer, train_steps
class TestTorchHidden(unittest.TestCase):
    def test_future_does_not_change_prefix(self):
        torch.manual_seed(3); m=ByteTransformer(ModelConfig(context_length=6,d_model=16,n_heads=4,n_layers=1,d_ff=32)); m.eval()
        a=torch.tensor([[1,2,3,4,5,6]]); b=torch.tensor([[1,2,3,99,100,101]])
        with torch.no_grad(): la,lb=m(a),m(b)
        self.assertTrue(torch.allclose(la[:,:3],lb[:,:3],atol=1e-6))
    def test_training_reduces_loss_on_repetitive_data(self):
        data=(b'ABRACADABRA '*80); cfg=ModelConfig(context_length=8,d_model=16,n_heads=4,n_layers=1,d_ff=32)
        _,h=train_steps(data,cfg,steps=30,batch_size=16,lr=5e-3,device='cpu',seed=4)
        self.assertLess(sum(h[-5:])/5, sum(h[:5])/5)
if __name__=='__main__': unittest.main()
