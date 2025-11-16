import json
import os
import zynthalic_chiasmus as translator  # Uses the smart translator we made

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
INPUT_FILE = "raw_anchors/The_Bookseller_of_Kabul.txt"  # Change to your book path
OUTPUT_FILE = "The_Bookseller.zyntalic_clean.jsonl"

def generate_clean_pairs():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Could not find {INPUT_FILE}")
        return

    print(f"Reading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    print(f"Translating {len(lines)} lines...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out_f:
        for line in lines:
            text = line.strip()
            if not text: continue
            if len(text) < 10: continue # Skip tiny lines

            # 1. Get the CLEAN Zynthalic Translation
            # (No 'Between order and chaos' templates, just the translation)
            zynthalic_text = translator.translate_chiasmus(text)
            
            # 2. Extract just the text (the translator prints logs, we silence them)
            # The translate function returns the full string.
            
            # 3. Clean up the output (remove the logging prints if they are captured)
            # Our translator returns a clean string like "Vo word... 꽇"
            
            # 4. Create the Training Pair
            entry = {
                "source": text,          # English
                "target": zynthalic_text # Zynthalic Translation
            }
            
            # Write to JSONL
            out_f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f" Done! Saved clean training data to {OUTPUT_FILE}")

if __name__ == "__main__":
    # Mute the print statements from the translator logic to keep console clean
    import sys, io
    original_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        generate_clean_pairs()
    finally:
        sys.stdout = original_stdout
        print(f"Finished. Check {OUTPUT_FILE}")