# Zyntalic Schelling Trainer (with Lexicon Priors)

A tiny, dependency-light scaffold that aligns Zyntalic’s internal embeddings to cultural Schelling points (great-book anchors) and bends surface style using **anchor-specific lexicons**, while keeping your rules (Hangul+Polish tokens, mirrored meanings by default, and deferred context).

## Highlights
- Anchor-specific lexicon priors tilt tone without copying source passages.
- Thin Procrustes/Ridge projection keeps your base embedding while nudging toward curated anchors.
- Works offline with NumPy only, but can swap in modern embedding backends when you need fidelity.
- Ships with CLIs, demos, and a FastAPI surface for quick inspection.

## Repository layout
- `zyntalic_core.py` — generator + embeddings + lexicon prior + optional projection `models/W.npy`.
- `train_projection.py` — trains thin projection **W** (Procrustes or Ridge) from `anchors.tsv`.
- `anchors.tsv` — template with `(anchor_id, excerpt)` rows (replace with curated/authorized text).
- `lexicon/*.json` — per-anchor wordlists and mirrored motifs (safe generic terms; extend freely).
- `demo_generate.py` / `demo_generate_lexicon.py` — quick CLI demos for sampling outputs.
- `Zynthalic_onefile.py` — FastAPI/UVicorn surface for browser-based inspection.
- `models/` — output folder for `W.npy` and `meta.json`.

## Environment setup
```bash
python -m venv .venv
source .venv/bin/activate  # or: .venv\Scripts\activate on Windows
pip install -e .           # add [embed] extra to pull sentence-transformers
```

## Train + sample (CLI quickstart)
```bash
# 1) Train the projection (optional but recommended)
python train_projection.py --anchors anchors.tsv --method procrustes
# or: python train_projection.py --anchors anchors.tsv --method ridge --ridge_lam 1e-3

# 2) Generate samples (uses models/W.npy if present)
python demo_generate_lexicon.py
# → zyntalic_words_lexicon_demo.txt
```

## FastAPI surface demo
```bash
pip install fastapi uvicorn pypdf python-multipart
uvicorn zynthalic_onefile:app --reload
```
Then open `http://127.0.0.1:8000/` for the interface or hit `http://127.0.0.1:8000/health` for a plain-text readiness probe.

## Lexicon priors
After picking the top-k anchors per token, the generator samples adjectives/nouns/verbs from anchor-weighted lists and chooses mirrored **motif pairs** from those anchors when possible. This nudges tone without quoting.

## Swap in real embeddings
Replace `base_embedding()` and `anchor_vec()` with your preferred model (e5, BGE, etc.) to increase fidelity. Everything else stays the same.

## Guardrails
Use only public-domain or licensed texts in `anchors.tsv`. Lexicons contain generic words; avoid inserting long verbatim passages.
