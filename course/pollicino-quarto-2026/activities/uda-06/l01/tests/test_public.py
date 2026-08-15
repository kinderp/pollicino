import unittest
from fractions import Fraction
from main import normalized_intervals,arithmetic_trace,interval_information_bits
class T(unittest.TestCase):
 def test_intervals(self):
  x=normalized_intervals({'A':3,'B':1}); self.assertEqual(x['A'],(Fraction(0),Fraction(3,4))); self.assertEqual(x['B'],(Fraction(3,4),Fraction(1)))
 def test_trace(self): self.assertEqual(arithmetic_trace('AB',{'A':3,'B':1})[-1],(Fraction(9,16),Fraction(3,4)))
 def test_bits(self): self.assertAlmostEqual(interval_information_bits(Fraction(0),Fraction(1,4)),2.0)
