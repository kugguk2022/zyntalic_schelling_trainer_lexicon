# -*- coding: utf-8 -*-
from zyntalic_core import generate_words, export_to_txt
if __name__ == "__main__":
    entries = generate_words(50, use_projection=True)
    export_to_txt(entries, "zyntalic_words_lexicon_demo.txt")
    print("Wrote zyntalic_words_lexicon_demo.txt (n=50)")
    for e in entries[:10]:
        print(e["word"], "→", e["sentence"])
