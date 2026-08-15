import math, unittest
from main import softmax, entropy_bits

class TestSoftmaxHidden(unittest.TestCase):
    def test_large_logits_are_stable(self):
        p=softmax([10000,10001,9999])
        self.assertTrue(all(math.isfinite(x) for x in p))
        self.assertAlmostEqual(sum(p),1.0)

    def test_shift_invariance(self):
        a=softmax([1,2,3]); b=softmax([101,102,103])
        for x,y in zip(a,b): self.assertAlmostEqual(x,y)

    def test_empty_rejected(self):
        with self.assertRaises(ValueError): softmax([])

    def test_uniform_entropy(self):
        self.assertAlmostEqual(entropy_bits([0.25]*4),2.0)

if __name__ == '__main__': unittest.main()
