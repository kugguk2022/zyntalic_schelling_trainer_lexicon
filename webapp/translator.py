# -*- coding: utf-8 -*-
"""
Webapp-facing translator shim. We forward to the core ZyntalicTranslator so the
FastAPI app and CLI share the same S-O-V-C + Korean-tail behaviour.
"""
from zyntalic_translator import ZyntalicTranslator

__all__ = ["ZyntalicTranslator"]

