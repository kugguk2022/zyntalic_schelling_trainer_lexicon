import unittest
from zyntalic.utils.rng import get_rng
from zyntalic.generator.core import generate_word

class TestDeterminism(unittest.TestCase):
    def test_rng_stability(self):
        """Test that the RNG utility is actually stable."""
        rng1 = get_rng("apple")
        rng2 = get_rng("apple")
        rng3 = get_rng("banana")
        
        # Apple should equal Apple
        self.assertEqual(rng1.random(), rng2.random())
        # Apple should NOT equal Banana
        self.assertNotEqual(rng1.random(), rng3.random())

    def test_word_generation(self):
        """Test that the generator produces identical words for identical inputs."""
        word1 = generate_word("freedom")
        word2 = generate_word("freedom")
        
        print(f"Run 1: {word1}")
        print(f"Run 2: {word2}")
        
        self.assertEqual(word1, word2)

if __name__ == '__main__':
    unittest.main()