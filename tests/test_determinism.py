cat > tests/test_determinism.py << 'EOF'
import json
import numpy as np

def test_embedding_determinism():
    """Embeddings must be identical across runs."""
    from zyntalic_embeddings import embed_text
    
    text = "The old man looked at the sea."
    results = [embed_text(text, dim=300) for _ in range(10)]
    
    # Convert to numpy for easy comparison
    arr = np.array(results)
    assert np.allclose(arr, arr[0]), "Embeddings must be deterministic"

def test_normalized_data_structure():
    """Normalized JSONL must have required fields."""
    with open("data/persepolis_clean.jsonl", "r") as f:
        for line in f:
            row = json.loads(line)
            assert "source" in row
            assert "target" in row
            assert "lemma" in row
            assert "anchors" in row
            # Target must NOT contain ⟦ctx:
            assert "⟦ctx:" not in row["target"]
            break  # Just check first line

def test_embedding_determinism():
    """Embeddings must be identical across runs."""
    from zyntalic_embeddings import embed_text
    
    text = "The old man looked at the sea."
    results = [embed_text(text, dim=300) for _ in range(10)]
    
    # Convert to numpy for easy comparison
    arr = np.array(results)
    assert np.allclose(arr, arr[0]), "Embeddings must be deterministic"

def test_normalized_data_structure():
    """Normalized JSONL must have required fields."""
    with open("data/persepolis_clean.jsonl", "r") as f:
        for line in f:
            row = json.loads(line)
            assert "source" in row
            assert "target" in row
            assert "lemma" in row
            assert "anchors" in row
            # Target must NOT contain ⟦ctx:
            assert "⟦ctx:" not in row["target"]
            break  # Just check first line

if __name__ == "__main__":
    test_embedding_determinism()
    test_normalized_data_structure()
    print("✅ All determinism tests passed")

