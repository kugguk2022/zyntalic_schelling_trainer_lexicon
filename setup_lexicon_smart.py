import os
import json
import re
from collections import Counter
import random

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
TARGET_ANCHORS = [
    "Homer_Iliad", "Homer_Odyssey", "Plato_Republic",
    "Aristotle_Organon", "Virgil_Aeneid", "Dante_DivineComedy",
    "Shakespeare_Sonnets", "Goethe_Faust", "Cervantes_DonQuixote",
    "Milton_ParadiseLost", "Melville_MobyDick", "Darwin_OriginOfSpecies",
    "Austen_PridePrejudice", "Tolstoy_WarPeace", "Dostoevsky_BrothersKaramazov",
    "Laozi_TaoTeChing", "Sunzi_ArtOfWar", "Descartes_Meditations",
    "Bacon_NovumOrganum", "Spinoza_Ethics"
]

INPUT_DIR = "raw_anchors"
OUTPUT_DIR = "lexicon"

# ---------------------------------------------------------
# SIMPLE PROCESSING LOGIC (NO NLTK REQUIRED)
# ---------------------------------------------------------
def process_book_simple(filepath):
    print(f"  Reading {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except Exception as e:
        print(f"  ! Error reading file: {e}")
        return None

    # Simple word extraction using regex
    print("  Extracting words...")
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Common word lists for basic filtering
    common_adjectives = {'good', 'great', 'big', 'small', 'long', 'short', 'high', 'low', 
                        'old', 'new', 'young', 'black', 'white', 'red', 'blue', 'green',
                        'happy', 'sad', 'beautiful', 'ugly', 'strong', 'weak', 'rich', 'poor'}
    
    common_nouns = {'man', 'woman', 'child', 'house', 'tree', 'water', 'fire', 'earth',
                   'sky', 'sun', 'moon', 'star', 'day', 'night', 'time', 'year',
                   'life', 'death', 'love', 'heart', 'mind', 'soul', 'god', 'king'}
    
    common_verbs = {'is', 'are', 'was', 'were', 'have', 'has', 'had', 'do', 'does', 'did',
                   'say', 'said', 'see', 'saw', 'come', 'came', 'go', 'went', 'know',
                   'think', 'thought', 'take', 'took', 'give', 'gave', 'make', 'made'}
    
    # Simple classification based on common words and patterns
    adjectives = set()
    nouns = set()
    verbs = set()
    
    for word in words:
        if word in common_adjectives or word.endswith(('able', 'ible', 'ful', 'ic', 'ical', 'ive', 'less', 'ous')):
            adjectives.add(word)
        elif word in common_nouns or word.endswith(('tion', 'sion', 'ment', 'ness', 'ity', 'ance', 'ence')):
            nouns.add(word)
        elif word in common_verbs or word.endswith(('ed', 'ing', 'ize', 'ise')):
            verbs.add(word)
        else:
            # Default to noun for unknown words
            nouns.add(word)
    
    # Convert to lists and take most common words
    word_freq = Counter(words)
    
    def get_most_common(word_set, n=200):
        common_words = [(word, word_freq[word]) for word in word_set]
        common_words.sort(key=lambda x: x[1], reverse=True)
        return [word for word, freq in common_words[:n]]
    
    return {
        "adjectives": get_most_common(adjectives),
        "nouns": get_most_common(nouns),
        "verbs": get_most_common(verbs)
    }

def main():
    # Ensure directories exist
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        print(f"Created '{INPUT_DIR}'. Please put your .txt files here!")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"Scanning '{INPUT_DIR}' for anchors...")
    
    # Check which files we actually have
    available_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]
    
    if not available_files:
        print("CRITICAL: No .txt files found in 'raw_anchors'.")
        print("Please download at least one book (e.g. Homer_Iliad.txt) and try again.")
        return

    # Process each file found
    for filename in available_files:
        name_no_ext = filename.replace(".txt", "")
        
        print(f"\nProcessing Anchor: {name_no_ext}")
        data = process_book_simple(os.path.join(INPUT_DIR, filename))
        
        if data:
            # Add generic motifs
            data["motifs"] = [
                ["order", "chaos"], ["light", "dark"], 
                ["spirit", "flesh"], ["time", "eternity"]
            ]
            
            out_path = os.path.join(OUTPUT_DIR, f"{name_no_ext}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            print(f"  -> Saved {len(data['nouns'])} nouns to {out_path}")

    print("\nDone! Zynthalic Core can now use these lexicons.")

if __name__ == "__main__":
    main()