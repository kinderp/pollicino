import math, unittest
from main import cross_entropy, cross_entropy_gradient, gradient_descent

class TestGradientPublic(unittest.TestCase):
    def test_good_logit_has_lower_loss(self):
        self.assertLess(cross_entropy([0,5,0],1), cross_entropy([0,0,5],1))

    def test_gradient_sums_zero(self):
        self.assertAlmostEqual(sum(cross_entropy_gradient([1,2,3],2)),0.0)

    def test_gradient_descent_quadratic(self):
        path=gradient_descent(10.0, lambda x: 2*(x-3), 0.1, 30)
        self.assertLess(abs(path[-1]-3), abs(path[0]-3))

if __name__ == '__main__': unittest.main()
