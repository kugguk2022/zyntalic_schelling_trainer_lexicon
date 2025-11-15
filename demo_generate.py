# -*- coding: utf-8 -*-
from zyntalic_core import generate_words, export_to_txt
if __name__ == "__main__":
    entries = generate_words(200, use_projection=True)
    export_to_txt(entries, "zyntalic_words_demo.txt")
    for e in entries[:5]:
        print(e["word"], "→", e["sentence"])
