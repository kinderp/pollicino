import unittest
from main import normalized_intervals,arithmetic_trace,interval_information_bits
class T(unittest.TestCase):
 def test_invalid_weights(self):
  with self.assertRaises(ValueError): normalized_intervals({'A':0})
 def test_unknown_symbol(self):
  with self.assertRaises(ValueError): arithmetic_trace('Z',{'A':1})
 def test_empty_sequence(self): self.assertEqual(arithmetic_trace('',{'A':1}),[])
 def test_invalid_width(self):
  with self.assertRaises(ValueError): interval_information_bits(1,1)
