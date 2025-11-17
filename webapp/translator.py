# -*- coding: utf-8 -*-
import re, random
from typing import List, Dict, Tuple

try:
    from zyntalic_core import (
        base_embedding, anchor_weights_for_vec,
        generate_word, make_context, CHOSEONG
    )
except Exception:
    import hashlib, random
    CHOSEONG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
    def _rng_from(s): 
        h = int(hashlib.blake2b(s.encode('utf-8'), digest_size=8).hexdigest(), 16)
        r = random.Random(h); return r
    def base_embedding(s: str, dim: int = 300):
        r = _rng_from(s); return [r.random() for _ in range(dim)]
    def anchor_weights_for_vec(v, top_k=3):
        names = ["Homer_Iliad","Homer_Odyssey","Bible","Plato_Rep","Shakespeare","Dante","Godel","Darwin"]
        weights = [random.random() for _ in names]
        s = sum(weights) or 1.0
        pairs = list(zip(names, [w/s for w in weights]))
        pairs.sort(key=lambda x: x[1], reverse=True)
        return pairs[:top_k]
    def generate_word():
        return "".join(random.choice(CHOSEONG) for _ in range(3))
    def make_context(lemma, anchors, pos_hint):
        labs = ";".join(a for a,_ in anchors)
        return f"⟦ctx: lemma={lemma}; pos≈{pos_hint}; anchors={labs}⟧"

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

    def _mirrored_line(self, anchors, weights) -> str:
        try:
            from zyntalic_core import _choose_motif, TEMPLATES
            A, B = _choose_motif(anchors, weights)
            import random
            t = random.choice(TEMPLATES)
            return t.format(A=A, B=B)
        except Exception:
            A = anchors[0][0] if anchors else "order"
            B = anchors[1][0] if len(anchors) > 1 else "chaos"
            return f"{A} with {B} returns, then retreats."

    def _plain_line(self, anchors, weights) -> str:
        try:
            from zyntalic_core import plain_sentence_anchored
            return plain_sentence_anchored(anchors, weights)
        except Exception:
            return "The path curves gently, and the witness remains."

    def translate_sentence(self, sent: str) -> Dict:
        """
        Translate a single English sentence into Zyntalic.

        New behaviour:
        - Try to parse English into Subject/Object/Verb/Context (S-O-V-C).
        - Apply Hungarian-style plural & French-style tense marking.
        - If anything fails, fall back to plain token mapping.
        """
        sent = (sent or "").strip()
        if not sent:
            return {"source": "", "target": "", "anchors": []}

        # Anchors at sentence level (Schelling points)
        anchors = self.sentence_to_anchors(sent, top_k=3)
        weights = [w for _, w in anchors]

        # 1) Try new syntax-aware pipeline
        z_surface = None
        try:
            from english_parser import parse_sentence
            from zyntalic_syntax import to_zyntalic_order

            parsed = parse_sentence(sent)
            z_surface = to_zyntalic_order(parsed, self.map_token)
        except Exception:
            z_surface = None

        # 2) Fallback: old behaviour (bag-of-words -> random mapping)
        if not z_surface:
            toks = self._tokenize_words(sent)
            z_words = [self.map_token(t) for t in toks]
            if z_words:
                z_surface = " ".join(z_words)
            else:
                z_surface = self._plain_line(list(zip(anchors, weights)), weights)
            lemma = z_words[0] if z_words else "ø"
        else:
            # lemma for tooltip / context: first Zyntalic token
            lemma = z_surface.split()[0] if z_surface.split() else "ø"

        # Mirror / plain core line (semantic commentary)
        import random
        if random.random() < self.mirror_rate:
            core_line = self._mirrored_line(list(zip(anchors, weights)), weights)
        else:
            core_line = self._plain_line(list(zip(anchors, weights)), weights)

        pos_hint = self._pos_hint_for_word(lemma)
        ctx = make_context(lemma, anchors, pos_hint)

        out_sent = f"{z_surface}. {core_line} {ctx}"
        return {"source": sent, "target": out_sent, "anchors": anchors}


    def translate_text(self, text: str) -> List[Dict]:
        parts = [p.strip() for p in _SENT_SPLIT.split(text) if p and p.strip()]
        return [self.translate_sentence(p) for p in parts]
