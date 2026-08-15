import unittest,main
class TestBenchmarkPublic(unittest.TestCase):
 def test_uniform(self): self.assertEqual(main.uniform_bpb(),8.0)
 def test_ratio(self): self.assertAlmostEqual(main.ideal_ratio_from_bpb(4.0),0.5)
 def test_split(self):
  d=b"abcdefghij"; tr,te=main.split_train_test(d,0.8); self.assertEqual(tr+te,d); self.assertTrue(tr); self.assertTrue(te)
 def test_models(self):
  r=main.benchmark_models(b"AB"*500,b"AB"*100,2,0.1); self.assertEqual([x["model"] for x in r],["uniform","0-gram","1-gram","2-gram"])
 def test_context_beats_uniform(self):
  r=main.benchmark_models(b"AB"*1000,b"AB"*200,1,0.1); one=next(x for x in r if x["model"]=="1-gram"); self.assertLess(float(one["bpb"]),8.0)
if __name__=="__main__":unittest.main()
