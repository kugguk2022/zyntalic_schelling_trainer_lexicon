# Zyntalic Schelling Trainer (with Lexicon Priors)

**What this is:** A tiny, dependency-light scaffold that aligns Zyntalic’s internal embeddings to cultural Schelling points (great-book anchors) and bends surface style using **anchor-specific lexicons**, while keeping your rules:
- Hangul+Polish tokens
- Mirrored meanings by default
- Context appended at the end of each sentence

## Files
- `zyntalic_core.py` — generator + embeddings + **lexicon prior** + optional projection `models/W.npy`
- `train_projection.py` — trains thin projection **W** (Procrustes or Ridge) from `anchors.tsv`
- `anchors.tsv` — template with `(anchor_id, excerpt)` rows (replace with your curated/authorized text)
- `lexicon/*.json` — per-anchor wordlists and mirrored motifs (safe generic terms; extend freely)
- `demo_generate.py` / `demo_generate_lexicon.py` — quick demos
- `models/` — output folder for `W.npy` and `meta.json`

## Quickstart
```bash
# 1) Train the projection (optional but recommended)
python3 train_projection.py --anchors anchors.tsv --method procrustes
# or: python3 train_projection.py --anchors anchors.tsv --method ridge --ridge_lam 1e-3

# 2) Generate samples (uses models/W.npy if present)
python3 demo_generate_lexicon.py
# → zyntalic_words_lexicon_demo.txt
```

## Lexicon Priors
After picking the top-k anchors per token, the generator samples adjectives/nouns/verbs from anchor-weighted lists and chooses mirrored **motif pairs** from those anchors when possible. This nudges tone without quoting.

## Swap in real embeddings
Replace `base_embedding()` and `anchor_vec()` with your preferred model (e.g., e5/BGE) to increase fidelity. Everything else stays the same.

## Guardrails
Use only public-domain or licensed texts in `anchors.tsv`. Lexicons contain generic words; avoid inserting long verbatim passages.
