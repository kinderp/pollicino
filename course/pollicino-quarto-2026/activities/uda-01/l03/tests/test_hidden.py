import unittest

from main import information_bits, most_surprising


class TestInformationHidden(unittest.TestCase):
    def test_less_probable_means_more_information(self):
        self.assertGreater(information_bits(0.01), information_bits(0.5))

    def test_most_surprising(self):
        index, info = most_surprising([0.5, 0.25, 0.125])
        self.assertEqual(index, 2)
        self.assertAlmostEqual(info, 3)

    def test_empty_list_rejected(self):
        with self.assertRaises(ValueError):
            most_surprising([])


if __name__ == "__main__":
    unittest.main()
