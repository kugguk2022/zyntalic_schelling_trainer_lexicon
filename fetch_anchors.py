import os
import urllib.request
import time

# ---------------------------------------------------------
# CONFIGURATION: Map filenames to Gutenberg Book IDs
# ---------------------------------------------------------
# These IDs are the standard Project Gutenberg identifiers.
BOOK_MAP = {
    "Homer_Iliad": "6130",                  # The Iliad (Butler trans)
    "Homer_Odyssey": "1727",                # The Odyssey (Butler trans)
    "Plato_Republic": "1497",               # The Republic
    "Aristotle_Organon": "2412",            # The Categories (Part of Organon)
    "Virgil_Aeneid": "456",                 # The Aeneid
    "Dante_DivineComedy": "8800",           # The Divine Comedy
    "Shakespeare_Sonnets": "1041",          # Sonnets
    "Goethe_Faust": "14591",                # Faust
    "Cervantes_DonQuixote": "996",          # Don Quixote
    "Milton_ParadiseLost": "20",            # Paradise Lost
    "Melville_MobyDick": "2701",            # Moby Dick
    "Darwin_OriginOfSpecies": "1228",       # Origin of Species
    "Austen_PridePrejudice": "1342",        # Pride and Prejudice
    "Tolstoy_WarPeace": "2600",             # War and Peace
    "Dostoevsky_BrothersKaramazov": "28054",# The Brothers Karamazov
    "Laozi_TaoTeChing": "4033",             # Tao Te Ching
    "Sunzi_ArtOfWar": "132",                # The Art of War
    "Descartes_Meditations": "59",          # Meditations on First Philosophy
    "Bacon_NovumOrganum": "45988",          # The New Organon
    "Spinoza_Ethics": "3800"                # Ethics
}

TARGET_DIR = "raw_anchors"
BASE_URL = "https://www.gutenberg.org/cache/epub/{}/pg{}.txt"

def download_anchors():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)
        print(f"Created directory: {TARGET_DIR}")

    print(f"Starting download of {len(BOOK_MAP)} anchors...")
    print("------------------------------------------------")

    for filename, book_id in BOOK_MAP.items():
        url = BASE_URL.format(book_id, book_id)
        output_path = os.path.join(TARGET_DIR, f"{filename}.txt")
        
        if os.path.exists(output_path):
            print(f"[SKIP] {filename} already exists.")
            continue

        print(f"[DOWNLOADING] {filename} (ID: {book_id})...")
        
        try:
            # Use a user-agent to avoid being blocked by Gutenberg
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (ZynthalicBot/1.0)'}
            )
            with urllib.request.urlopen(req) as response:
                data = response.read().decode('utf-8', errors='ignore')
                
                # OPTIONAL: Strip the Gutenberg License header/footer 
                # (Rough heuristic: delete first 1% and last 10% if you want cleaner data)
                # For now, we save raw to ensure we don't cut actual text.
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(data)
            
            # Be polite to the server
            time.sleep(1) 
            
        except Exception as e:
            print(f"  ! FAILED to download {filename}: {e}")

    print("------------------------------------------------")
    print("All downloads finished. You can now run 'setup_lexicon_smart.py'.")

if __name__ == "__main__":
    download_anchors()