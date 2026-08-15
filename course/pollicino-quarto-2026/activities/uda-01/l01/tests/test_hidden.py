import tempfile
import unittest
from pathlib import Path

from main import describe_byte, read_prefix


class TestFileBytesHidden(unittest.TestCase):
    def test_invalid_byte_is_rejected(self):
        for value in (-1, 256):
            with self.assertRaises(ValueError):
                describe_byte(value)

    def test_zero_length_prefix(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.bin"
            path.write_bytes(b"abc")
            self.assertEqual(read_prefix(path, 0), b"")

    def test_negative_length_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.bin"
            path.write_bytes(b"abc")
            with self.assertRaises(ValueError):
                read_prefix(path, -1)


if __name__ == "__main__":
    unittest.main()
