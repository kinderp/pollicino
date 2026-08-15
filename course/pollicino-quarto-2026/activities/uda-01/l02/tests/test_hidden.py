import unittest

from main import find_collision, truncated_hash_int


class TestHashesHidden(unittest.TestCase):
    def test_pigeonhole_collision_for_eight_bits(self):
        # 257 distinct inputs mapped to 256 outputs must collide.
        collision = find_collision(8, 257)
        self.assertIsNotNone(collision)
        left, right, digest = collision
        self.assertNotEqual(left, right)
        self.assertEqual(truncated_hash_int(left, 8), digest)
        self.assertEqual(truncated_hash_int(right, 8), digest)

    def test_one_bit_hash_collides_very_quickly(self):
        self.assertIsNotNone(find_collision(1, 3))


if __name__ == "__main__":
    unittest.main()
