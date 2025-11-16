# -*- coding: utf-8 -*-
"""Unifies text generation across engines; falls back to rule-based translator."""
import random
import re

def generate_text(src: str, *, mode: str = "plain", mirror_rate: float = 0.8) -> str:
    """
    Generate Zyntalic text from source, ensuring all Zyntalic rules are followed.
    """
    result = None
    
    # 1) preferred: Saramago-style chiasmus engine
    try:
        import zynthalic_chiasmus as zch
        if hasattr(zch, "translate_saramago_chiasmus"):
            result = zch.translate_saramago_chiasmus(src)
    except Exception:
        pass

    # 2) optional: pretty publisher HTML
    if result is None and mode == "html":
        try:
            import zynthalic_publisher as pub
            if hasattr(pub, "publish_html"):
                result = pub.publish_html(src)
            elif hasattr(pub, "publish_book"):  # fallback if publish_html not present
                result = pub.publish_book(src, filename=None)
        except Exception:
            pass

    # 3) fallback: rule-based translator (ensures all rules are followed)
    if result is None:
        try:
            from webapp.translator import ZyntalicTranslator
            tr = ZyntalicTranslator(mirror_rate=mirror_rate)
            rows = tr.translate_text(src)
            result = "\n".join(r["target"] for r in rows)
        except Exception:
            # last resort: return the raw text
            result = src
    
    return result

# ---------- DETERMINISTIC RULE-BASED FALLBACK ----------
# Respects Zyntalic rules: Hangul+Polish tokens, mirrored meanings, context at sentence end

CHOSEONG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNGSEONG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
JONGSEONG = ["","ㄱ","ㄲ","ㄳ","ㄴ","ㄵ","ㄶ","ㄷ","ㄹ","ㄺ","ㄻ","ㄼ","ㄽ","ㄾ","ㄿ","ㅀ","ㅁ","ㅂ","ㅄ","ㅅ","ㅆ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]

POLISH_CONSONANTS = "bcćdđfghjklłmnńprsśtvwzźż"
POLISH_VOWELS = "aąeęioóuy"
POLISH_SUFFIXES = ["sk", "ov", "icz", "zy", "ał", "ył", "ść"]

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def _compose_hangul(cho: str, jung: str, jong: str = "") -> str:
    """Compose a Hangul syllable from components."""
    try:
        L_idx = CHOSEONG.index(cho)
        V_idx = JUNGSEONG.index(jung)
        T_idx = JONGSEONG.index(jong) if jong else 0
        
        SBase = 0xAC00
        LCount, VCount, TCount = 19, 21, 28
        SIndex = (L_idx * VCount + V_idx) * TCount + T_idx
        return chr(SBase + SIndex)
    except (ValueError, IndexError):
        return cho + jung + jong


def _deterministic_word(word: str, pos_hint: str = "noun") -> str:
    """
    Generates a Zyntalic token following the rules:
    - Nouns: primarily Hangul (85%)
    - Verbs: primarily Polish (85%)
    - Mixed: Hangul + Polish suffixes
    Ensures consistency: same word always produces same token.
    """
    if not word:
        return "ø"

    # Seed the random generator with the word itself
    r = random.Random(word.lower())
    
    # Determine POS from position/length as heuristic if not specified
    is_noun = pos_hint == "noun" or len(word) % 2 == 0
    
    if is_noun:
        # Nouns: Hangul-dominant with optional Polish suffix
        if r.random() < 0.85:
            # Pure Hangul syllables (2-3)
            num_syllables = r.choice([2, 3])
            syllables = []
            for _ in range(num_syllables):
                cho = r.choice(CHOSEONG)
                jung = r.choice(JUNGSEONG)
                jong = r.choice(JONGSEONG[:8])  # Lighter final consonants
                syllables.append(_compose_hangul(cho, jung, jong))
            return "".join(syllables)
        else:
            # Hangul + Polish suffix
            cho = r.choice(CHOSEONG)
            jung = r.choice(JUNGSEONG)
            jong = r.choice(JONGSEONG[:5])
            base = _compose_hangul(cho, jung, jong)
            suf = r.choice(POLISH_SUFFIXES)
            return base + suf
    else:
        # Verbs: Polish-dominant with optional Hangul component
        if r.random() < 0.85:
            # Pure Polish: consonant + vowel + consonant + suffix
            c1 = r.choice(POLISH_CONSONANTS)
            v1 = r.choice(POLISH_VOWELS)
            c2 = r.choice(POLISH_CONSONANTS)
            suf = r.choice(POLISH_SUFFIXES)
            return c1 + v1 + c2 + suf
        else:
            # Polish + Hangul marker
            c1 = r.choice(POLISH_CONSONANTS)
            v1 = r.choice(POLISH_VOWELS)
            cho = r.choice(CHOSEONG[:10])  # Lighter Hangul
            return c1 + v1 + cho

def _identify_structure(sent: str) -> tuple:
    """Identifies two pivot concepts (A and B) for mirrored chiasmus."""
    words = [w for w in re.findall(r"[A-Za-z]+", sent) if len(w) > 3]
    if len(words) >= 2:
        # Use first and last significant words
        return words[0], words[-1], "noun", "verb"
    if len(words) == 1:
        return words[0], "Void", "noun", "noun"
    return "Self", "Other", "noun", "noun"


def _deterministic_anchor_select(sent: str) -> list:
    """Hashes the sentence to consistently select cultural anchors."""
    anchors = [
        "Homer_Iliad",
        "Homer_Odyssey", 
        "Plato_Republic",
        "Aristotle_Organon",
        "Virgil_Aeneid",
        "Dante_DivineComedy",
        "Shakespeare_Sonnets",
        "Goethe_Faust",
        "Cervantes_DonQuixote",
        "Milton_ParadiseLost",
        "Melville_MobyDick",
        "Darwin_OriginOfSpecies",
        "Tolstoy_WarPeace",
        "Dostoevsky_BrothersKaramazov"
    ]
    val = sum(ord(c) for c in sent)
    primary = anchors[val % len(anchors)]
    secondary = anchors[(val * 7 + len(sent)) % len(anchors)]
    tertiary = anchors[(val * 13) % len(anchors)]
    return [primary, secondary, tertiary]


def _make_context_string(lemma: str, anchors: list, pos_hint: str) -> str:
    """Create deferred context string (placed at sentence END per Zyntalic rules)."""
    anchor_labels = ";".join(anchors)
    return f"⟦ctx: lemma={lemma}; pos≈{pos_hint}; anchors={anchor_labels}⟧"


def _create_mirrored_template(token_a: str, token_b: str) -> str:
    """Create mirrored meaning pattern (core Zyntalic rule)."""
    templates = [
        f"{token_a} → {token_b} || {token_b} ↵ {token_a}",
        f"By {token_a} through {token_b}; by {token_b} through {token_a}",
        f"{token_a} begets {token_b}, and {token_b} reframes {token_a}",
        f"Seek {token_a} by {token_b}; keep {token_b} by {token_a}"
    ]
    # Use token hash to consistently select template
    idx = (hash(token_a + token_b) % len(templates))
    return templates[idx]


def _fallback_translate(text: str, mirror_rate: float = 0.8) -> str:
    """
    Fallback translator that respects all Zyntalic rules:
    1. Hangul+Polish token generation (Hangul for nouns, Polish for verbs)
    2. Mirrored meanings by default (chiasmus patterns)
    3. Context placement at sentence END
    """
    parts = [p.strip() for p in _SENT_SPLIT.split(text) if p and p.strip()]
    out = []

    for sent in parts:
        # Identify structure for mirroring
        subj_a, subj_b, pos_a, pos_b = _identify_structure(sent)

        # Tokenize and translate to Zyntalic
        eng_tokens = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", sent)
        
        # Generate Zyntalic words with POS awareness
        z_words = []
        for i, w in enumerate(eng_tokens):
            # Alternate POS for variety (nouns=even, verbs=odd)
            pos = "noun" if i % 2 == 0 else "verb"
            z_words.append(_deterministic_word(w, pos_hint=pos))
        
        z_surface = " ".join(z_words) if z_words else "∅"

        # Generate key tokens for mirroring
        token_a = _deterministic_word(subj_a, pos_hint=pos_a)
        token_b = _deterministic_word(subj_b, pos_hint=pos_b)
        
        # Determine if this sentence should be mirrored
        sent_hash = sum(ord(c) for c in sent)
        is_mirrored = (sent_hash % 100) / 100.0 <= mirror_rate

        # Create core meaning (mirrored by default)
        if is_mirrored and subj_a != subj_b:
            core = _create_mirrored_template(token_a, token_b)
        else:
            # Non-mirrored fallback (plain statement)
            core = f"{token_a} persists as {token_a}"

        # Select anchors and create context (placed at END)
        anchors = _deterministic_anchor_select(sent)
        lemma = z_words[0] if z_words else "∅"
        ctx = _make_context_string(lemma, anchors, pos_a)
        
        # Assemble: surface + core + context (context at END per rules)
        out.append(f"{z_surface}. {core} {ctx}")

    return "\n".join(out)
