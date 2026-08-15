import tempfile
import unittest
from pathlib import Path

from main import describe_byte, read_prefix


class TestFileBytes(unittest.TestCase):
    def test_describe_byte(self):
        self.assertEqual(
            describe_byte(65),
            {"decimal": 65, "binary": "01000001", "hex": "41"},
        )

    def test_boundary_bytes(self):
        self.assertEqual(describe_byte(0)["hex"], "00")
        self.assertEqual(describe_byte(255)["binary"], "11111111")

    def test_read_prefix(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.bin"
            path.write_bytes(b"POLLICINO")
            self.assertEqual(read_prefix(path, 4), b"POLL")


if __name__ == "__main__":
    unittest.main()
