import unittest,main
class TestBenchmarkHidden(unittest.TestCase):
 def test_invalid_fraction(self):
  with self.assertRaises(ValueError): main.split_train_test(b"abc",1.0)
 def test_negative_bpb(self):
  with self.assertRaises(ValueError): main.ideal_ratio_from_bpb(-0.1)
 def test_exact_split(self):
  d=bytes(range(100)); tr,te=main.split_train_test(d,0.75); self.assertEqual(tr,d[:75]); self.assertEqual(te,d[75:])
 def test_header(self): self.assertTrue(main.format_table([{"model":"uniform","order":-1,"bpb":8.0,"ideal_ratio":1.0}]).startswith("model\tbpb\tideal_ratio"))
if __name__=="__main__":unittest.main()
