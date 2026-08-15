import unittest
from main import cross_entropy, cross_entropy_gradient, numerical_gradient, gradient_descent

class TestGradientHidden(unittest.TestCase):
    def test_softmax_ce_gradient_matches_numerical(self):
        logits=[0.3,-0.2,1.1]; target=2
        analytic=cross_entropy_gradient(logits,target)
        for i in range(3):
            def f(v):
                copy=logits.copy(); copy[i]=v; return cross_entropy(copy,target)
            numeric=numerical_gradient(f, logits[i])
            self.assertAlmostEqual(analytic[i],numeric,places=5)

    def test_invalid_learning_rate(self):
        with self.assertRaises(ValueError): gradient_descent(1,lambda x:x,0,1)

if __name__ == '__main__': unittest.main()
