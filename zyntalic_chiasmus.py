import re
import random
import hashlib
import os
import json
from collections import Counter

# ---------------------------------------------------------
# 1. HANGUL MAPPING (The "Periodic Table" of Meaning)
# ---------------------------------------------------------
# We map specific consonants to specific "Vibes" (Anchors)
# so the reader can literally read the conflict in the character.

CONSONANT_MAP = [
    "ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"
]

VOWEL_HARMONY = ["ㅡ", "ㅗ", "ㅜ"] # Use for Agreement/Reflection
VOWEL_CONFLICT = ["ㅣ", "ㅐ", "ㅔ", "ㅑ"] # Use for Irony/Shift

def get_anchor_consonant(anchor_name):
    """Maps an anchor (e.g., Iliad) to a specific Consonant (e.g., ㄱ)."""
    # Deterministic mapping
    idx = int(hashlib.md5(anchor_name.encode()).hexdigest(), 16) % len(CONSONANT_MAP)
    return CONSONANT_MAP[idx]

def compose_hangul(initial, vowel, final):
    """Builds the block from the 3 parts."""
    CHOSEONG = ["ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ","ㅆ","ㅇ","ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]
    JUNGSEONG = ["ㅏ","ㅐ","ㅑ","ㅒ","ㅓ","ㅔ","ㅕ","ㅖ","ㅗ","ㅘ","ㅙ","ㅚ","ㅛ","ㅜ","ㅝ","ㅞ","ㅟ","ㅠ","ㅡ","ㅢ","ㅣ"]
    JONGSEONG = ["","ㄱ","ㄲ","ㄳ","ㄴ","ㄵ","ㄶ","ㄷ","ㄹ","ㄺ","ㄻ","ㄼ","ㄽ","ㄾ","ㄿ","ㅀ","ㅁ","ㅂ","ㅄ","ㅅ","ㅆ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]

    try:
        # Map input chars to standard Hangul indices
        ci = CHOSEONG.index(initial)
        vi = JUNGSEONG.index(vowel)
        ti = JONGSEONG.index(final) if final else 0
        base = 0xAC00
        return chr(base + (ci * 21 + vi) * 28 + ti)
    except:
        return initial # Fallback if mapping fails

# ---------------------------------------------------------
# 2. LATIN BODY GENERATOR
# ---------------------------------------------------------
LATIN_CONSONANTS = "bcćdđfghjklłmnńprsśtvwzźż"
LATIN_VOWELS     = "aąeęioóuy"

def generate_latin_word(text):
    seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    length = rng.choice([1, 2, 2, 3])
    out = ""
    for _ in range(length):
        out += rng.choice(LATIN_CONSONANTS) + rng.choice(LATIN_VOWELS)
    return out.capitalize() if text[0].isupper() else out

# ---------------------------------------------------------
# 3. THE CHIASMUS DETECTOR
# ---------------------------------------------------------
LEXICON_CACHE = {}
def load_lexicons():
    if LEXICON_CACHE: return
    if not os.path.exists("lexicon"): return
    for f in os.listdir("lexicon"):
        if f.endswith(".json"):
            with open(f"lexicon/{f}", "r", encoding="utf-8") as file:
                LEXICON_CACHE[f.replace(".json", "")] = json.load(file)

def analyze_context_vector(words):
    """Returns the dominant Anchor for a list of words."""
    load_lexicons()
    votes = Counter()
    ignore = {"the","and","is","of","to","in","but","not"}
    
    for w in words:
        w = w.lower()
        if w in ignore: continue
        for anchor, data in LEXICON_CACHE.items():
            if w in data.get("nouns", []) or w in data.get("verbs", []):
                votes[anchor] += 1
    
    if not votes: return "Neutral"
    return votes.most_common(1)[0][0]

def generate_mirror_sigil(sentence_text):
    """
    Splits the sentence, compares the halves, and builds the Sigil.
    """
    # 1. Split sentence into two halves (Thesis / Antithesis)
    words = re.findall(r'\w+', sentence_text)
    if not words: return ""
    
    midpoint = len(words) // 2
    first_half = words[:midpoint]
    second_half = words[midpoint:]
    
    # 2. Analyze both halves
    context_A = analyze_context_vector(first_half)
    context_B = analyze_context_vector(second_half)
    
    # 3. Get Semantic Consonants
    cons_A = get_anchor_consonant(context_A) # Thesis (Top)
    cons_B = get_anchor_consonant(context_B) # Antithesis (Bottom)
    
    # 4. Determine Relationship (The Vowel)
    if context_A == context_B:
        # Pure Reflection / Continuation (Horizontal Vowel)
        vowel = random.choice(VOWEL_HARMONY)
        rel_type = "Reflection"
    else:
        # Irony / Conflict / Shift (Vertical Vowel)
        vowel = random.choice(VOWEL_CONFLICT)
        rel_type = "Irony"
        
    # 5. Build the Sigil
    sigil = compose_hangul(cons_A, vowel, cons_B)
    return sigil, rel_type

# ---------------------------------------------------------
# 4. TRANSLATOR LOOP
# ---------------------------------------------------------
def translate_saramago_chiasmus(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    output = []
    
    print(f"{'SIGIL':<5} | {'TYPE':<12} | {'SENTENCE'}")
    print("-" * 60)

    for sent in sentences:
        if not sent.strip(): continue
        
        # 1. Translate Words (Latin Body)
        raw_words = sent.split()
        trans_words = []
        clean_text_for_analysis = []
        
        for w in raw_words:
            clean = "".join(filter(str.isalpha, w))
            clean_text_for_analysis.append(clean)
            if clean:
                tw = generate_latin_word(clean)
                punct = "".join(filter(lambda x: not x.isalpha(), w))
                trans_words.append(tw + punct)
            else:
                trans_words.append(w)
                
        body = " ".join(trans_words)
        if body.endswith("."): body = body[:-1]
        
        # 2. Generate the Chiasmus Sigil
        sigil, rtype = generate_mirror_sigil(" ".join(clean_text_for_analysis))
        
        # 3. Append
        final = f"{body} {sigil}"
        output.append(final)
        
        print(f"{sigil:<5} | {rtype:<12} | {sent[:40]}...")

    return " ".join(output)

if __name__ == "__main__":
    # Example with both Reflection and Irony
    text = """
    The war brings death, and death brings war.
    The priest blessed the knife.
    Love is the law, love is the bond.
    The king became a beggar.
    """
    
    print("\n--- PROCESSING ---")
    res = translate_saramago_chiasmus(text)
    
    print("\n--- FINAL TEXT ---")
    print(res)