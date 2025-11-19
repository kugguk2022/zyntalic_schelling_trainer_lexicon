# -*- coding: utf-8 -*-
"""Unified text generation adapter.
Order of preference:
1) zynthalic_chiasmus.translate_chiasmus (correct function per repo)
2) zynthalic_chiasmus.translate_saramago_chiasmus (legacy/alternate)
3) zynthalic_publisher.publish_html / publish_book (HTML)
4) rule-based translator fallback (no embeddings dump)
"""

def generate_text(src: str, *, mode: str = "plain", mirror_rate: float = 0.8) -> str:
    # 1) Preferred: correct function name
    try:
        import zynthalic_chiasmus as zch
        if hasattr(zch, "translate_chiasmus"):
            return zch.translate_chiasmus(src)
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
            if hasattr(pub, "publish_book"):
                out = pub.publish_book(src, filename=None)
                if isinstance(out, str):
                    return out
        except Exception:
            pass

    # 3) fallback: rule-based translator (no embeddings UI noise)
    try:
        from webapp.translator import ZyntalicTranslator
        tr = ZyntalicTranslator(mirror_rate=mirror_rate)
        rows = tr.translate_text(src)
        return "\n".join(r["target"] for r in rows)
    except Exception:
        # last resort: return the raw text
        return src
