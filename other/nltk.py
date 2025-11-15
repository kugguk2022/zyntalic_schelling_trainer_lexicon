import os
import json
import nltk
from collections import Counter
import random

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
# The script will look for .txt files with these names in 'raw_anchors/'
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
# PROCESSING LOGIC
# ---------------------------------------------------------
def process_book(filepath):
    print(f"  Reading {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except Exception as e:
        print(f"  ! Error reading file: {e}")
        return None

    # 1. Tokenize (Split into words intelligently)
    print("  Tokenizing...")
    tokens = nltk.word_tokenize(text)
    
    # 2. POS Tagging (Identify Adjective vs Noun vs Verb)
    # 'universal' tagset simplifies tags to ADJ, NOUN, VERB, etc.
    print("  Tagging Parts of Speech...")
    tagged = nltk.pos_tag(tokens, tagset='universal')

    adjectives = set()
    nouns = set()
    verbs = set()

    # 3. Filter and Sort
    for word, tag in tagged:
        w = word.lower()
        if not w.isalpha(): continue # Skip punctuation
        if len(w) < 3: continue      # Skip 'is', 'at', 'to'

        if tag == 'ADJ':
            adjectives.add(w)
        elif tag == 'NOUN':
            nouns.add(w)
        elif tag == 'VERB':
            verbs.add(w)

    # Convert to lists
    return {
        "adjectives": list(adjectives),
        "nouns": list(nouns),
        "verbs": list(verbs)
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
        
        # Only process if it's one of our target anchors (optional restriction)
        # Remove the 'if' below if you want to process ANY text file you add.
        if name_no_ext in TARGET_ANCHORS or True: 
            print(f"\nProcessing Anchor: {name_no_ext}")
            data = process_book(os.path.join(INPUT_DIR, filename))
            
            if data:
                # Add generic motifs (since we can't easily extract these automatically)
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