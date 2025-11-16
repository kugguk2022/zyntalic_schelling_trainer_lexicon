# Zyntalic Development Guide

## Architecture Overview

### Core Modules

#### `zyntalic_core.py`
- Core translation engine
- Hangul/Polish token generation
- Anchor-based embeddings
- Lexicon loading and management

#### `zyntalic_adapter.py`
- Unified interface for text generation
- Fallback translator with proper rule enforcement
- Multiple engine support (chiasmus, publisher, translator)

#### `webapp/translator.py`
- Sentence-level translation
- Token mapping with consistency
- Anchor weight calculation

### Translation Pipeline

1. **Input Processing**: Text/PDF → Sentence segmentation
2. **Anchor Selection**: Cultural anchor assignment per sentence
3. **Token Generation**: English → Zyntalic tokens (Hangul/Polish)
4. **Mirroring**: Apply chiasmus patterns (A→B || B→A)
5. **Context Addition**: Append deferred context at sentence end

## Adding New Features

### Adding a New Cultural Anchor

1. Add anchor name to `config.py` ANCHORS list
2. Create lexicon file at `lexicon/<anchor_name>.json`:

```json
{
  "adjectives": ["word1", "word2"],
  "nouns": ["word3", "word4"],
  "verbs": ["word5", "word6"],
  "motifs": [["concept1", "concept2"], ["concept3", "concept4"]]
}
```

3. Add raw text to `raw_anchors/<anchor_name>.txt`
4. Run training: `python train_projection.py --anchors anchors.tsv`

### Extending the Web API

Add new endpoints in `webapp/app.py`:

```python
@app.get("/custom-endpoint")
async def custom_endpoint(request: Request):
    # Your implementation
    return {"status": "success"}
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_smoke.py::test_basic_translation
```

### Writing Tests

Create test files in `tests/` directory:

```python
def test_feature():
    from zyntalic_core import generate_word
    word = generate_word()
    assert len(word) > 0
    assert any(c in word for c in "ㄱㄴㄷ")  # Has Hangul
```

## Deployment

### Production Deployment

1. **Environment Setup**:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[webapp]"
```

2. **Configuration**:
```bash
export ZYNTALIC_HOST=0.0.0.0
export ZYNTALIC_PORT=8000
export ZYNTALIC_DEBUG=false
export ZYNTALIC_LOG_LEVEL=INFO
```

3. **Start Server**:
```bash
python webapp/run.py
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install -e ".[webapp]"

EXPOSE 8000

CMD ["python", "webapp/run.py"]
```

Build and run:

```bash
docker build -t zyntalic .
docker run -p 8000:8000 zyntalic
```

## Performance Optimization

### Caching

Lexicon data is cached in memory after first load. To invalidate:

```python
from zyntalic_core import _LEXICON_CACHE
_LEXICON_CACHE = None
```

### Batch Processing

For large documents, process in batches:

```python
def translate_large_text(text, batch_size=1000):
    sentences = text.split('.')
    for i in range(0, len(sentences), batch_size):
        batch = sentences[i:i+batch_size]
        yield translate_batch(batch)
```

## Troubleshooting

### Common Issues

**Import Errors**: Ensure you're running from repo root or PYTHONPATH is set correctly

**PDF Extraction Fails**: Install pypdf: `pip install pypdf`

**Server Won't Start**: Check port availability: `netstat -an | grep 8000`

**Poor Translation Quality**: Train projection model: `python train_projection.py`

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `pytest tests/`
5. Format code: `ruff format .`
6. Submit pull request

## Code Style

- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to all functions
- Maximum line length: 100 characters
- Use `ruff` for linting and formatting

## Logging

Use structured logging:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Processing started", extra={"user": "username"})
logger.warning("Unusual condition", extra={"value": x})
logger.error("Operation failed", exc_info=True)
```
