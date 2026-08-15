import tempfile
import unittest
from pathlib import Path

from main import byte_counts, roundtrip_copy, shannon_entropy, uniform_code_length_bits


class TestEntropy(unittest.TestCase):
    def test_counts_cover_all_bytes(self):
        counts = byte_counts(b"AAB")
        self.assertEqual(len(counts), 256)
        self.assertEqual(counts[65], 2)
        self.assertEqual(counts[66], 1)
        self.assertEqual(sum(counts), 3)

    def test_entropy_known_examples(self):
        self.assertAlmostEqual(shannon_entropy(b""), 0.0)
        self.assertAlmostEqual(shannon_entropy(b"AAAA"), 0.0)
        self.assertAlmostEqual(shannon_entropy(b"ABAB"), 1.0)

    def test_uniform_model_costs_eight_bits_per_byte(self):
        self.assertEqual(uniform_code_length_bits(b"abc"), 24)

    def test_roundtrip_is_byte_exact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.bin"
            target = Path(temp_dir) / "target.bin"
            source.write_bytes(bytes(range(256)))
            before, after = roundtrip_copy(source, target)
            self.assertEqual(before, after)
            self.assertEqual(source.read_bytes(), target.read_bytes())


if __name__ == "__main__":
    unittest.main()
