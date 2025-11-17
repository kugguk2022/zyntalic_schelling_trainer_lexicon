# -*- coding: utf-8 -*-
"""
Zyntalic syntax + morphology rules.

- Word order: Subject – Object – Verb – Context  (S-O-V-C)
- Plurals: Hungarian-style suffixes; uncountables / "beyond many" -> "ur"
- Tense marking: French-style (present default, past & future marked on verb)
"""

from dataclasses import dataclass
from typing import Optional, Callable

# A tiny vowel-harmony proxy just to get a Hungarian-ish feeling.
BACK_VOWELS = "aáoóuú"
FRONT_VOWELS = "eéiíöőüű"


@dataclass
class ParsedSentence:
    subject: str
    verb: str
    obj: Optional[str]
    context: Optional[str]
    tense: str  # "present", "past", "future"
    subj_is_plural: bool
    obj_is_plural: bool
    subj_uncountable: bool = False
    obj_uncountable: bool = False
    subj_beyond_many: bool = False
    obj_beyond_many: bool = False


def _choose_hu_plural_suffix(stem: str) -> str:
    """Very coarse Hungarian-ish plural suffix decision."""
    s = stem.lower()
    if any(v in s for v in BACK_VOWELS):
        return "ok"
    if any(v in s for v in FRONT_VOWELS):
        return "ek"
    # no clear vowels -> neutral
    return "k"


def make_plural(stem: str, *, uncountable: bool = False,
                beyond_many: bool = False) -> str:
    """
    Plural system:
    - Normal plural: stem + (ok|ek|k) (Hungarian-like)
    - Uncountable / beyond-many: stem + "ur"
    """
    if uncountable or beyond_many:
        return stem + "ur"
    return stem + _choose_hu_plural_suffix(stem)


def mark_tense(z_verb: str, tense: str) -> str:
    """
    French-ish tense markings:

    - present: bare stem
    - past: a closed 'é' style ending
    - future: analytic 'va-' auxiliary before stem ("je vais parler" vibe)
    """
    tense = (tense or "present").lower()
    if tense == "past":
        # past participle flavour
        return z_verb + "é"
    if tense == "future":
        # analytic future: auxiliary + infinitive
        return "va-" + z_verb
    return z_verb


def to_zyntalic_order(
    parsed: ParsedSentence,
    map_token: Callable[[str], str],
) -> str:
    """
    Convert a ParsedSentence into a Zyntalic surface string using:

    - S-O-V-C order
    - Hungarian-like plurals
    - French-like tense marking
    """
    # Subject
    s = map_token(parsed.subject) if parsed.subject else ""
    if s and parsed.subj_is_plural:
        s = make_plural(
            s,
            uncountable=parsed.subj_uncountable,
            beyond_many=parsed.subj_beyond_many,
        )

    # Object
    o = map_token(parsed.obj) if parsed.obj else ""
    if o and parsed.obj_is_plural:
        o = make_plural(
            o,
            uncountable=parsed.obj_uncountable,
            beyond_many=parsed.obj_beyond_many,
        )

    # Verb
    v = map_token(parsed.verb) if parsed.verb else ""
    if v:
        v = mark_tense(v, parsed.tense)

    # Context: we do not pluralize or tense-mark context; it's often a PP/adverbial.
    c = map_token(parsed.context) if parsed.context else ""

    parts = [p for p in (s, o, v, c) if p]
    return " ".join(parts)
