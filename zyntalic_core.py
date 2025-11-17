# -*- coding: utf-8 -*-
"""
Zyntalic Core (Schelling-anchored, Lexicon-aware)
- Hangul+Polish tokens
- Mirrored meanings
- Context at sentence END
- Anchor-aware embeddings (optional learned projection W)
- Lexicon prior: anchor-weighted word choice + motifs
"""
import hashlib, random, os, json
from typing import List, Tuple, Dict, Optional

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

def compose_hangul_block(ch: str, ju: str, jo: str) -> str:
    """
    Compose a Hangul syllable block from choseong, jungseong, and jongseong.
    
    Args:
        ch: Choseong (initial consonant)
        ju: Jungseong (vowel)
        jo: Jongseong (final consonant)
        
    Returns:
        Composed Hangul syllable or concatenated string if composition fails
    """
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
    """Swap vowel for stylistic variation."""
    return "ㅑ" if v == "ㅏ" else v


def fuse_syllables(root: str, marker: str) -> str:
    """Fuse syllables with marker for morphological variation."""
    return root + marker


def lemmatize(word: str) -> str:
    """
    Remove common suffixes to extract lemma.
    
    Args:
        word: Zyntalic word to lemmatize
        
    Returns:
        Base form of the word
    """
    suffixes = ["ㅆ","었","ś","ął","ㅇ","ł"]
    for s in suffixes:
        if word.endswith(s):
            return word[:-len(s)]
    return word

# -------------------- Anchors --------------------
ANCHORS = [
    "Homer_Iliad", "Homer_Odyssey", "Plato_Republic",
    "Aristotle_Organon", "Virgil_Aeneid", "Dante_DivineComedy",
    "Shakespeare_Sonnets", "Goethe_Faust", "Cervantes_DonQuixote",
    "Milton_ParadiseLost", "Melville_MobyDick", "Darwin_OriginOfSpecies",
    "Austen_PridePrejudice", "Tolstoy_WarPeace", "Dostoevsky_BrothersKaramazov",
    "Laozi_TaoTeChing", "Sunzi_ArtOfWar", "Descartes_Meditations",
    "Bacon_NovumOrganum", "Spinoza_Ethics"
]

def _det_seed(text: str) -> int:
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def _det_vec(tag: str, dim: int = 300):
    rng = random.Random(_det_seed(tag))
    return [rng.random() for _ in range(dim)]

ANCHOR_VECS = {a: _det_vec(a) for a in ANCHORS}

def _dot(a, b): return sum(x*y for x,y in zip(a,b))
def _l2(a): return (sum(x*x for x in a))**0.5
def _normalize(v):
    n = _l2(v) or 1.0
    return [x/n for x in v]

def _mix(vecs, weights):
    out = [0.0]*len(vecs[0])
    for w, v in zip(weights, vecs):
        for i, x in enumerate(v):
            out[i] += w*x
    return out

# -------------------- Lexicon Prior --------------------
_LEXICON_CACHE = None

def load_lexicons(dirpath: str = "lexicon"):
    """Load anchor lexicons if present. Returns dict[anchor] -> {adjectives, nouns, verbs, motifs}"""
    global _LEXICON_CACHE
    if _LEXICON_CACHE is not None:
        return _LEXICON_CACHE
    data = {}
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

def _weighted_sample(pool, weights):
    import random
    if not pool:
        return None
    r = random.random() * sum(weights)
    acc = 0.0
    for item, w in zip(pool, weights):
        acc += w
        if r <= acc:
            return item
    return pool[-1]

def _mix_lists(anchors, weights, field, base_list, k_sharpen=1.0):
    """Create a weighted sampler list for a given lexical field ('adjectives'|'nouns'|'verbs')."""
    L = load_lexicons()
    pool, wts = [], []
    for a, w in zip(anchors, weights):
        if a in L and field in L[a]:
            for tok in L[a][field]:
                pool.append(tok)
                wts.append(max(1e-6, w**k_sharpen))
    for tok in base_list:
        pool.append(tok); wts.append(0.2)  # smoothing
    return pool, wts

def _choose_motif(anchors, weights):
    L = load_lexicons()
    motif_pool, motif_w = [], []
    for a, w in zip(anchors, weights):
        if a in L and "motifs" in L[a]:
            for pair in L[a]["motifs"]:
                if isinstance(pair, list) and len(pair) == 2:
                    motif_pool.append(tuple(pair)); motif_w.append(max(1e-6, w))
    if motif_pool:
        return _weighted_sample(motif_pool, motif_w)
    # fallback generic
    return random.choice([
        ("light","dark"), ("order","chaos"), ("silence","noise"),
        ("rise","fall"), ("future","past"), ("open","closed"),
        ("presence","absence"), ("truth","doubt"), ("dream","waking"),
        ("center","edge"), ("stillness","motion")
    ])

# -------------------- Syllables & Words --------------------
def create_hangul_syllable() -> str:
    ch = random.choice(CHOSEONG)
    ju = swap_vowel(random.choice(JUNGSEONG)) if random.random() < 0.25 else random.choice(JUNGSEONG)
    jo = random.choice(JONGSEONG)
    return compose_hangul_block(ch, ju, jo)

def create_latin_syllable() -> str:
    c = random.choice(POLISH_CONSONANTS)
    v = random.choice(POLISH_VOWELS)
    tail = random.choice(["", random.choice(POLISH_CONSONANTS)])
    return c+v+tail

def create_syllable(pos="noun") -> str:
    r = random.random()
    if pos == "noun":
        return create_hangul_syllable() if r < 0.85 else create_latin_syllable()
    if pos == "verb":
        return create_latin_syllable() if r < 0.85 else create_hangul_syllable()
    return create_hangul_syllable() if r < 0.5 else create_latin_syllable()

def generate_word() -> str:
    sylls = [
        create_syllable(pos=random.choice(["noun","verb"])),
        create_syllable(pos=random.choice(["noun","verb"])),
        create_syllable(pos=random.choice(["noun","verb"]))
    ]
    if random.random() < 0.3:
        sylls[1] = fuse_syllables(sylls[1], random.choice(["ł","ㅆ","ś","ㅇ"]))
    return "".join(sylls)

# -------------------- Sentence templates --------------------
TEMPLATES = [
    "To {A} through {B}; to {B} through {A}.",
    "{A} begets {B}, and {B} reframes {A}.",
    "Seek {A} by {B}; keep {B} by {A}.",
    "Between {A} and {B}, the path mirrors back from {B} to {A}."
]

def mirrored_sentence_anchored(anchors, weights) -> str:
    A,B = _choose_motif(anchors, weights)
    t = random.choice(TEMPLATES)
    return t.format(A=A, B=B)

def plain_sentence_anchored(anchors, weights) -> str:
    base_adj = ["bright","mysterious","ancient","vivid","whimsical","silent","resolute"]
    base_noun= ["journey","whisper","echo","saga","pattern","interval","lattice"]
    base_verb= ["weaves","reveals","hides","balances","translates"]
    pool_adj, w_adj = _mix_lists(anchors, weights, 'adjectives', base_adj, k_sharpen=1.0)
    pool_noun,w_noun= _mix_lists(anchors, weights, 'nouns',      base_noun, k_sharpen=1.0)
    pool_verb,w_verb= _mix_lists(anchors, weights, 'verbs',      base_verb, k_sharpen=1.0)
    adj = _weighted_sample(pool_adj, w_adj) or random.choice(base_adj)
    noun= _weighted_sample(pool_noun, w_noun) or random.choice(base_noun)
    verb= _weighted_sample(pool_verb, w_verb) or random.choice(base_verb)
    return f"A {adj} {noun} {verb} itself."

# -------------------- Context block --------------------
def make_context(word: str, chosen_anchors: List[str], pos_hint: str) -> str:
    lemma = lemmatize(word)
    ctx_anchors = "|".join(chosen_anchors)
    return f"⟦ctx: lemma={lemma}; pos≈{pos_hint}; anchors={ctx_anchors}⟧"

# -------------------- Embeddings & Projection -------------
def base_embedding(key: str, dim: int = 300):
    rng = random.Random(_det_seed(key))
    return [rng.random() for _ in range(dim)]

def anchor_weights_for_vec(vec: List[float], top_k: int = 3):
    v = _normalize(vec)
    scores = []
    for a, av in ANCHOR_VECS.items():
        scores.append((a, _dot(v, _normalize(av))))
    scores.sort(key=lambda x: x[1], reverse=True)
    top = scores[:top_k]
    import math
    m = max(s for _,s in top) if top else 0.0
    exps = [math.exp(s - m) for _,s in top]
    Z = sum(exps) or 1.0
    weights = [e/Z for e in exps]
    return [(name, w) for (name,_), w in zip(top, weights)]

def load_projection(path: str = "models/W.npy"):
    if np is None: return None
    if not os.path.exists(path): return None
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

def generate_embedding(word: str, dim: int = 300, W=None):
    vb = base_embedding(word, dim)
    canon = apply_projection(vb, W)
    if canon == vb:  # no projection available
        aw0 = anchor_weights_for_vec(vb, top_k=3)
        vecs = [vb] + [ANCHOR_VECS[a] for a,_ in aw0]
        ws   = [0.5] + [0.5*w for _,w in aw0]
        canon = _normalize(_mix(vecs, ws))
    aw = anchor_weights_for_vec(canon, top_k=3)
    return canon, aw

def _det_seed(text: str) -> int:
    import hashlib
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def _det_vec(tag: str, dim: int = 300):
    rng = random.Random(_det_seed(tag))
    return [rng.random() for _ in range(dim)]


def _build_anchor_vecs(dim: int = 300) -> Dict[str, List[float]]:
    """
    Build anchor vectors as true Schelling points:
    - If a real embedder exists, embed the canonical work name.
    - Otherwise, fall back to deterministic RNG.
    """
    vecs: Dict[str, List[float]] = {}
    for name in ANCHORS:
        label_text = name.replace("_", " ")
        if embed_text is not None:
            v = embed_text(label_text, dim=dim)
        else:
            v = _det_vec(name, dim=dim)
        vecs[name] = _normalize(v)
    return vecs


ANCHOR_VECS = _build_anchor_vecs(dim=300)


def base_embedding(key: str, dim: int = 300):
    """
    Base embedding for any key (word, lemma, sentence).
    - Prefer real embeddings from zyntalic_embeddings.embed_text.
    - Fallback: deterministic RNG based on hash.
    """
    if embed_text is not None:
        return embed_text(key, dim=dim)
    rng = random.Random(_det_seed(key))
    return [rng.random() for _ in range(dim)]


# -------------------- Public generation --------------------
def generate_entry(mirror_rate: float = 0.8, W=None) -> Dict:
    w = generate_word()
    pos_hint = "noun" if any(c in w for c in CHOSEONG) else "verb"
    emb, aw = generate_embedding(w, W=W)
    chosen = [name for name,_ in aw]
    weights = [w for _, w in aw]
    if random.random() < mirror_rate:
        sent_core = mirrored_sentence_anchored(chosen, weights)
    else:
        sent_core = plain_sentence_anchored(chosen, weights)
    sentence = f"{sent_core} {make_context(w, chosen, pos_hint)}"
    meaning = f"{sent_core}"
    return {"word":w, "meaning":meaning, "sentence":sentence, "anchors":aw, "embedding":emb}

def export_to_txt(entries, filename="zyntalic_words.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        for e in entries:
            anchors_str = ";".join([f"{a}:{w:.3f}" for a,w in e["anchors"]])
            emb_str = ",".join(f"{v:.6f}" for v in e["embedding"])
            f.write(f"{e['word']}\t{e['meaning']}\t{e['sentence']}\t{anchors_str}\t{emb_str}\n")

def generate_words(n=1000, use_projection=True):
    W = load_projection("models/W.npy") if use_projection else None
    seen, out = set(), []
    while len(out) < n:
        e = generate_entry(W=W)
        if e["word"] in seen: 
            continue
        seen.add(e["word"]); out.append(e)
    return out

if __name__ == "__main__":
    print("Generating demo set (n=1000). If models/W.npy exists, it will be used.")
    entries = generate_words(1000, use_projection=True)
    export_to_txt(entries, "zyntalic_words.txt")
    print("Wrote zyntalic_words.txt")
