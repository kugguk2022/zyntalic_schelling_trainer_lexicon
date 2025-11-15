import os
import json
import re
import random
from collections import Counter

# ---------------------------------------------------------
# 0. THE "CLASSIC" DICTIONARY (No NLTK required)
# ---------------------------------------------------------
# We explicitly list common words found in classical texts to identify POS.
# This acts as our filter. If a word in the book matches these, we keep it.

CORE_ADJECTIVES = {
    "good", "bad", "great", "small", "large", "old", "new", "young", "long", 
    "short", "bright", "dark", "fair", "foul", "wise", "foolish", "true", 
    "false", "just", "unjust", "brave", "cowardly", "sweet", "bitter", 
    "sharp", "dull", "high", "low", "deep", "shallow", "rich", "poor",
    "divine", "mortal", "ancient", "eternal", "fleeting", "hollow", "solid",
    "golden", "silver", "iron", "stone", "wooden", "silent", "loud",
    "mysterious", "sacred", "profane", "beautiful", "ugly", "vast", "tiny",
    "red", "black", "white", "green", "blue", "pale", "crimson", "shadowy"
}

CORE_VERBS = {
    "be", "have", "do", "say", "go", "come", "know", "think", "take", "see",
    "give", "make", "find", "tell", "ask", "work", "seem", "feel", "try",
    "leave", "call", "live", "die", "stand", "fall", "rise", "run", "walk",
    "fight", "love", "hate", "fear", "hope", "wish", "speak", "hear", "look",
    "move", "turn", "start", "stop", "create", "destroy", "build", "break",
    "seek", "hide", "reveal", "cast", "forge", "weave", "sing", "cry"
}

CORE_NOUNS = {
    "time", "year", "people", "way", "day", "man", "thing", "woman", "life",
    "child", "world", "school", "state", "family", "student", "group", 
    "country", "problem", "hand", "part", "place", "case", "week", "company",
    "system", "program", "question", "work", "government", "number", "night",
    "point", "home", "water", "room", "mother", "area", "money", "story",
    "fact", "month", "lot", "right", "study", "book", "eye", "job", "word",
    "business", "issue", "side", "kind", "head", "house", "service", "friend",
    "father", "power", "hour", "game", "line", "end", "member", "law", "car",
    "city", "community", "name", "president", "team", "minute", "idea", "kid",
    "body", "information", "back", "parent", "face", "others", "level", 
    "office", "door", "health", "person", "art", "war", "history", "party",
    "result", "change", "morning", "reason", "research", "girl", "guy", 
    "moment", "air", "teacher", "force", "education", "foot", "boy", "age",
    "policy", "god", "soul", "spirit", "truth", "justice", "wisdom", "virtue",
    "chaos", "void", "abyss", "shadow", "light", "fire", "earth", "wind", "sea"
}

# The list of anchors your Core script expects
EXPECTED_ANCHORS = [
    "Homer_Iliad", "Homer_Odyssey", "Plato_Republic",
    "Aristotle_Organon", "Virgil_Aeneid", "Dante_DivineComedy",
    "Shakespeare_Sonnets", "Goethe_Faust", "Cervantes_DonQuixote",
    "Milton_ParadiseLost", "Melville_MobyDick", "Darwin_OriginOfSpecies",
    "Austen_PridePrejudice", "Tolstoy_WarPeace", "Dostoevsky_BrothersKaramazov",
    "Laozi_TaoTeChing", "Sunzi_ArtOfWar", "Descartes_Meditations",
    "Bacon_NovumOrganum", "Spinoza_Ethics"
]

# ---------------------------------------------------------
# 1. PROCESSING LOGIC
# ---------------------------------------------------------

def clean_and_split(text):
    # Lowercase and remove non-alpha characters
    text = text.lower()
    words = re.findall(r'\b[a-z]{3,}\b', text) # Only words 3+ chars
    return words

def categorize_words(word_list):
    # Count frequency of words in the text
    counts = Counter(word_list)
    
    found_adj = []
    found_noun = []
    found_verb = []
    
    # Check found words against our Core Lists
    for word, count in counts.most_common():
        if word in CORE_ADJECTIVES:
            found_adj.append(word)
        elif word in CORE_NOUNS:
            found_noun.append(word)
        elif word in CORE_VERBS:
            found_verb.append(word)
            
    # If the text didn't have enough matches, backfill with random Core words
    # so the system never crashes.
    while len(found_adj) < 20: found_adj.append(random.choice(list(CORE_ADJECTIVES)))
    while len(found_noun) < 20: found_noun.append(random.choice(list(CORE_NOUNS)))
    while len(found_verb) < 20: found_verb.append(random.choice(list(CORE_VERBS)))
    
    return found_adj, found_noun, found_verb

def process():
    # Create directories
    if not os.path.exists("lexicon"): os.makedirs("lexicon")
    if not os.path.exists("raw_anchors"): os.makedirs("raw_anchors")
    
    print(f"Looking for text files in 'raw_anchors/'...")
    
    for anchor_name in EXPECTED_ANCHORS:
        txt_path = os.path.join("raw_anchors", f"{anchor_name}.txt")
        json_path = os.path.join("lexicon", f"{anchor_name}.json")
        
        words = []
        
        if os.path.exists(txt_path):
            print(f"Processing {anchor_name}...")
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    words = clean_and_split(text)
            except Exception as e:
                print(f"  Error reading {txt_path}: {e}")
        else:
            # If file missing, we proceed silently using the backfill mechanism
            # This allows the demo to run even without downloading 20 books.
            pass

        adjs, nouns, verbs = categorize_words(words)
        
        # Create the JSON structure
        data = {
            "adjectives": adjs,
            "nouns": nouns,
            "verbs": verbs,
            "motifs": [
                ["order", "chaos"], ["light", "dark"], 
                ["one", "all"], ["mind", "matter"], 
                ["time", "eternity"]
            ] 
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    print("------------------------------------------------")
    print("Done! 'lexicon/' folder is ready for Zynthalic Core.")
    print("If you didn't put files in 'raw_anchors/', we used default fallback words.")

if __name__ == "__main__":
    process()