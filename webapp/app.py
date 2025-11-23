# -*- coding: utf-8 -*-
"""
Zyntalic Web Application
FastAPI server for translating text/PDF documents to Zyntalic language
"""
import io
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import PDF library
try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfFileReader as PdfReader
        except ImportError:
            PdfReader = None
            logger.warning("No PDF library found. PDF support disabled.")

# Setup paths
CURRENT_DIR = Path(__file__).parent.absolute()
REPO_ROOT = CURRENT_DIR.parent
OUT_DIR = REPO_ROOT / "outputs"
OUT_DIR.mkdir(exist_ok=True)

# Add parent directory to path for imports
import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Import Zyntalic modules
try:
    from zyntalic_adapter import generate_text
    from webapp.translator import ZyntalicTranslator
except ImportError as e:
    logger.error(f"Failed to import Zyntalic modules: {e}")
    raise

# Initialize FastAPI app
app = FastAPI(title="Zyntalic Translator", version="1.0.0")

# Mount static files and templates
STATIC_DIR = CURRENT_DIR / "static"
TEMPLATES_DIR = CURRENT_DIR / "templates"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from PDF bytes."""
    if PdfReader is None:
        raise HTTPException(
            status_code=501,
            detail="PDF support not available. Install pypdf or PyPDF2.",
        )

    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        parts = []
        for page in reader.pages:
            text = page.extract_text() or ""
            parts.append(text)
        return re.sub(r"[ \t]+", " ", "\n".join(parts)).strip()
    except Exception as e:  # pragma: no cover - runtime guard
        logger.error(f"Error extracting PDF text: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to extract PDF text: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/translate", response_class=HTMLResponse)
async def translate(
    request: Request,
    pdf: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    mirror_rate: float = Form(0.8),
    pretty: int = Form(0),
):
    """Translate PDF or text to Zyntalic language."""

    # Validate inputs
    if not pdf and not text:
        raise HTTPException(
            status_code=400,
            detail="Either 'pdf' file or 'text' must be provided.",
        )

    # Extract text from PDF or use provided text
    if pdf:
        try:
            file_bytes = await pdf.read()
            source_text = extract_pdf_text(file_bytes)
            filename_base = Path(pdf.filename or "document.pdf").stem
        except Exception as e:  # pragma: no cover - runtime guard
            logger.error(f"PDF processing error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    else:
        source_text = text
        filename_base = "text_input"

    if not source_text or not source_text.strip():
        raise HTTPException(status_code=400, detail="No text content to translate.")

    # Limit text length to prevent timeouts
    MAX_LENGTH = 200_000
    if len(source_text) > MAX_LENGTH:
        logger.warning(f"Text truncated from {len(source_text)} to {MAX_LENGTH} characters")
        source_text = source_text[:MAX_LENGTH]

    try:
        # Generate Zyntalic text
        mode = "html" if pretty else "plain"
        translated_text = generate_text(source_text, mode=mode, mirror_rate=mirror_rate)

        # Create detailed translation data
        translator = ZyntalicTranslator(mirror_rate=mirror_rate)
        translation_rows = translator.translate_text(source_text)

        # Save outputs
        tsv_filename = f"{filename_base}.zyntalic.tsv"
        jsonl_filename = f"{filename_base}.zyntalic.jsonl"
        tsv_path = OUT_DIR / tsv_filename
        jsonl_path = OUT_DIR / jsonl_filename

        # Write TSV file
        with open(tsv_path, "w", encoding="utf-8") as f:
            f.write("source\ttarget\tanchors\n")
            for row in translation_rows:
                anchors_str = ";".join(f"{k}:{w:.3f}" for k, w in row["anchors"])
                f.write(f"{row['source']}\t{row['target']}\t{anchors_str}\n")

        # Write JSONL file
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for row in translation_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        logger.info(f"Translation completed: {len(translation_rows)} sentences")

        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "content": translated_text,
                "tsv_url": f"/download?path={tsv_filename}",
                "jsonl_url": f"/download?path={jsonl_filename}",
            },
        )

    except Exception as e:  # pragma: no cover - runtime guard
        logger.error(f"Translation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@app.get("/download")
async def download(path: str):
    """Download generated translation files."""
    # Sanitize path to prevent directory traversal
    safe_path = Path(path).name
    full_path = OUT_DIR / safe_path

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Invalid file path")

    return FileResponse(
        path=str(full_path),
        filename=safe_path,
        media_type="application/octet-stream",
    )
