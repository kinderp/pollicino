import unittest
from main import affine_scalar, linear_logits, parameter_count

class TestLogitsPublic(unittest.TestCase):
    def test_affine_scalar(self):
        self.assertEqual(affine_scalar(2, 3, 1), 7)

    def test_linear_logits(self):
        features=[1.0,2.0]
        weights=[[1.0,0.0],[0.0,1.0],[-1.0,1.0]]
        biases=[0.0,1.0,0.5]
        self.assertEqual(linear_logits(features,weights,biases), [1.0,3.0,1.5])

    def test_parameter_count(self):
        self.assertEqual(parameter_count(4, 256), 4*256+256)

if __name__ == '__main__': unittest.main()
