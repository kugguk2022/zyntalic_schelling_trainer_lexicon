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
# ---------- FASTAPI APP (Codex UI) ----------
try:
    from fastapi import FastAPI, UploadFile, File, Form
    from fastapi.responses import PlainTextResponse, HTMLResponse
    from pypdf import PdfReader
    HAVE_WEB = True
except Exception:
    HAVE_WEB = False

# helper: sentence split and tokenization
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_WORDS = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+")

def _sentences(text: str):
    return [p.strip() for p in _SENT_SPLIT.split(text or "") if p and p.strip()]

def _tokens(s: str):
    return _WORDS.findall(s)

# engines (we’ll try to use real core if available)
def _core_funcs():
    try:
        import zyntalic_core as zc  # if present in your repo
        return {
            "base_embedding": getattr(zc, "base_embedding"),
            "anchor_weights_for_vec": getattr(zc, "anchor_weights_for_vec"),
            "generate_word": getattr(zc, "generate_word", _fallback_generate_word),
        }
    except Exception:
        return {
            "base_embedding": _fallback_base_embedding,
            "anchor_weights_for_vec": _fallback_anchor_weights_for_vec,
            "generate_word": _fallback_generate_word,
        }

def build_codex_html(src_text: str, mirror_rate: float = 0.8) -> str:
    """Builds the two-column codex with tooltips and sigils."""
    src_text = (src_text or "").strip()
    if not src_text:
        return "<p>No text provided.</p>"

    core = _core_funcs()
    lex_map = {}  # English token -> Zynthalic token (stable within page)
    sigils = ["컁","옹","냊","얍","뱅","칩"]  # lightweight “structure” markers

    english_paras = []
    zynthalic_paras = []

    for si, sent in enumerate(_sentences(src_text)):
        # anchors per sentence
        v = core["base_embedding"](sent)
        aw = core["anchor_weights_for_vec"](v, top_k=3)
        anchors = [a for a, _ in aw] or ["Unknown Root"]

        # 1) English column: just keep the sentence
        english_paras.append(sent)

        # 2) Zynthalic column: token map + tooltip (origin = top anchor)
        z_tokens = []
        top_anchor = anchors[0]
        for tok in _tokens(sent):
            key = tok.lower()
            if key not in lex_map:
                lex_map[key] = core["generate_word"]()
            zt = lex_map[key]
            z_tokens.append(
                f'<span class="word" data-origin="{tok} → {top_anchor}">{zt}</span>'
            )

        # mirrored/ironic line marker at end
        sigil = sigils[si % len(sigils)]
        z_line = " ".join(z_tokens) + f' <span class="sigil" title="Structure: Irony">{sigil}</span>'
        zynthalic_paras.append(z_line)

    # HTML shell (your Codex layout)
    css = """
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Noto+Serif+KR:wght@400;700&display=swap');
        body{background:#f4f1ea;color:#2c2c2c;font-family:'Cormorant Garamond',serif;margin:0;padding:40px;display:flex;justify-content:center}
        .container{max-width:1000px;width:100%;display:grid;grid-template-columns:1fr 1fr;gap:60px;border-left:1px solid #dcdcdc;padding-left:40px}
        h1{grid-column:1/-1;text-align:center;font-weight:400;letter-spacing:4px;text-transform:uppercase;margin-bottom:60px;color:#8b0000}
        .english-col{color:#666;line-height:1.8;font-size:18px;text-align:justify}
        .zynthalic-col{color:#000;line-height:1.8;font-size:19px;text-align:justify;font-style:italic}
        .sigil{font-family:'Noto Serif KR',serif;font-weight:bold;color:#8b0000;font-style:normal;margin-left:8px;cursor:help;font-size:1.2em}
        .word{position:relative;cursor:pointer;text-decoration:none;border-bottom:1px dotted #aaa}
        .word:hover{color:#8b0000;border-bottom:1px solid #8b0000}
        .word:hover::after{content:attr(data-origin);position:absolute;bottom:100%;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:5px 10px;border-radius:4px;font-size:12px;font-family:sans-serif;font-style:normal;white-space:nowrap;z-index:10;box-shadow:0 4px 6px rgba(0,0,0,0.1)}
        .footer{grid-column:1/-1;margin-top:80px;border-top:1px solid #ccc;padding-top:20px;font-size:12px;text-align:center;color:#888}
        form{grid-column:1/-1;margin-bottom:28px}
        textarea{width:100%;height:160px}
    """
    import html as _html
    eng_html = "".join(f"<p>{_html.escape(p)}</p>" for p in english_paras)
    zyn_html = "".join(f"<p>{p}</p>" for p in zynthalic_paras)

    page = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"><title>Zynthalic Codex</title>
<style>{css}</style>
</head>
<body>
<div class="container">
  <h1>The Zynthalic Codex</h1>

  <!-- quick input forms on top of page -->
  <form method="post" action="/codex_text">
    <label>Paste English and render Codex:</label><br>
    <textarea name="text" placeholder="Paste English here...">{_html.escape(src_text)}</textarea><br>
    <label>Mirror rate:</label> <input type="number" step="0.05" min="0" max="1" name="mirror_rate" value="{mirror_rate}">
    <button type="submit">Render</button>
  </form>
  <form method="post" action="/codex_pdf" enctype="multipart/form-data">
    <label>Or upload PDF:</label>
    <input type="file" name="pdf" accept="application/pdf" required>
    <label>Mirror rate:</label> <input type="number" step="0.05" min="0" max="1" name="mirror_rate" value="{mirror_rate}">
    <button type="submit">Render PDF</button>
  </form>

  <div class="english-col">{eng_html}</div>
  <div class="zynthalic-col">{zyn_html}</div>

  <div class="footer">Generated by Zynthalic Codex | {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</div>
</div>
</body>
</html>"""
    return page

if HAVE_WEB:
    app = FastAPI()

    @app.get("/health", response_class=PlainTextResponse)
    async def health():
        return "ok"

    @app.get("/", response_class=HTMLResponse)
    async def home():
        # empty codex page with sample text prompt
        return build_codex_html("The old man looked at the sea.\nThe sea looked back at him.\nWar is a cruel master, but peace is a gentle lie.")

    @app.post("/codex_text", response_class=HTMLResponse)
    async def codex_text(text: str = Form(...), mirror_rate: float = Form(0.8)):
        return build_codex_html(text, mirror_rate=mirror_rate)

    @app.post("/codex_pdf", response_class=HTMLResponse)
    async def codex_pdf(pdf: UploadFile = File(...), mirror_rate: float = Form(0.8)):
        data = await pdf.read()
        reader = PdfReader(io.BytesIO(data))
        txt = []
        for p in reader.pages:
            t = p.extract_text() or ""
            txt.append(t)
        return build_codex_html("\n".join(txt), mirror_rate=mirror_rate)

    # Keep plain endpoints too
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
