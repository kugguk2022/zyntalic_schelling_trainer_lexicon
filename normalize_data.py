# Create the normalization script
cat > scripts/normalize_data.py << 'EOF'
import json
import re
import sys
import os

def parse_zyntalic_line(target_str):
    """Separates the Zyntalic text from the context block."""
    if "⟦ctx:" not in target_str:
        return target_str.strip(), None, None, []

    text_part, ctx_part = target_str.split("⟦ctx:", 1)
    text_part = text_part.strip()
    
    lemma = None
    pos = None
    anchors = []

    m_lemma = re.search(r"lemma=([^;\]]+)", ctx_part)
    if m_lemma: lemma = m_lemma.group(1).strip()

    m_pos = re.search(r"pos≈([^;\]]+)", ctx_part)
    if m_pos: pos = m_pos.group(1).strip()

    m_anchors = re.search(r"anchors=([^\]]+)", ctx_part)
    if m_anchors:
        raw = m_anchors.group(1).replace("|", ",")
        anchors = [a.strip() for a in raw.split(",") if a.strip()]

    return text_part, lemma, pos, anchors

def main():
    INPUT_FILE = "outputs/Persepolis_1.zyntalic.jsonl"  # Adjust path
    OUTPUT_FILE = "data/persepolis_clean.jsonl"

    if not os.path.exists(INPUT_FILE):
        print(f"Error: Could not find {INPUT_FILE}")
        return

    print(f"Normalizing {INPUT_FILE}...")
    count = 0
    
    with open(INPUT_FILE, "r", encoding="utf-8") as fin, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as fout:
        
        for line in fin:
            if not line.strip(): continue
            try:
                row = json.loads(line)
                
                clean_target, lemma, pos, ctx_anchors = parse_zyntalic_line(row.get("target", ""))
                
                final_row = {
                    "source": row.get("source"),
                    "target": clean_target,
                    "lemma": lemma,
                    "pos": pos,
                    "anchors": row.get("anchors", [])  # The numeric weights
                }
                
                fout.write(json.dumps(final_row, ensure_ascii=False) + "\n")
                count += 1
            except json.JSONDecodeError:
                continue

    print(f"Done. Wrote {count} clean records to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
EOF

python scripts/normalize_data.py
