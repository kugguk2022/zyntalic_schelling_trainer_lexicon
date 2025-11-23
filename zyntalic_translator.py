import re
import random
import hashlib
import os
import json

# ---------------------------------------------------------
# 1. CORE ALPHABET & SYLLABLE LOGIC
# ---------------------------------------------------------
CHOSEONG = ["ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ","ㅆ","ㅇ","ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]
JUNGSEONG = ["ㅏ","ㅐ","ㅑ","ㅒ","ㅓ","ㅔ","ㅕ","ㅖ","ㅗ","ㅘ","ㅙ","ㅚ","ㅛ","ㅜ","ㅝ","ㅞ","ㅟ","ㅠ","ㅡ","ㅢ","ㅣ"]
JONGSEONG = ["","ㄱ","ㄲ","ㄳ","ㄴ","ㄵ","ㄶ","ㄷ","ㄹ","ㄺ","ㄻ","ㄼ","ㄽ","ㄾ","ㄿ","ㅀ","ㅁ","ㅂ","ㅄ","ㅅ","ㅆ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]

POLISH_CONSONANTS = "bcćdđfghjklłmnńprsśtvwzźż"
POLISH_VOWELS     = "aąeęioóuy"

def deterministic_seed(word):
    """Turn an English word into a specific number seed."""
    h = hashlib.sha256(word.encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def compose_hangul(seed, idx):
    random.seed(seed + idx)
    c = random.choice(CHOSEONG)
    v = random.choice(JUNGSEONG)
    t = random.choice(JONGSEONG)
    # Hangul Composition Math
    base = 0xAC00
    ci, vi, ti = CHOSEONG.index(c), JUNGSEONG.index(v), JONGSEONG.index(t)
    return chr(base + (ci * 21 + vi) * 28 + ti)

def compose_latin(seed, idx):
    random.seed(seed + idx)
    c = random.choice(POLISH_CONSONANTS)
    v = random.choice(POLISH_VOWELS)
    t = random.choice(["", random.choice(POLISH_CONSONANTS)])
    return c + v + t

def get_zynthalic_word(english_word):
    """
    Translates English -> Zynthalic.
    'Love' will ALWAYS return the same Zynthalic string.
    """
    w = english_word.lower()
    seed = deterministic_seed(w)
    rng = random.Random(seed)
    
    # Determine length (2 or 3 syllables usually)
    length = rng.choice([2, 2, 3])
    
    syllables = []
    for i in range(length):
        # 50/50 chance of Hangul vs Polish for each syllable
        if rng.random() > 0.5:
            syllables.append(compose_hangul(seed, i))
        else:
            syllables.append(compose_latin(seed, i))
            
    # Fuse them
    word = "".join(syllables)
    
    # Capitalize if original was capitalized
    if english_word[0].isupper():
        word = word.capitalize() # Only works on Latin parts, but good enough
        
    return word

# ---------------------------------------------------------
# 2. DICTIONARY BUILDER
# ---------------------------------------------------------
DICTIONARY = {}

def load_anchors():
    """Loads the JSON files we built earlier to add 'Flavor' text."""
    anchors = {}
    lex_dir = "lexicon"
    if not os.path.exists(lex_dir): return {}
    
    for f in os.listdir(lex_dir):
        if f.endswith(".json"):
            with open(os.path.join(lex_dir, f), 'r', encoding='utf-8') as file:
                anchors[f.replace(".json", "")] = json.load(file)
    return anchors

ANCHOR_DATA = load_anchors()

def get_definition_flavor(english_word):
    """
    Finds which Ancient Books contain this word to create a 'history'.
    """
    found_in = []
    w = english_word.lower()
    for book, data in ANCHOR_DATA.items():
        if w in data.get("nouns", []) or w in data.get("verbs", []) or w in data.get("adjectives", []):
            found_in.append(book)
    
    if not found_in:
        return "A Neologism; concept not found in the Ancient Anchors."
    
    # Pick 2 random books
    refs = random.sample(found_in, min(2, len(found_in)))
    return f"Rooted in {', '.join(refs)}."

# ---------------------------------------------------------
# 3. TRANSLATOR LOGIC
# ---------------------------------------------------------
def translate_text(text):
    """
    Parses text, translates words, preserves punctuation.
    """
    # Split by keeping delimiters (punctuation, spaces)
    tokens = re.split(r'(\W+)', text)
    translated_tokens = []
    
    for t in tokens:
        if t.strip() and t.replace("'", "").isalpha():
            # It's a word
            z_word = get_zynthalic_word(t)
            translated_tokens.append(z_word)
            
            # Add to dictionary
            if t.lower() not in DICTIONARY:
                DICTIONARY[t.lower()] = {
                    "zyn": z_word,
                    "etymology": get_definition_flavor(t)
                }
        else:
            # It's punctuation or space
            translated_tokens.append(t)
            
    return "".join(translated_tokens)

# Simple class wrapper for compatibility with web app translator behaviour.
try:
    from webapp.translator import ZyntalicTranslator as _WebTranslator
except Exception:
    _WebTranslator = None


class ZyntalicTranslator:
    def __init__(self, mirror_rate: float = 0.8):
        self.mirror_rate = mirror_rate
        self._delegate = _WebTranslator(mirror_rate=mirror_rate) if _WebTranslator else None

    def translate_text(self, text: str):
        if self._delegate:
            return self._delegate.translate_text(text)
        # Fallback: mimic web translator contract when delegate missing
        translated = translate_text(text)
        return [{"source": text, "target": translated, "anchors": []}]


# ---------------------------------------------------------
# 4. MAIN EXECUTION
# ---------------------------------------------------------
if __name__ == "__main__":
    # A. TRANSLATE A SAMPLE
    sample_text = """
    In the beginning, there was silence. The sea whispered to the sky.
    Truth is a pathless land, yet we walk it with heavy feet.
    """
    
    print("--- ORIGINAL ENGLISH ---")
    print(sample_text)
    
    translated = translate_text(sample_text)
    
    print("\n--- ZYNTHALIC TRANSLATION ---")
    print(translated)
    
    # B. GENERATE DICTIONARY
    print("\n--- ZYNTHALIC DICTIONARY (AUTO-GENERATED) ---")
    print(f"{'ZYNTHALIC':<15} | {'ENGLISH':<12} | {'ETYMOLOGY'}")
    print("-" * 70)
    
    for eng, data in list(DICTIONARY.items())[:10]: # Show top 10
        print(f"{data['zyn']:<15} | {eng:<12} | {data['etymology']}")

    # C. EXPORT
    with open("zynthalic_translation.txt", "w", encoding="utf-8") as f:
        f.write(translated)
    
    with open("zynthalic_dictionary.json", "w", encoding="utf-8") as f:
        json.dump(DICTIONARY, f, indent=2, ensure_ascii=False)
        
    print("\nSaved 'zynthalic_translation.txt' and 'zynthalic_dictionary.json'.")
