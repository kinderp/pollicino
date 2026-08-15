import unittest
from main import init_model, make_examples, loss_bits, train, bigram_bpb

class TestMLPHidden(unittest.TestCase):
    def test_training_reduces_training_bpb(self):
        data=(b'ABRACADABRA! '*10)
        model=init_model(context_size=2,embedding_dim=3,hidden_dim=6,seed=3)
        before=loss_bits(model,make_examples(data,2))
        history=train(model,data,epochs=3,learning_rate=0.08)
        self.assertLess(history[-1],before)

    def test_bigram_is_finite_for_unseen(self):
        self.assertGreater(bigram_bpb(b'AAAAABBBBB',b'XYZXYZ'),0)

    def test_empty_examples_loss(self):
        model=init_model(); self.assertEqual(loss_bits(model,[]),0.0)

if __name__ == '__main__': unittest.main()
