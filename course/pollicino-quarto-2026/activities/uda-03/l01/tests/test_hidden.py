import unittest
from main import dot, linear_logits, parameter_count

class TestLogitsHidden(unittest.TestCase):
    def test_dot_dimension_error(self):
        with self.assertRaises(ValueError): dot([1],[1,2])

    def test_weight_shape_error(self):
        with self.assertRaises(ValueError): linear_logits([1,2], [[1]], [0])

    def test_bias_count_error(self):
        with self.assertRaises(ValueError): linear_logits([1], [[1],[2]], [0])

    def test_negative_dimension(self):
        with self.assertRaises(ValueError): parameter_count(-1,3)

if __name__ == '__main__': unittest.main()
