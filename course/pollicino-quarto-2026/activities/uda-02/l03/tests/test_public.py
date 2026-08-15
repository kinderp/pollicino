import unittest,main
class TestZeroOrderPublic(unittest.TestCase):
 def test_counts(self):
  c=main.byte_counts(b"ABBA"); self.assertEqual(len(c),256); self.assertEqual(c[65],2); self.assertEqual(c[66],2)
 def test_probs(self): self.assertAlmostEqual(sum(main.empirical_probabilities(b"AAAB")),1.0)
 def test_constant_entropy(self): self.assertAlmostEqual(main.entropy_bpb(b"A"*100),0.0)
 def test_two_symbols(self): self.assertAlmostEqual(main.entropy_bpb(b"AB"*100),1.0)
 def test_uniform_cost(self): self.assertAlmostEqual(main.cross_entropy_bpb(b"POLLICINO",[1/256]*256),8.0)
if __name__=="__main__":unittest.main()
