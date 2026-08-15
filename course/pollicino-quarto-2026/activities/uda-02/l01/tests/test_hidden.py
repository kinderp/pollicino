import unittest
import main

class TestRLEHidden(unittest.TestCase):
    def test_all_byte_values_roundtrip(self):
        data=bytes(range(256)); self.assertEqual(main.rle_decode(main.rle_encode(data)),data)
    def test_odd_stream_is_invalid(self):
        with self.assertRaises(ValueError): main.rle_decode(b"\x03A\x02")
    def test_zero_count_is_invalid(self):
        with self.assertRaises(ValueError): main.rle_decode(b"\x00A")
    def test_empty_ratio(self): self.assertEqual(main.compression_ratio(b"",b""),1.0)
    def test_rle_can_expand_data(self):
        data=bytes(range(100)); self.assertGreater(len(main.rle_encode(data)),len(data))

if __name__=="__main__": unittest.main()
