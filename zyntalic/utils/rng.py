# zyntalic/utils/rng.py
import random
import hashlib

def get_rng(seed_input: str) -> random.Random:
    """
    Returns a seeded Random object based on the input string.
    Input: "Love" -> Always returns the same Random object.
    Input: "War"  -> Always returns a different Random object.
    """
    if seed_input is None:
        seed_input = "default_seed"
        
    # Create a stable hash of the input string
    hash_obj = hashlib.sha256(str(seed_input).encode("utf-8"))
    hex_dig = hash_obj.hexdigest()
    
    # Take the first 8 characters and turn them into an integer
    seed_int = int(hex_dig[:8], 16)
    
    # Return a dedicated Random instance (does not affect global random)
    return random.Random(seed_int)