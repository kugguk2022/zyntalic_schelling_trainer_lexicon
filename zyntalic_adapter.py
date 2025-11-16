# -*- coding: utf-8 -*-
"""Unified text generation adapter.
Prefers the Zynthalic text engines; falls back to rule-based translator.
"""
from typing import Optional

def generate_text(src: str, *, mode: str = "plain", mirror_rate: float = 0.8) -> str:
    # 1) Preferred: Saramago-style chiasmus engine
    try:
        import zynthalic_chiasmus as zch
        if hasattr(zch, "translate_saramago_chiasmus"):
            return zch.translate_saramago_chiasmus(src)
    except Exception:
        pass

    # 2) Pretty publisher HTML (if requested)
    if mode == "html":
        try:
            import zynthalic_publisher as pub
            if hasattr(pub, "publish_html"):
                return pub.publish_html(src)
            if hasattr(pub, "publish_book"):
                out = pub.publish_book(src, filename=None)
                if isinstance(out, str):
                    return out
        except Exception:
            pass

    # 3) Rule-based fallback
    try:
        from webapp.translator import ZyntalicTranslator
        tr = ZyntalicTranslator(mirror_rate=mirror_rate)
        rows = tr.translate_text(src)
        return "\n".join(r["target"] for r in rows)
    except Exception:
        return src
