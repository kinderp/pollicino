import math, unittest
from main import softmax, predicted_class, probability_of

class TestSoftmaxPublic(unittest.TestCase):
    def test_uniform(self):
        p=softmax([0,0,0,0])
        self.assertTrue(all(math.isclose(x,0.25) for x in p))

    def test_sum_one(self):
        self.assertAlmostEqual(sum(softmax([1,2,3])),1.0)

    def test_prediction(self):
        self.assertEqual(predicted_class([-1,7,3]),1)

    def test_probability_of(self):
        self.assertGreater(probability_of([0,3,0],1),0.8)

if __name__ == '__main__': unittest.main()
