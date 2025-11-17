# -*- coding: utf-8 -*-
"""
Embedding backend for Zyntalic.

If sentence-transformers is available, use a real model.
Otherwise, fall back to deterministic hash-based pseudo-embeddings.
"""

from typing import List
import hashlib, random

try:
    from sentence_transformers import SentenceTransformer
    _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    _DIM = _MODEL.get_sentence_embedding_dimension()
except Exception:
    _MODEL = None
    _DIM = 300


def embed_text(text: str, dim: int | None = None) -> List[float]:
    """
    Returns a dense embedding vector for text.

    If a real model is available, use it.
    Otherwise, return a deterministic pseudo-random vector.
    """
    global _DIM
    if dim is None:
        dim = _DIM

    if _MODEL is not None:
        v = _MODEL.encode(text, normalize_embeddings=True)
        v = v.tolist()
        if len(v) > dim:
            return v[:dim]
        if len(v) < dim:
            # pad deterministically
            rnd = random.Random(int(hashlib.sha256(text.encode()).hexdigest(), 16))
            v = v + [rnd.random() for _ in range(dim - len(v))]
        return v

    # Fallback: deterministic RNG
    data = (text or "").encode("utf-8")
    digest = hashlib.blake2b(data, digest_size=16).digest()
    seed = int.from_bytes(digest, "big")
    rng = random.Random(seed)
    return [rng.random() for _ in range(dim)]
