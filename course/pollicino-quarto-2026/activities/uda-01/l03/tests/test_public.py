import unittest

from main import information_bits, sequence_information


class TestInformation(unittest.TestCase):
    def test_powers_of_two(self):
        self.assertAlmostEqual(information_bits(1), 0)
        self.assertAlmostEqual(information_bits(1 / 2), 1)
        self.assertAlmostEqual(information_bits(1 / 4), 2)
        self.assertAlmostEqual(information_bits(1 / 256), 8)

    def test_information_adds_for_a_sequence(self):
        self.assertAlmostEqual(sequence_information([1 / 2, 1 / 4]), 3)

    def test_invalid_probability(self):
        for p in (0, -0.1, 1.1):
            with self.assertRaises(ValueError):
                information_bits(p)


if __name__ == "__main__":
    unittest.main()
