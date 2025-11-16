# -*- coding: utf-8 -*-
import os, io, re, json
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pypdf import PdfReader

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO_ROOT, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

import sys
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from zyntalic_adapter import generate_text
from webapp.translator import ZyntalicTranslator

app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    parts = []
    for p in reader.pages:
        t = p.extract_text() or ""
        parts.append(t)
    return re.sub(r"[ \t]+", " ", "\n".join(parts)).strip()

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/translate", response_class=HTMLResponse)
async def translate(request: Request, pdf: UploadFile = File(...), mirror_rate: float = Form(0.8), pretty: str = Form("0")):
    fb = await pdf.read()
    text = extract_pdf_text(fb)
    if not text:
        return HTMLResponse("<p>No text extracted.</p>", status_code=400)

    mode = "html" if (pretty in ["1", "true", "on"]) else "plain"
    out = generate_text(text, mode=mode, mirror_rate=mirror_rate)

    # Also produce a small parallel corpus for download
    tr = ZyntalicTranslator(mirror_rate=mirror_rate)
    rows = tr.translate_text(text[:200_000])
    base = os.path.splitext(os.path.basename(pdf.filename or "book.pdf"))[0]
    tsv_path = os.path.join(OUT_DIR, f"{base}.zyntalic.tsv")
    jsonl_path = os.path.join(OUT_DIR, f"{base}.zyntalic.jsonl")
    with open(tsv_path, "w", encoding="utf-8") as f:
        f.write("source\ttarget\tanchors\n")
        for r in rows:
            a = ";".join(f"{k}:{w:.3f}" for k,w in r["anchors"])
            f.write(f"{r['source']}\t{r['target']}\t{a}\n")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return templates.TemplateResponse("result.html", {
        "request": request,
        "content": out,
        "tsv_url": f"/download?path={os.path.basename(tsv_path)}",
        "jsonl_url": f"/download?path={os.path.basename(jsonl_path)}",
    })

@app.get("/download")
def download(path: str):
    full = os.path.join(OUT_DIR, path)
    if not os.path.exists(full):
        return PlainTextResponse("Not found", status_code=404)
    return FileResponse(full, filename=os.path.basename(full))
