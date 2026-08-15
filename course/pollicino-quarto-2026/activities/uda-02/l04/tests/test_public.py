import unittest,main
class TestNGramPublic(unittest.TestCase):
 def test_order_zero(self): self.assertIn(b"",main.train_ngram(b"ABCABC",0).context_counts)
 def test_distribution(self): self.assertAlmostEqual(sum(main.context_distribution(main.train_ngram(b"ABABAB",1),b"A",0.5)),1.0)
 def test_alternation(self): self.assertEqual(main.most_likely_next(main.train_ngram(b"AB"*200,1),b"A",0.1)[0],66)
 def test_bigram_beats_zero(self):
  tr=b"AB"*1000; te=b"AB"*200; self.assertLess(main.evaluate_bpb(main.train_ngram(tr,1),te,0.1),main.evaluate_bpb(main.train_ngram(tr,0),te,0.1))
 def test_short(self): self.assertEqual(main.evaluate_bpb(main.train_ngram(b"A",2),b"A",0.5),0.0)
if __name__=="__main__":unittest.main()
