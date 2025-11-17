# -*- coding: utf-8 -*-
"""
Compatibility shim for legacy ``import zynthalic_onefile``.

The canonical single-file app now lives in ``Zyntalic_onefile.py`` (note the
capital Z and the missing ``h``).  Some deployment scripts still reference the
old module path, so we mirror the original module's namespace here to keep
``uvicorn zynthalic_onefile:app`` and similar commands working without any
other changes.
"""
from importlib import import_module as _import_module
import sys as _sys

_CANONICAL_NAME = "Zyntalic_onefile"

try:
    _canonical = _import_module(_CANONICAL_NAME)
except ModuleNotFoundError as exc:  # pragma: no cover - defensive guard
    raise ImportError(
        f"Unable to import '{_CANONICAL_NAME}'. The Zyntalic single-file app "
        "was renamed; make sure the canonical module is present."
    ) from exc

# Mirror every attribute (FastAPI app, CLI entry point, helpers, etc.).
_this_module = _sys.modules[__name__]
_this_module.__dict__.update(_canonical.__dict__)

