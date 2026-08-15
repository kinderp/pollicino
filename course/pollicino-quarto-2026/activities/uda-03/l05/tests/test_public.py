import math, unittest
from main import init_model, make_examples, forward, loss_bits

class TestMLPPublic(unittest.TestCase):
    def test_examples(self):
        self.assertEqual(make_examples(b'ABCD',2), [([65,66],67),([66,67],68)])

    def test_forward_distribution(self):
        model=init_model(context_size=2,embedding_dim=3,hidden_dim=5,seed=1)
        p,_=forward(model,[65,66])
        self.assertEqual(len(p),256); self.assertAlmostEqual(sum(p),1.0)
        self.assertTrue(all(0 < x < 1 for x in p))

    def test_initial_loss_is_finite(self):
        model=init_model(seed=1)
        self.assertTrue(math.isfinite(loss_bits(model,make_examples(b'ABRACADABRA',2))))

if __name__ == '__main__': unittest.main()
