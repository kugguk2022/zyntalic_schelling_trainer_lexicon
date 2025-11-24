import importlib
import json
from pathlib import Path

import numpy as np
import pytest

DATA_PATH = Path("data/persepolis_clean.jsonl")


def test_imports():
    importlib.import_module("zyntalic_translator")
    importlib.import_module("zyntalic_cli")
    importlib.import_module("zyntalic_core")


def test_embedding_determinism():
    """Embeddings must be identical across runs."""
    from zyntalic_embeddings import embed_text

    text = "The old man looked at the sea."
    results = [embed_text(text, dim=300) for _ in range(10)]

    arr = np.array(results)
    assert np.allclose(arr, arr[0]), "Embeddings must be deterministic"


def test_normalized_data_structure():
    """Normalized JSONL must have required fields."""
    if not DATA_PATH.exists():
        pytest.skip(f"{DATA_PATH} is missing; skipping normalized structure check")

    with DATA_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            assert "source" in row
            assert "target" in row
            assert "lemma" in row
            assert "anchors" in row
            # Target must NOT contain the old corrupted ctx marker
            assert "�Y�ctx:" not in row["target"]
            break  # Just check first line


if __name__ == "__main__":
    test_embedding_determinism()
    test_normalized_data_structure()
    print("�o. All determinism tests passed")
