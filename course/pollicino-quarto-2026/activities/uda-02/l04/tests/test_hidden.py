import math,unittest,main
class TestNGramHidden(unittest.TestCase):
 def test_negative_order(self):
  with self.assertRaises(ValueError): main.train_ngram(b"ABC",-1)
 def test_unseen_fallback(self):
  p=main.context_distribution(main.train_ngram(b"AAAAAB",2),b"ZZ",0.5); self.assertAlmostEqual(sum(p),1.0); self.assertGreater(p[65],p[90])
 def test_smoothing_finite(self): self.assertTrue(math.isfinite(main.evaluate_bpb(main.train_ngram(b"AAAA",1),b"AB",0.5)))
 def test_compare_shape(self): self.assertEqual([o for o,_ in main.compare_orders(b"ABCABCABC",b"ABCABC",2,0.5)],[0,1,2])
 def test_probability_range(self):
  p=main.next_byte_probability(main.train_ngram(b"ABAB",1),b"A",66,0.5); self.assertGreater(p,0); self.assertLessEqual(p,1)
if __name__=="__main__":unittest.main()
