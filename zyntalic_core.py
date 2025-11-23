# -*- coding: utf-8 -*-
"""
Zyntalic Core (Schelling-anchored, Lexicon-aware)
- Fully deterministic via zyntalic.utils.rng.get_rng
- Features: Hangul+Polish tokens, Mirrored meanings, Context Blocks, Lexicon Priors
"""

import os
import json
import math
from typing import List, Dict, Optional, Tuple

# --- 1. THE GOLDEN KEY: Import the Deterministic RNG Tool ---
try:
    from zyntalic.utils.rng import get_rng
except ImportError:
    # Fallback if utils structure isn't set up yet
    import random
    import hashlib
    def get_rng(seed: str):
        h = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()
        return random.Random(int(h[:8], 16))

# Optional dependencies
try:
    import numpy as np
except Exception:
    np = None
try:
    from zyntalic_embeddings import embed_text
except Exception:
    embed_text = None
# -------------------- Alphabet --------------------
CHOSEONG = ["ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ","ㅆ","ㅇ","ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]
JUNGSEONG = ["ㅏ","ㅐ","ㅑ","ㅒ","ㅓ","ㅔ","ㅕ","ㅖ","ㅗ","ㅘ","ㅙ","ㅚ","ㅛ","ㅜ","ㅝ","ㅞ","ㅟ","ㅠ","ㅡ","ㅢ","ㅣ"]
JONGSEONG = ["","ㄱ","ㄲ","ㄳ","ㄴ","ㄵ","ㄶ","ㄷ","ㄹ","ㄺ","ㄻ","ㄼ","ㄽ","ㄾ","ㄿ","ㅀ","ㅁ","ㅂ","ㅄ","ㅅ","ㅆ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]

POLISH_CONSONANTS = "bcćdđfghjklłmnńprsśtvwzźż"
POLISH_VOWELS     = "aąeęioóuy"

# -------------------- Anchors --------------------
ANCHORS = [
    "Homer_Iliad", "Homer_Odyssey", "Plato_Republic", "Aristotle_Organon", 
    "Virgil_Aeneid", "Dante_DivineComedy", "Shakespeare_Sonnets", "Goethe_Faust", 
    "Cervantes_DonQuixote", "Milton_ParadiseLost", "Melville_MobyDick", 
    "Darwin_OriginOfSpecies", "Austen_PridePrejudice", "Tolstoy_WarPeace", 
    "Dostoevsky_BrothersKaramazov", "Laozi_TaoTeChing", "Sunzi_ArtOfWar", 
    "Descartes_Meditations", "Bacon_NovumOrganum", "Spinoza_Ethics"
]

# -------------------- Lexicon Prior --------------------
_LEXICON_CACHE: Optional[Dict[str, dict]] = None

def load_lexicons(dirpath: str = "lexicon") -> Dict[str, dict]:
    """Load anchor lexicons if present."""
    global _LEXICON_CACHE
    if _LEXICON_CACHE is not None:
        return _LEXICON_CACHE
    data: Dict[str, dict] = {}
    if not os.path.isdir(dirpath):
        _LEXICON_CACHE = {}
        return _LEXICON_CACHE
    for fn in os.listdir(dirpath):
        if not fn.endswith(".json"): 
            continue
        try:
            with open(os.path.join(dirpath, fn), "r", encoding="utf-8") as f:
                obj = json.load(f)
            key = fn[:-5]
            data[key] = obj
        except Exception:
            continue
    _LEXICON_CACHE = data
    return _LEXICON_CACHE

def _weighted_sample(rng, pool, weights):
    """Deterministic weighted sample using passed RNG."""
    if not pool:
        return None
    total = sum(weights)
    r = rng.random() * total
    acc = 0.0
    for item, w in zip(pool, weights):
        acc += w
        if r <= acc:
            return item
    return pool[-1]

def _mix_lists(anchors, weights, field, base_list, k_sharpen=1.0):
    """Mix lexicon lists based on anchor weights."""
    L = load_lexicons()
    pool, wts = [], []
    for a, w in zip(anchors, weights):
        if a in L and field in L[a]:
            for tok in L[a][field]:
                pool.append(tok)
                wts.append(max(1e-6, w**k_sharpen))
    # smooth with base list
    for tok in base_list:
        pool.append(tok)
        wts.append(0.2)
    return pool, wts

def _choose_motif(rng, anchors, weights):
    """Deterministic motif selection."""
    L = load_lexicons()
    motif_pool, motif_w = [], []
    for a, w in zip(anchors, weights):
        if a in L and "motifs" in L[a]:
            for pair in L[a]["motifs"]:
                if isinstance(pair, list) and len(pair) == 2:
                    motif_pool.append(tuple(pair))
                    motif_w.append(max(1e-6, w))
    if motif_pool:
        return _weighted_sample(rng, motif_pool, motif_w)
    # fallback generic motifs
    defaults = [
        ("light","dark"), ("order","chaos"), ("silence","noise"),
        ("rise","fall"), ("future","past"), ("open","closed"),
        ("presence","absence"), ("truth","doubt")
    ]
    return defaults[int(rng.random() * len(defaults))]

# -------------------- Helpers --------------------
def compose_hangul_block(ch: str, ju: str, jo: str) -> str:
    LCount, VCount, TCount = 19, 21, 28
    SBase = 0xAC00
    try:
        L = CHOSEONG.index(ch)
        V = JUNGSEONG.index(ju)
        T = JONGSEONG.index(jo)
    except ValueError:
        return ch + ju + jo
    SIndex = (L * VCount + V) * TCount + T
    return chr(SBase + SIndex)

def swap_vowel(v: str) -> str:
    return "ㅑ" if v == "ㅏ" else v

def fuse_syllables(root: str, marker: str) -> str:
    return root + marker

def lemmatize(word: str) -> str:
    suffixes = ["ㅆ","었","ś","ął","ㅇ","ł"]
    for s in suffixes:
        if word.endswith(s):
            return word[:-len(s)]
    return word

def _dot(a, b): 
    return sum(x*y for x,y in zip(a,b))

def _l2(a): 
    return (sum(x*x for x in a))**0.5

def _normalize(v):
    n = _l2(v) or 1.0
    return [x/n for x in v]

def _mix(vecs, weights):
    out = [0.0]*len(vecs[0])
    for w, v in zip(weights, vecs):
        for i, x in enumerate(v):
            out[i] += w*x
    return out

# -------------------- Deterministic Syllables --------------------
def create_hangul_syllable(rng) -> str:
    ch = rng.choice(CHOSEONG)
    ju = swap_vowel(rng.choice(JUNGSEONG)) if rng.random() < 0.25 else rng.choice(JUNGSEONG)
    jo = rng.choice(JONGSEONG)
    return compose_hangul_block(ch, ju, jo)

def create_latin_syllable(rng) -> str:
    c = rng.choice(POLISH_CONSONANTS)
    v = rng.choice(POLISH_VOWELS)
    tail = rng.choice(["", rng.choice(POLISH_CONSONANTS)])
    return c+v+tail

def create_syllable(rng, pos="noun") -> str:
    r = rng.random()
    if pos == "noun":
        return create_hangul_syllable(rng) if r < 0.85 else create_latin_syllable(rng)
    if pos == "verb":
        return create_latin_syllable(rng) if r < 0.85 else create_hangul_syllable(rng)
    return create_hangul_syllable(rng) if r < 0.5 else create_latin_syllable(rng)

def generate_word(seed_key: str) -> str:
    """Generate Zyntalic word deterministically from a seed string."""
    rng = get_rng(seed_key)
    sylls = [
        create_syllable(rng, pos=rng.choice(["noun","verb"])),
        create_syllable(rng, pos=rng.choice(["noun","verb"])),
        create_syllable(rng, pos=rng.choice(["noun","verb"]))
    ]
    if rng.random() < 0.3:
        sylls[1] = fuse_syllables(sylls[1], rng.choice(["ł","ㅆ","ś","ㅇ"]))
    return "".join(sylls)

# -------------------- Sentence Templates --------------------
TEMPLATES = [
    "To {A} through {B}; to {B} through {A}.",
    "{A} begets {B}, and {B} reframes {A}.",
    "Seek {A} by {B}; keep {B} by {A}.",
    "Between {A} and {B}, the path mirrors back from {B} to {A}."
]

def mirrored_sentence_anchored(rng, anchors, weights) -> str:
    """Chiasmus style."""
    A, B = _choose_motif(rng, anchors, weights)
    t = rng.choice(TEMPLATES)
    return t.format(A=A, B=B)

def plain_sentence_anchored(rng, anchors, weights) -> str:
    """Standard style using Lexicon Lists."""
    base_adj = ["bright","mysterious","ancient","vivid","whimsical"]
    base_noun= ["journey","whisper","echo","saga","pattern"]
    base_verb= ["weaves","reveals","hides","balances"]
    
    pool_adj, w_adj = _mix_lists(anchors, weights, 'adjectives', base_adj)
    pool_noun, w_noun= _mix_lists(anchors, weights, 'nouns', base_noun)
    pool_verb, w_verb= _mix_lists(anchors, weights, 'verbs', base_verb)
    
    adj = _weighted_sample(rng, pool_adj, w_adj) or rng.choice(base_adj)
    noun= _weighted_sample(rng, pool_noun, w_noun) or rng.choice(base_noun)
    verb = _weighted_sample(rng, pool_verb, w_verb) or rng.choice(base_verb)
    
    return f"A {adj} {noun} {verb} itself."

# -------------------- Context Block --------------------
def make_context(word: str, chosen_anchors: List[str], pos_hint: str) -> str:
    lemma = lemmatize(word)
    ctx_anchors = "|".join(chosen_anchors)
    return f"⟦ctx: lemma={lemma}; pos≈{pos_hint}; anchors={ctx_anchors}⟧"

# -------------------- Embeddings --------------------
def base_embedding(key: str, dim: int = 300):
    if embed_text is not None:
        return embed_text(key, dim=dim)
    rng = get_rng(f"embed::{key}")
    return [rng.random() for _ in range(dim)]

def _build_anchor_vecs(dim: int = 300) -> Dict[str, List[float]]:
    vecs = {}
    for name in ANCHORS:
        label = name.replace("_", " ")
        vecs[name] = _normalize(base_embedding(label, dim))
    return vecs

ANCHOR_VECS = _build_anchor_vecs()

def anchor_weights_for_vec(vec: List[float], top_k: int = 3):
    v = _normalize(vec)
    scores = []
    for a, av in ANCHOR_VECS.items():
        scores.append((a, _dot(v, _normalize(av))))
    scores.sort(key=lambda x: x[1], reverse=True)
    top = scores[:top_k]
    m = max(s for _,s in top) if top else 0.0
    exps = [math.exp(s - m) for _,s in top]
    Z = sum(exps) or 1.0
    weights = [e/Z for e in exps]
    return [(name, w) for (name,_), w in zip(top, weights)]

def load_projection(path: str = "models/W.npy"):
    if np is None: 
        return None
    if not os.path.exists(path): 
        return None
    try:
        return np.load(path)
    except Exception:
        return None

def apply_projection(vec: List[float], W) -> List[float]:
    if np is None or W is None: 
        return vec
    v = np.asarray(vec).reshape(1,-1) @ W
    v = v.flatten().tolist()
    return _normalize(v)

def generate_embedding(seed_key: str, dim: int = 300, W=None):
    vb = base_embedding(seed_key, dim)
    canon = apply_projection(vb, W)
    if canon == vb and W is None:
        # no projection: softly mix with anchors
        aw0 = anchor_weights_for_vec(vb, top_k=3)
        vecs = [vb] + [ANCHOR_VECS[a] for a,_ in aw0]
        ws   = [0.5] + [0.5*w for _,w in aw0]
        canon = _normalize(_mix(vecs, ws))
    aw = anchor_weights_for_vec(canon, top_k=3)
    return canon, aw

# -------------------- Public API --------------------
def generate_entry(seed_word: str, mirror_rate: float = 0.8, W=None) -> Dict:
    """
    Generate a full dictionary entry deterministically.
    seed_word: The English input (e.g., 'Love') which seeds ALL randomness.
    """
    rng = get_rng(seed_word)
    
    # 1. Zyntalic Token (deterministic)
    w = generate_word(seed_word)
    pos_hint = "noun" if any(c in w for c in CHOSEONG) else "verb"
    
    # 2. Embedding & Anchors (seeded by the same key)
    emb, aw = generate_embedding(seed_word, W=W)
    chosen = [name for name,_ in aw]
    weights = [wgt for _, wgt in aw]
    
    # 3. Sentence
    if rng.random() < mirror_rate:
        sent_core = mirrored_sentence_anchored(rng, chosen, weights)
    else:
        sent_core = plain_sentence_anchored(rng, chosen, weights)
    
    # 4. Context
    sentence = f"{sent_core} {make_context(w, chosen, pos_hint)}"
    
    return {
        "word": w, 
        "meaning": sent_core, 
        "sentence": sentence, 
        "anchors": aw, 
        "embedding": emb
    }

def export_to_txt(entries, filename="zyntalic_words.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        for e in entries:
            anchors_str = ";".join(f"{a}:{w:.3f}" for a,w in e["anchors"])
            emb_str = ",".join(f"{v:.6f}" for v in e["embedding"])
            f.write(f"{e['word']}\t{e['meaning']}\t{e['sentence']}\t{anchors_str}\t{emb_str}\n")

def generate_words(
    n: int = 1000, 
    use_projection: bool = True, 
    root_seed: str = "zyntalic_default"
):
    """
    Deterministic bulk generator.
    - Same (n, use_projection, root_seed) -> same wordlist every run.
    - Different root_seed -> different stable lexicon.
    """
    W = load_projection("models/W.npy") if use_projection else None
    out = []
    seen = set()
    i = 0
    while len(out) < n:
        seed = f"{root_seed}:{i}"
        e = generate_entry(seed, W=W)
        if e["word"] not in seen:
            seen.add(e["word"])
            out.append(e)
        i += 1
        if i > n * 10:  # safety
            break
    return out

def generate_words_demo(n=10):
    """Generate n sample words using integer seeds for consistency."""
    results = []
    W = load_projection()
    for i in range(n):
        seed = f"concept_{i}" 
        results.append(generate_entry(seed, W=W))
    return results

if __name__ == "__main__":
    print("--- Zyntalic Deterministic Core Test ---")
    
    e1 = generate_entry("Love")
    e2 = generate_entry("Love")
    e3 = generate_entry("War")
    
    print(f"Input 'Love' -> {e1['word']} | {e1['meaning']}")
    print(f"Input 'Love' -> {e2['word']} | {e2['meaning']}")
    print(f"Input 'War'  -> {e3['word']} | {e3['meaning']}")
    
    assert e1['word'] == e2['word'], "CRITICAL FAIL: Non-deterministic output!"
    print("\nSUCCESS: Output is deterministic.")
    
    print("\nGenerating demo lexicon...")
    entries = generate_words(n=20, use_projection=True, root_seed="demo_seed")
    export_to_txt(entries, "zyntalic_words_demo.txt")
    print("Wrote zyntalic_words_demo.txt")
