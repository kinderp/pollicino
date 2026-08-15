import unittest
from main import init_embedding, lookup, sgd_update_row

class TestEmbeddingHidden(unittest.TestCase):
    def test_lookup_is_copy(self):
        table=init_embedding(4,2,seed=1); row=lookup(table,0); row[0]=999
        self.assertNotEqual(table[0][0],999)

    def test_update_only_selected_row(self):
        table=init_embedding(4,2,seed=1); before=[r.copy() for r in table]
        sgd_update_row(table,2,[1,-1],0.1)
        self.assertEqual(table[0],before[0]); self.assertNotEqual(table[2],before[2])

    def test_invalid_token(self):
        with self.assertRaises(IndexError): lookup(init_embedding(2,2),2)

if __name__ == '__main__': unittest.main()
