# -*- coding: utf-8 -*-
import hashlib
import re
from typing import Dict, List, Tuple

try:
    from zyntalic_core import (
        CHOSEONG,
        anchor_weights_for_vec,
        base_embedding,
        generate_word,
        make_context,
    )
    try:
        from zyntalic.utils.rng import get_rng
    except Exception:
        from utils.rng import get_rng  # type: ignore
except Exception:
    import random

    CHOSEONG = "BCDFGHJKLMNPQRSTVWXYZ"

    def get_rng(seed_input: str = "fallback"):
        h = hashlib.sha256(seed_input.encode("utf-8")).hexdigest()
        return random.Random(int(h[:8], 16))

    def base_embedding(s: str, dim: int = 300):
        rng = get_rng(f"embed::{s}")
        return [rng.random() for _ in range(dim)]

    def anchor_weights_for_vec(v, top_k=3):
        names = ["Homer_Iliad", "Homer_Odyssey", "Plato_Rep"]
        rng = get_rng("anchors")
        weights = [rng.random() for _ in names]
        s = sum(weights) or 1.0
        pairs = list(zip(names, [w / s for w in weights]))
        pairs.sort(key=lambda x: x[1], reverse=True)
        return pairs[:top_k]

    def generate_word(seed_key: str = ""):
        rng = get_rng(seed_key or "fallback")
        letters = list(CHOSEONG)
        return "".join(rng.choice(letters) for _ in range(3))

    def make_context(lemma, anchors, pos_hint):
        labs = ";".join(a for a in anchors)
        return f"[ctx: lemma={lemma}; pos={pos_hint}; anchors={labs}]"


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


class ZyntalicTranslator:
    def __init__(self, mirror_rate: float = 0.8):
        self.mirror_rate = mirror_rate
        self.lex_map: Dict[str, str] = {}

    def _tokenize_words(self, s: str) -> List[str]:
        return re.findall(r"[A-Za-z�?-�-�~-����-Ǩ]+", s)

    def _pos_hint_for_word(self, zword: str) -> str:
        return "noun" if any(ch in zword for ch in CHOSEONG) else "verb"

    def map_token(self, tok: str) -> str:
        key = tok.lower()
        if key in self.lex_map:
            return self.lex_map[key]
        z = generate_word(key)
        self.lex_map[key] = z
        return z

    def sentence_to_anchors(self, sent: str, top_k: int = 3) -> List[Tuple[str, float]]:
        v = base_embedding(sent, dim=300)
        return anchor_weights_for_vec(v, top_k=top_k)

    def _mirrored_line(self, anchor_names, weights) -> str:
        try:
            from zyntalic_core import _choose_motif, TEMPLATES

            rng = get_rng("mirror::" + "|".join(anchor_names))
            A, B = _choose_motif(rng, anchor_names, weights)
            t = rng.choice(TEMPLATES)
            return t.format(A=A, B=B)
        except Exception:
            A = anchor_names[0] if anchor_names else "order"
            B = anchor_names[1] if len(anchor_names) > 1 else "chaos"
            return f"{A} with {B} returns, then retreats."

    def _plain_line(self, anchor_names, weights) -> str:
        try:
            from zyntalic_core import plain_sentence_anchored

            rng = get_rng("plain::" + "|".join(anchor_names))
            return plain_sentence_anchored(rng, anchor_names, weights)
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

        anchors = self.sentence_to_anchors(sent, top_k=3)
        anchor_names = [a for a, _ in anchors]
        weights = [w for _, w in anchors]

        z_surface = None
        try:
            from english_parser import parse_sentence
            from zyntalic_syntax import to_zyntalic_order

            parsed = parse_sentence(sent)
            z_surface = to_zyntalic_order(parsed, self.map_token)
        except Exception:
            z_surface = None

        if not z_surface:
            toks = self._tokenize_words(sent)
            z_words = [self.map_token(t) for t in toks]
            if z_words:
                z_surface = " ".join(z_words)
            else:
                z_surface = self._plain_line(anchor_names, weights)
            lemma = z_words[0] if z_words else "??"
        else:
            lemma = z_surface.split()[0] if z_surface.split() else "??"

        rng = get_rng("core::" + sent)
        if rng.random() < self.mirror_rate:
            core_line = self._mirrored_line(anchor_names, weights)
        else:
            core_line = self._plain_line(anchor_names, weights)

        pos_hint = self._pos_hint_for_word(lemma)
        ctx = make_context(lemma, anchor_names, pos_hint)

        out_sent = f"{z_surface}. {core_line} {ctx}"
        return {"source": sent, "target": out_sent, "anchors": anchors}

    def translate_text(self, text: str) -> List[Dict]:
        parts = [p.strip() for p in _SENT_SPLIT.split(text) if p and p.strip()]
        return [self.translate_sentence(p) for p in parts]
