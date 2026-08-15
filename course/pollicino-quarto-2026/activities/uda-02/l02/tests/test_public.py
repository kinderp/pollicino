import unittest,main
class TestHuffmanPublic(unittest.TestCase):
 def test_empty(self): self.assertEqual(main.huffman_code_lengths(b""),{})
 def test_single(self): self.assertEqual(main.huffman_code_lengths(b"A"*20),{65:1})
 def test_prefix(self): self.assertTrue(main.is_prefix_free(main.canonical_codes(main.huffman_code_lengths(b"AAAABBBCCD"))))
 def test_roundtrip(self):
  d=b"BANANA_BANDANA"; l=main.huffman_code_lengths(d); c=main.canonical_codes(l); p,n=main.encode_payload(d,c); self.assertEqual(main.decode_payload(p,n,c),d)
 def test_common_short(self):
  l=main.huffman_code_lengths(b"A"*100+b"B"*20+b"C"*5); self.assertLessEqual(l[65],l[67])
if __name__=="__main__":unittest.main()
