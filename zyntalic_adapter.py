# -*- coding: utf-8 -*-
"""Unifies text generation across engines; falls back to rule-based translator."""
from typing import Optional

def generate_text(src: str, *, mode: str = "plain") -> str:
    # 1) preferred: Saramago-style chiasmus engine
    try:
        import zynthalic_chiasmus as zch
        if hasattr(zch, "translate_saramago_chiasmus"):
            return zch.translate_saramago_chiasmus(src)
    except Exception:
        pass

    # 2) optional: pretty publisher HTML
    if mode == "html":
        try:
            import zynthalic_publisher as pub
            if hasattr(pub, "publish_html"):
                return pub.publish_html(src)
            if hasattr(pub, "publish_book"):  # fallback if publish_html not present
                return pub.publish_book(src, filename=None)  # ensure it returns a string
        except Exception:
            pass

    # 3) fallback: rule-based translator (no embeddings UI noise)
    try:
        from webapp.translator import ZyntalicTranslator
        tr = ZyntalicTranslator(mirror_rate=0.8)
        rows = tr.translate_text(src)
        return "\n".join(r["target"] for r in rows)
    except Exception:
        # last resort: return the raw text
        return src
