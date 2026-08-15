import unittest
from main import add_vectors,combine_embeddings,causal_mask,context_windows
class TestSequencePositions(unittest.TestCase):
 def test_add_vectors(self): self.assertEqual(add_vectors([1,2],[3,4]),[4,6])
 def test_combine_embeddings(self): self.assertEqual(combine_embeddings([[1,0],[0,1]],[[0.1,0.2],[0.3,0.4]]),[[1.1,0.2],[0.3,1.4]])
 def test_causal_mask(self): self.assertEqual(causal_mask(3),[[True,False,False],[True,True,False],[True,True,True]])
 def test_context_windows(self): self.assertEqual(context_windows(b"ABCD",2)[3],(b"BC",ord("D")))
