import math,unittest,main
class TestZeroOrderHidden(unittest.TestCase):
 def test_empty(self): self.assertEqual(main.entropy_bpb(b""),0.0)
 def test_smoothed_sum(self): self.assertAlmostEqual(sum(main.smoothed_probabilities(b"AAA",1.0)),1.0)
 def test_unseen_positive(self): self.assertGreater(main.smoothed_probabilities(b"AAA",0.5)[66],0.0)
 def test_unseen_infinite(self): self.assertTrue(math.isinf(main.cross_entropy_bpb(b"B",main.empirical_probabilities(b"AAAA"))))
 def test_top(self):
  t=main.top_bytes(b"AAABBCC",2); self.assertEqual(t[0][0],65); self.assertEqual(t[0][1],3)
if __name__=="__main__":unittest.main()
