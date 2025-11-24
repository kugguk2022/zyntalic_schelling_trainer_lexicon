# zyntalic/protocol.py

import hashlib
from typing import Literal
from zyntalic_core import generate_entry  # your deterministic core

Mode = Literal["hash", "vq"]

def _hash_seed(text: str, anchor: str) -> str:
    h = hashlib.sha256(f"{anchor}::{text}".encode("utf-8")).hexdigest()
    return h  # we can just use hex as seed_key

def _vq_seed_stub(text: str, anchor: str) -> str:
    """
    Placeholder for future VQ.
    Currently just buckets the hash into a small number of clusters.
    Later: replace with real embedding + codebook.
    """
    h = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
    cluster_id = h % 4096  # fake codebook size
    return f"{anchor}::cluster-{cluster_id}"

def semantic_seed(text: str, anchor: str, mode: Mode = "hash") -> str:
    if mode == "hash":
        return _hash_seed(text, anchor)
    elif mode == "vq":
        return _vq_seed_stub(text, anchor)
    else:
        raise ValueError(f"Unknown mode {mode}")

def encode_to_zyntalic(
    text: str,
    anchor: str = "Homer_Iliad",
    mode: Mode = "hash",
    mirror_rate: float = 0.8,
    W=None
):
    seed_key = semantic_seed(text, anchor, mode=mode)
    entry = generate_entry(seed_key, mirror_rate=mirror_rate, W=W)
    entry["source_text"] = text
    entry["anchor_used"] = anchor
    entry["mode"] = mode
    return entry
