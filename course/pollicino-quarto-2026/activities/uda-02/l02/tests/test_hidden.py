import unittest,main
class TestHuffmanHidden(unittest.TestCase):
 def test_all_symbols(self):
  d=bytes(range(256))*2; l=main.huffman_code_lengths(d); c=main.canonical_codes(l); p,n=main.encode_payload(d,c); self.assertEqual(main.decode_payload(p,n,c),d)
 def test_deterministic(self): self.assertEqual(main.huffman_code_lengths(b"ABCD"*20),main.huffman_code_lengths(b"ABCD"*20))
 def test_bits(self):
  d=b"AAAAABBBBCCCDDE"; l=main.huffman_code_lengths(d); c=main.canonical_codes(l); _,n=main.encode_payload(d,c); self.assertEqual(n,main.payload_bits(d,l))
 def test_invalid_length(self):
  with self.assertRaises(ValueError): main.decode_payload(b"\x00",9,{65:(0,1)})
 def test_header_cost(self): self.assertGreater(main.estimated_codebook_bits(main.huffman_code_lengths(bytes(range(64)))),0)
if __name__=="__main__":unittest.main()
