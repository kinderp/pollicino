import math
import unittest

from main import byte_counts, shannon_entropy


class TestEntropyHidden(unittest.TestCase):
    def test_all_byte_values_once_have_eight_bits_entropy(self):
        self.assertAlmostEqual(shannon_entropy(bytes(range(256))), 8.0, places=10)

    def test_three_to_one_distribution(self):
        expected = -(0.75 * math.log2(0.75) + 0.25 * math.log2(0.25))
        self.assertAlmostEqual(shannon_entropy(b"AAAB"), expected)

    def test_counts_sum_to_input_length(self):
        data = bytes(range(32)) * 3
        self.assertEqual(sum(byte_counts(data)), len(data))


if __name__ == "__main__":
    unittest.main()
