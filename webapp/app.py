# -*- coding: utf-8 -*-
import os, io, re, json, subprocess, tempfile
from typing import List
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from pypdf import PdfReader

# Adjust these paths if you run the app from another cwd
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANCHORS_TSV = os.path.join(REPO_ROOT, "anchors.tsv")
LEXICON_DIR = os.path.join(REPO_ROOT, "lexicon")
MODELS_DIR = os.path.join(REPO_ROOT, "models")
OUT_DIR = os.path.join(REPO_ROOT, "outputs")
os.makedirs(LEXICON_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# import after sys.path tweak so we can call generator directly
import sys
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
from zyntalic_core import generate_words, export_to_txt  # uses models/W.npy if present

app = FastAPI()

HTML_FORM = """
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Zyntalic PDF → Output</title></head>
  <body style="font-family:sans-serif;max-width:900px;margin:2rem auto;">
    <h2>Upload a book (PDF) → anchor → train → generate Zyntalic</h2>
    <form action="/upload" method="post" enctype="multipart/form-data">
      <label>Anchor ID (e.g., Dante_DivineComedy):</label><br/>
      <input type="text" name="anchor_id" required style="width:420px;"><br/><br/>
      <label>PDF file:</label><br/>
      <input type="file" name="pdf" accept="application/pdf" required><br/><br/>
      <label>Max excerpts from PDF (lines for anchors.tsv, default 400):</label><br/>
      <input type="number" name="max_excerpts" value="400"><br/><br/>
      <label>Chars per excerpt (min..max, default 300..600):</label><br/>
      <input type="text" name="excerpt_span" value="300,600"><br/><br/>
      <label>Generate how many Zyntalic rows (default 5000):</label><br/>
      <input type="number" name="n_rows" value="5000"><br/><br/>
      <button type="submit">Run</button>
    </form>
    <p style="margin-top:1rem;color:#666">
      Note: only use public-domain/licensed PDFs. This pipeline stores short excerpts for anchors and lexicons.
    </p>
  </body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_FORM

def _extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    parts = []
    for p in reader.pages:
        t = p.extract_text() or ""
        parts.append(t)
    # Simple whitespace normalization
    text = re.sub(r"[ \t]+", " ", "\n".join(parts)).strip()
    return text

def _to_excerpts(text: str, min_len=300, max_len=600, cap=400) -> List[str]:
    # Split into rough sentences/paras and pack windows in [min_len, max_len]
    raw = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
    buf, out = "", []
    for piece in raw:
        piece = piece.strip()
        if not piece:
            continue
        if len(buf) + 1 + len(piece) <= max_len:
            buf = (buf + " " + piece).strip()
        else:
            if len(buf) >= min_len:
                out.append(buf)
            buf = piece
            if len(buf) > max_len:
                out.append(buf[:max_len])
                buf = ""
        if len(out) >= cap:
            break
    if buf and len(out) < cap:
        out.append(buf[:max_len])
    return out[:cap]

def _append_anchors(anchor_id: str, excerpts: List[str], path=ANCHORS_TSV):
    mode = "a" if os.path.exists(path) else "w"
    with open(path, mode, encoding="utf-8") as f:
        for ex in excerpts:
            # each row: anchor_id<TAB>excerpt
            f.write(f"{anchor_id}\t{ex}\n")

def _run(cmd: list):
    # Runs a Python script in this repo
    p = subprocess.run([sys.executable] + cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    ok = (p.returncode == 0)
    return ok, p.stdout + ("\n" + p.stderr if p.stderr else "")

@app.post("/upload")
async def upload(
    anchor_id: str = Form(...),
    pdf: UploadFile = Form(...),
    max_excerpts: int = Form(400),
    excerpt_span: str = Form("300,600"),
    n_rows: int = Form(5000),
):
    fb = await pdf.read()
    text = _extract_pdf_text(fb)
    lo, hi = (300, 600)
    try:
        lo, hi = [int(x.strip()) for x in excerpt_span.split(",")]
    except Exception:
        pass
    excerpts = _to_excerpts(text, min_len=lo, max_len=hi, cap=max_excerpts)
    if not excerpts:
        return PlainTextResponse("No text extracted from PDF.", status_code=400)

    _append_anchors(anchor_id, excerpts, ANCHORS_TSV)

    # 1) build/merge lexicons from anchors
    ok, logs = _run(["lexicon_from_tsv.py", "--anchors", "anchors.tsv", "--out", "lexicon", "--topk", "24", "--merge"])
    if not ok:
        return PlainTextResponse("lexicon_from_tsv.py failed:\n" + logs, status_code=500)

    # 2) train projection W (Procrustes)
    ok, logs = _run(["train_projection.py", "--anchors", "anchors.tsv", "--method", "procrustes"])
    if not ok:
        return PlainTextResponse("train_projection.py failed:\n" + logs, status_code=500)

    # 3) generate Zyntalic output (uses models/W.npy if present)
    entries = generate_words(n_rows, use_projection=True)
    out_path = os.path.join(OUT_DIR, f"zyntalic_words_{anchor_id}.txt")
    export_to_txt(entries, out_path)

    # Return a very simple HTML result with a download link
    name = os.path.basename(out_path)
    return HTMLResponse(f"""
      <html><body style="font-family:sans-serif;max-width:900px;margin:2rem auto;">
        <h3>Done</h3>
        <p>Appended ~{len(excerpts)} excerpts for <b>{anchor_id}</b> to anchors.tsv, merged lexicons, trained W, and generated {n_rows} rows.</p>
        <ul>
          <li><a href="/download?file={name}">Download {name}</a></li>
          <li><a href="/download?file=anchors.tsv">Download anchors.tsv</a></li>
        </ul>
        <p><a href="/">Back</a></p>
      </body></html>
    """)

@app.get("/download")
def download(file: str):
    if file == "anchors.tsv":
        path = ANCHORS_TSV
    else:
        path = os.path.join(OUT_DIR, file)
    if not os.path.exists(path):
        return PlainTextResponse("Not found", status_code=404)
    return FileResponse(path, filename=os.path.basename(path))
