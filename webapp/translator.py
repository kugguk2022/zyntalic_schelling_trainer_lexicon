# -*- coding: utf-8 -*-
"""
This module translates English text into Zyntalic
using the Chiasmus/Saramago engine.
"""
import os
import re
import sys
from typing import List, Dict, Any

# --- Add Repo Root to Path ---
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# --- Import the CORRECT Engine ---
try:
    # This is the Saramago/Chiasmus translator
    import zynthalic_chiasmus as core
except ImportError:
    print("FATAL: Could not find zynthalic_chiasmus.py. Make sure it is in the root.")
    # Fallback to a dummy module to avoid crashing the server
    class DummyCore:
        def translate_chiasmus(self, t): return "TRANSLATOR NOT FOUND"
        def analyze_context_vector(self, w): return "Neutral"
        def generate_mirror_sigil(self, t): return "!", "Error"
    core = DummyCore()


class ZyntalicTranslator:
    def __init__(self, mirror_rate: float = 0.8):
        """
        Initializes the translator.
        Note: The 'mirror_rate' is ignored, as the Chiasmus engine
        auto-detects mirrors (chiasmus) instead of using a random rate.
        """
        core.load_lexicons() # Pre-load the lexicons

    def translate_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Translates a block of text into a list of sentence pairs.
        This is used for generating the .tsv and .jsonl files.
        """
        output_rows = []
        
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue

            # 1. Get the translated Zyntalic body + sigil
            # We must silence the print statements from the core script
            zynthalic_sentence = self.get_clean_translation(sent)

            # 2. Get the anchor data for the .jsonl file
            # We re-run the analysis functions to get the metadata
            words = re.findall(r'\w+', sent)
            midpoint = len(words) // 2
            
            ctx_a = core.analyze_context_vector(words[:midpoint])
            ctx_b = core.analyze_context_vector(words[midpoint:])

            anchors = [
                [ctx_a, 0.5], # Thesis Anchor
                [ctx_b, 0.5]  # Antithesis Anchor
            ]
            
            output_rows.append({
                "source": sent,
                "target": zynthalic_sentence,
                "anchors": anchors
            })
            
        return output_rows

    def get_clean_translation(self, text: str) -> str:
        """
        Calls the core translator but captures and discards
        any print() statements from it.
        """
        # --- Mute stdout to capture only the return value ---
        original_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            # This function returns the full translated string
            translation = core.translate_chiasmus(text)
        finally:
            # Restore stdout
            sys.stdout = original_stdout
        
        # The function returns a string like: "SIGIL | TYPE | ... Vo rulo... 갣"
        # We need to extract just the final text.
        # Let's modify this slightly. We'll call the internal helpers.
        
        # --- A cleaner way to get just the text ---
        try:
            raw_words = text.split()
            trans_words = []
            clean_text_for_analysis = []

            for w in raw_words:
                clean = "".join(filter(str.isalpha, w))
                clean_text_for_analysis.append(clean)
                if clean:
                    tw = core.generate_latin_word(clean)
                    punct = "".join(filter(lambda x: not x.isalpha(), w))
                    trans_words.append(tw + punct)
                else:
                    trans_words.append(w)
            
            body = " ".join(trans_words)
            if body.endswith((".", "!", "?")): body = body[:-1]
            
            sigil, rtype = core.generate_mirror_sigil(" ".join(clean_text_for_analysis))
            
            return f"{body} {sigil}"
        except Exception as e:
            return f"Translation error: {e}"