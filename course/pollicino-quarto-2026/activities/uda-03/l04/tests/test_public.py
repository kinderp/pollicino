import unittest
from main import init_embedding, lookup, lookup_sequence, parameter_count

class TestEmbeddingPublic(unittest.TestCase):
    def test_shape_and_parameter_count(self):
        table=init_embedding(256,4,seed=7)
        self.assertEqual(len(table),256); self.assertEqual(len(table[0]),4)
        self.assertEqual(parameter_count(table),1024)

    def test_seed_is_reproducible(self):
        self.assertEqual(init_embedding(8,3,seed=2), init_embedding(8,3,seed=2))

    def test_lookup_sequence(self):
        table=init_embedding(256,2,seed=1)
        self.assertEqual(lookup_sequence(table,b'AB'), [lookup(table,65),lookup(table,66)])

if __name__ == '__main__': unittest.main()
