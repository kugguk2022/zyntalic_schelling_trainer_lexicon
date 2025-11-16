# -*- coding: utf-8 -*-
"""
Single-file English → Zynthalic translator.
- Prefers: zynthalic_chiasmus.translate_chiasmus(text)
- Fallback: rule-based mapping (Hangul token surface + mirrored line + context)
- Exposes: CLI and FastAPI (uvicorn zynthalic_onefile:app --reload)
"""

import io, re, sys, json, random

# ---------- PREFERRED ENGINE ----------
def _preferred_translate(text: str) -> str:
    # Your repo already has this file/function. If it fails, we fall back.
    # (We saw zynthalic_chiasmus.py in your repo.)  # noqa
    try:
        import zynthalic_chiasmus as zc  # from your repo
        if hasattr(zc, "translate_chiasmus"):
            return zc.translate_chiasmus(text)
    except Exception:
        pass
    return ""

# ---------- FALLBACK (rule-based) ----------
CHOSEONG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

def _fallback_make_context(lemma, anchors, pos_hint):
    labs = ";".join(anchors)
    return f"⟦ctx: lemma={lemma}; pos≈{pos_hint}; anchors={labs}⟧"

def _fallback_generate_word():
    return "".join(random.choice(CHOSEONG) for _ in range(3))

def _fallback_base_embedding(s: str, dim: int = 64):
    r = random.Random(hash(s) & 0xFFFFFFFF)
    return [r.random() for _ in range(dim)]

def _fallback_anchor_weights_for_vec(v, top_k=3):
    names = ["Homer_Iliad", "Homer_Odyssey", "Plato_Rep", "Shakespeare", "Dante", "Darwin"]
    r = random.Random(int(sum(v) * 1e6) & 0xFFFFFFFF)
    ws = [r.random() for _ in names]
    S = sum(ws) or 1.0
    pairs = list(zip(names, [w / S for w in ws]))
    pairs.sort(key=lambda x: x[1], reverse=True)
    return pairs[:top_k]

def _fallback_plain_line(anchor_names, weights):
    return "The thread turns once more; the witness remains."

def _fallback_mirrored_line(anchor_names, weights):
    A = anchor_names[0] if anchor_names else "order"
    B = anchor_names[1] if len(anchor_names) > 1 else "chaos"
    return f"To {A} through {B}; to {B} through {A}."

def _fallback_translate(text: str, mirror_rate: float = 0.8) -> str:
    parts = [p.strip() for p in _SENT_SPLIT.split(text) if p and p.strip()]
    out = []
    for sent in parts:
        v = _fallback_base_embedding(sent)
        aw = _fallback_anchor_weights_for_vec(v, top_k=3)
        anchor_names = [a for a, _ in aw]
        weights = [w for _, w in aw]
        # surface tokens
        toks = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", sent)
        z_words = [_fallback_generate_word() for _ in toks]
        z_surface = " ".join(z_words) if z_words else _fallback_plain_line(anchor_names, weights)
        # core mirrored vs plain
        core = _fallback_mirrored_line(anchor_names, weights) if random.random() < mirror_rate else _fallback_plain_line(anchor_names, weights)
        # context at end
        lemma = z_words[0] if z_words else "ø"
        pos_hint = "noun" if any(ch in lemma for ch in CHOSEONG) else "verb"
        ctx = _fallback_make_context(lemma, anchor_names, pos_hint)
        out.append(f"{z_surface}. {core} {ctx}")
    return "\n".join(out)

def translate(text: str, mirror_rate: float = 0.8) -> str:
    s = (text or "").strip()
    if not s:
        return ""
    # Try the real engine first
    out = _preferred_translate(s)
    if out:
        return out
    # Fallback
    return _fallback_translate(s, mirror_rate=mirror_rate)

# ---------- FASTAPI APP (optional) ----------
try:
    from fastapi import FastAPI, UploadFile, File, Form
    from fastapi.responses import PlainTextResponse, HTMLResponse
    from pypdf import PdfReader
    HAVE_WEB = True
except Exception:
    HAVE_WEB = False

if HAVE_WEB:
    app = FastAPI()

    @app.post("/translate_text", response_class=PlainTextResponse)
    async def translate_text(text: str = Form(...), mirror_rate: float = Form(0.8)):
        return translate(text, mirror_rate=mirror_rate)

    @app.post("/translate_pdf", response_class=PlainTextResponse)
    async def translate_pdf(pdf: UploadFile = File(...), mirror_rate: float = Form(0.8)):
        data = await pdf.read()
        reader = PdfReader(io.BytesIO(data))
        txt = []
        for p in reader.pages:
            t = p.extract_text() or ""
            txt.append(t)
        return translate("\n".join(txt), mirror_rate=mirror_rate)

# ---------- CLI ----------
def _cli():
    import argparse, pathlib
    ap = argparse.ArgumentParser(description="English → Zynthalic translator (single-file).")
    ap.add_argument("input", nargs="?", help="TXT file (default: stdin)")
    ap.add_argument("-o", "--out", help="Output file (default: stdout)")
    ap.add_argument("--mirror", type=float, default=0.8, help="Mirror rate 0..1")
    args = ap.parse_args()

    if args.input:
        text = pathlib.Path(args.input).read_text(encoding="utf-8", errors="ignore")
    else:
        text = sys.stdin.read()

    out = translate(text, mirror_rate=args.mirror)

    if args.out:
        pathlib.Path(args.out).write_text(out, encoding="utf-8")
    else:
        sys.stdout.write(out)

if __name__ == "__main__":
    _cli()
