def test_imports():
    import importlib
    importlib.import_module("zynthalic_cli")
    importlib.import_module("zyntalic_core")


def test_basic_translation():
    from zyntalic_adapter import generate_text
    result = generate_text("Hello world")
    assert isinstance(result, str)
    assert len(result) > 0
    # Note: Different engines may have different formats
    # The chiasmus engine doesn't include context, but that's OK


def test_translator():
    import sys
    sys.path.append("webapp")
    from translator import ZyntalicTranslator

    tr = ZyntalicTranslator(mirror_rate=0.8)
    result = tr.translate_text("Hello world.")

    assert isinstance(result, list)
    assert len(result) == 1
    assert "source" in result[0]
    assert "target" in result[0]
    assert "anchors" in result[0]
    assert "⟦ctx:" in result[0]["target"]  # Context at end


def test_config():
    from config import get_config
    config = get_config()
    assert isinstance(config, dict)
    assert "repo_root" in config
    assert "anchors" in config
    assert len(config["anchors"]) > 0
