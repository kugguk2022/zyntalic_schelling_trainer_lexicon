# -*- coding: utf-8 -*-
import re, random
from typing import List, Dict, Tuple

try:
    from zyntalic_core import (
        base_embedding, anchor_weights_for_vec,
        generate_word, make_context, CHOSEONG, plain_sentence_anchored
    )
    from zyntalic_core import _choose_motif, TEMPLATES
except Exception:
    # Fallback stubs if zyntalic_core is unavailable
    import hashlib
    CHOSEONG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
    def _rng_from(s):
        h = int(hashlib.blake2b(s.encode('utf-8'), digest_size=8).hexdigest(), 16)
        r = random.Random(h); return r
    def base_embedding(s: str, dim: int = 300):
        r = _rng_from(s); return [r.random() for _ in range(dim)]
    def anchor_weights_for_vec(v, top_k=3):
        names = ["Homer_Iliad","Homer_Odyssey","Plato_Rep","Shakespeare","Dante","Darwin"]
        weights = [random.random() for _ in names]
        s = sum(weights) or 1.0
        pairs = list(zip(names, [w/s for w in weights]))
        pairs.sort(key=lambda x: x[1], reverse=True)
        return pairs[:top_k]
    def generate_word():
        return "".join(random.choice(CHOSEONG) for _ in range(3))
    def make_context(lemma, anchors, pos_hint):
        labs = ";".join(anchors)
        return f"⟦ctx: lemma={lemma}; pos≈{pos_hint}; anchors={labs}⟧"
    def plain_sentence_anchored(anchors, weights):
        return "A silent lattice balances itself."
    def _choose_motif(anchors, weights):
        A = anchors[0] if anchors else "order"
        B = anchors[1] if len(anchors) > 1 else "chaos"
        return A, B
    TEMPLATES = [
        "To {A} through {B}; to {B} through {A}.",
        "{A} begets {B}, and {B} reframes {A}.",
    ]

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

class ZyntalicTranslator:
    def __init__(self, mirror_rate: float = 0.8):
        self.mirror_rate = mirror_rate
        self.lex_map: Dict[str, str] = {}

    def _tokenize_words(self, s: str) -> List[str]:
        return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", s)

    def _pos_hint_for_word(self, zword: str) -> str:
        return "noun" if any(ch in zword for ch in CHOSEONG) else "verb"

    def map_token(self, tok: str) -> str:
        key = tok.lower()
        if key in self.lex_map:
            return self.lex_map[key]
        z = generate_word()
        self.lex_map[key] = z
        return z

    def sentence_to_anchors(self, sent: str, top_k: int = 3) -> List[Tuple[str, float]]:
        v = base_embedding(sent, dim=300)
        return anchor_weights_for_vec(v, top_k=top_k)

    def _mirrored_line(self, anchor_names: List[str], weights: List[float]) -> str:
        A, B = _choose_motif(anchor_names, weights)
        t = random.choice(TEMPLATES)
        return t.format(A=A, B=B)

    def _plain_line(self, anchor_names: List[str], weights: List[float]) -> str:
        return plain_sentence_anchored(anchor_names, weights)

    def translate_sentence(self, sent: str) -> Dict:
        # 1) anchors
        aw = self.sentence_to_anchors(sent, top_k=3)
        anchor_names = [a for a,_ in aw]
        weights     = [w for _, w in aw]

        # 2) content-word mapping
        toks = self._tokenize_words(sent)
        z_words = [self.map_token(t) for t in toks]
        z_surface = " ".join(z_words) if z_words else self._plain_line(anchor_names, weights)

        # 3) mirrored vs plain insert
        if random.random() < self.mirror_rate:
            core_line = self._mirrored_line(anchor_names, weights)
        else:
            core_line = self._plain_line(anchor_names, weights)

        # 4) context
        lemma = z_words[0] if z_words else "ø"
        pos_hint = self._pos_hint_for_word(lemma)
        ctx = make_context(lemma, anchor_names, pos_hint)

        out_sent = f"{z_surface}. {core_line} {ctx}"
        return {"source": sent.strip(), "target": out_sent, "anchors": aw}

    def translate_text(self, text: str) -> List[Dict]:
        parts = [p.strip() for p in _SENT_SPLIT.split(text) if p and p.strip()]
        return [self.translate_sentence(p) for p in parts]
