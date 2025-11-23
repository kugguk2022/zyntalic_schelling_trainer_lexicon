import json
import numpy as np
import os

# Try real embeddings first, fallback to deterministic
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    def embed_texts(texts):
        return model.encode(texts, show_progress_bar=True)
except ImportError:
    from zyntalic_embeddings import embed_text
    def embed_texts(texts):
        return [embed_text(t, dim=384) for t in texts]

INPUT_FILE = "data/persepolis_clean.jsonl"
EMBED_FILE = "data/persepolis.npy"
META_FILE  = "data/persepolis_meta.jsonl"

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Please run normalize_data.py first.")
        return

    sources = []
    metadata = []

    print("Reading data...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            row = json.loads(line)
            sources.append(row["source"])
            
            metadata.append({
                "id": i,
                "lemma": row["lemma"],
                "target": row["target"],
                "anchors": row["anchors"]
            })

    print(f"Encoding {len(sources)} sentences...")
    embeddings = embed_texts(sources)

    print("Saving artifacts...")
    np.save(EMBED_FILE, embeddings)
    
    with open(META_FILE, "w", encoding="utf-8") as f:
        for m in metadata:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    print("Success. Embedding Index Built.")

if __name__ == "__main__":
    main()

