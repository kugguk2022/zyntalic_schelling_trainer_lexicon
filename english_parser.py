# -*- coding: utf-8 -*-
"""
Minimal English → ParsedSentence parser.

Primary path: spaCy (if installed).
Fallback: simple heuristic split (S V O [context]).
"""

from typing import Optional
from zyntalic_syntax import ParsedSentence

try:
    import spacy
    try:
        _NLP = spacy.load("en_core_web_sm")
    except Exception:
        _NLP = None
except Exception:
    _NLP = None


def _guess_plural(word: Optional[str]) -> bool:
    if not word:
        return False
    w = word.lower()
    # naive plural: ends with s but not obvious 3rd person verb
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return True
    return False


def _parse_with_spacy(sentence: str) -> ParsedSentence:
    doc = _NLP(sentence)
    root = next((t for t in doc if t.head == t and t.pos_ in ("VERB", "AUX")), None)
    if root is None:
        # degenerate case: treat first content word as verb
        root = next((t for t in doc if t.pos_ in ("VERB", "AUX")), doc[0])

    subj_tok = next(
        (c for c in root.children if c.dep_ in ("nsubj", "nsubjpass")),
        None,
    )
    obj_tok = next(
        (c for c in root.children if c.dep_ in ("dobj", "obj")),
        None,
    )

    subject = subj_tok.text if subj_tok is not None else ""
    verb = root.lemma_ if root.lemma_ else root.text
    obj = obj_tok.text if obj_tok is not None else None

    # context = everything not in subject/verb/object
    context_tokens = []
    for t in doc:
        if t is root or t is subj_tok or t is obj_tok:
            continue
        context_tokens.append(t.text)
    context = " ".join(context_tokens) or None

    # tense from morphology
    tense = "present"
    m = root.morph
    if "Tense=Past" in m:
        tense = "past"
    elif "Tense=Fut" in m:
        tense = "future"

    subj_plural = _guess_plural(subject)
    obj_plural = _guess_plural(obj)

    return ParsedSentence(
        subject=subject,
        verb=verb,
        obj=obj,
        context=context,
        tense=tense,
        subj_is_plural=subj_plural,
        obj_is_plural=obj_plural,
    )


def _parse_heuristic(sentence: str) -> ParsedSentence:
    toks = [t for t in sentence.strip().split() if t]
    subject = toks[0] if toks else ""
    verb = toks[1] if len(toks) > 1 else ""
    obj = toks[2] if len(toks) > 2 else None
    context = " ".join(toks[3:]) or None

    subj_plural = _guess_plural(subject)
    obj_plural = _guess_plural(obj)

    # no robust way to see tense without a tagger -> assume present
    return ParsedSentence(
        subject=subject,
        verb=verb,
        obj=obj,
        context=context,
        tense="present",
        subj_is_plural=subj_plural,
        obj_is_plural=obj_plural,
    )


def parse_sentence(sentence: str) -> ParsedSentence:
    if _NLP is not None:
        try:
            return _parse_with_spacy(sentence)
        except Exception:
            pass
    # fallback
    return _parse_heuristic(sentence)
