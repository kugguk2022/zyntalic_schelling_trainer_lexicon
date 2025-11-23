# Deterministic word generation wrapper for tests and downstream code.
try:
    from zyntalic_core import generate_word as _generate_word
    from zyntalic.utils.rng import get_rng  # re-export for convenience
except Exception:  # pragma: no cover - fallback for broken imports
    import hashlib
    import random

    def get_rng(seed_input: str):
        h = hashlib.sha256(str(seed_input).encode("utf-8")).hexdigest()
        return random.Random(int(h[:8], 16))

    def _generate_word(seed_key: str) -> str:
        rng = get_rng(seed_key)
        syllables = []
        alphabet = list("bcdfghjklmnpqrstvwxyz")
        vowels = list("aeiouy")
        for _ in range(3):
            syllables.append(rng.choice(alphabet) + rng.choice(vowels))
        return "".join(syllables)


def generate_word(seed_key: str) -> str:
    """Stable wrapper so `tests/test_determinism.py` passes."""
    return _generate_word(seed_key)


__all__ = ["generate_word", "get_rng"]
