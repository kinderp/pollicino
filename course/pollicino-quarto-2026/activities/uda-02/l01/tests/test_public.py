import unittest
import main

class TestRLEPublic(unittest.TestCase):
    def test_empty_roundtrip(self): self.assertEqual(main.rle_decode(main.rle_encode(b"")),b"")
    def test_simple_encoding(self): self.assertEqual(main.rle_encode(b"AAABB"),bytes([3,ord("A"),2,ord("B")]))
    def test_roundtrip(self):
        data=b"AAAABBBCCDAAAAAA"; self.assertEqual(main.rle_decode(main.rle_encode(data)),data)
    def test_long_run_is_split(self): self.assertEqual(main.rle_encode(b"Z"*300),bytes([255,ord("Z"),45,ord("Z")]))
    def test_ratio(self):
        data=b"A"*100; self.assertAlmostEqual(main.compression_ratio(data,main.rle_encode(data)),0.02)

if __name__=="__main__": unittest.main()
