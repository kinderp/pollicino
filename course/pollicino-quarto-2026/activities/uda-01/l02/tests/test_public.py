import hashlib
import unittest

from main import sha256_hex, truncated_hash_int


class TestHashes(unittest.TestCase):
    def test_sha256_known_vector(self):
        self.assertEqual(
            sha256_hex(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223"
            "b00361a396177a9cb410ff61f20015ad",
        )

    def test_first_eight_bits(self):
        expected = hashlib.sha256(b"abc").digest()[0]
        self.assertEqual(truncated_hash_int(b"abc", 8), expected)

    def test_invalid_width(self):
        for bits in (0, 257):
            with self.assertRaises(ValueError):
                truncated_hash_int(b"x", bits)


if __name__ == "__main__":
    unittest.main()
