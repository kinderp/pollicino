import unittest
from main import contiguous_split, make_examples, batch_iter

class TestDatasetPublic(unittest.TestCase):
    def test_split_lengths(self):
        tr,va,te=contiguous_split(bytes(range(100)),0.8,0.1)
        self.assertEqual((len(tr),len(va),len(te)),(80,10,10))
        self.assertEqual(tr+va+te, bytes(range(100)))
    def test_shifted_windows(self):
        ex=make_examples(b"ABCDE",3)
        self.assertEqual(ex[0],([65,66,67],[66,67,68]))
    def test_batch_determinism(self):
        ex=make_examples(b"ABCDEFGHIJ",2)
        a=list(batch_iter(ex,3,shuffle=True,seed=7))
        b=list(batch_iter(ex,3,shuffle=True,seed=7))
        self.assertEqual(a,b)
if __name__=='__main__': unittest.main()
