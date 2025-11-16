# Zyntalic Schelling Trainer

A professional language translation system that aligns Zyntalic's internal embeddings to cultural Schelling points (great-book anchors) and generates translations using **anchor-specific lexicons**, while maintaining core linguistic rules.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Core Features

- **Cultural Anchor System**: Aligns translations to 20+ classical literary works (Homer, Plato, Shakespeare, Dante, etc.)
- **Linguistic Rules**: 
  - Hangul syllables for nouns (85%)
  - Polish-based morphology for verbs (85%)
  - Mirrored meanings (chiasmus patterns)
  - Deferred context placement at sentence end
- **Lexicon Priors**: Anchor-specific word banks influence tone without copying source material
- **Flexible Architecture**: Works offline with NumPy, supports modern embedding backends
- **Production-Ready Web API**: FastAPI server with PDF support and comprehensive error handling

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install core dependencies
pip install -e .

# Install web application dependencies
pip install -e ".[webapp]"

# Install all dependencies (including dev tools)
pip install -e ".[all]"
```

### Basic Usage

#### Command Line Interface

```bash
# Generate sample translations
python demo_generate_lexicon.py

# Train projection model (optional, improves quality)
python train_projection.py --anchors anchors.tsv --method procrustes
```

#### Web Application

```bash
# Start the web server
cd webapp
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Then navigate to `http://localhost:8000` to access the web interface.

#### API Endpoints

- `GET /` - Web interface
- `POST /translate` - Translate text or PDF
- `GET /download?path=<filename>` - Download generated files
- `GET /health` - Health check endpoint

### Translation Example

```python
from zyntalic_adapter import generate_text

text = "The path of wisdom leads through understanding."
translated = generate_text(text, mirror_rate=0.8)
print(translated)
```

## Project Structure

```
.
├── zyntalic_core.py           # Core translation engine
├── zyntalic_adapter.py        # Unified text generation interface
├── webapp/
│   ├── app.py                 # FastAPI web application
│   ├── translator.py          # Translation logic
│   ├── requirements.txt       # Web dependencies
│   ├── static/                # CSS and static assets
│   └── templates/             # HTML templates
├── lexicon/                   # Anchor-specific word banks (JSON)
├── models/                    # Trained projection matrices
├── outputs/                   # Generated translations
├── tests/                     # Test suite
├── config.py                  # Configuration management
├── pyproject.toml            # Package metadata
└── README.md                 # This file
```

## Core Components

### Zyntalic Rules

1. **Token Generation**: Nouns use Hangul syllables (85%), verbs use Polish morphology (85%)
2. **Mirrored Meanings**: Chiasmus patterns by default (A→B || B→A)
3. **Context Placement**: Linguistic context appears at sentence end
4. **Cultural Anchors**: 20 classical works influence tone and word choice

### Lexicon System

Each anchor has associated word banks (adjectives, nouns, verbs) and motif pairs that influence translation tone without copying source material.

### Projection Training

Optional Procrustes/Ridge projection aligns base embeddings to cultural anchors for improved quality:

```bash
python train_projection.py --anchors anchors.tsv --method procrustes
```

## Configuration

Environment variables can be set to customize behavior:

- `ZYNTALIC_HOST` - Web server host (default: 0.0.0.0)
- `ZYNTALIC_PORT` - Web server port (default: 8000)
- `ZYNTALIC_DEBUG` - Enable debug mode (default: false)
- `ZYNTALIC_LOG_LEVEL` - Logging level (default: INFO)

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format and lint code
ruff check .
ruff format .
```

## License

MIT License - see LICENSE file for details.

## Citation

If you use this work in your research, please cite:

```
@software{zyntalic2025,
  title={Zyntalic Schelling Trainer},
  author={kugguk2022},
  year={2025},
  url={https://github.com/kugguk2022/zyntalic_schelling_trainer_lexicon}
}
```
