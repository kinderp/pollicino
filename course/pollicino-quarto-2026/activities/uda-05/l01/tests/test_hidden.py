import unittest
from main import contiguous_split, make_examples, batch_iter
class TestDatasetHidden(unittest.TestCase):
    def test_invalid_fractions(self):
        for args in [(0,0.1),(0.9,0.2)]:
            with self.assertRaises(ValueError): contiguous_split(b"abc",*args)
    def test_short_data(self): self.assertEqual(make_examples(b"ab",2),[])
    def test_stride(self): self.assertEqual(len(make_examples(b"abcdef",2,stride=2)),2)
    def test_batch_size_error(self):
        with self.assertRaises(ValueError): list(batch_iter([],0))
if __name__=='__main__': unittest.main()
