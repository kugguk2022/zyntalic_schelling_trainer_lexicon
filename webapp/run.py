# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

import uvicorn

# Ensure the repo root is importable so the reloader can always locate webapp.app
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from config import WEBAPP_DEBUG, WEBAPP_HOST, WEBAPP_PORT, LOG_LEVEL
except Exception:
    WEBAPP_HOST = os.getenv("ZYNTALIC_HOST", "0.0.0.0")
    WEBAPP_PORT = int(os.getenv("ZYNTALIC_PORT", "8000"))
    WEBAPP_DEBUG = os.getenv("ZYNTALIC_DEBUG", "false").lower() == "true"
    LOG_LEVEL = os.getenv("ZYNTALIC_LOG_LEVEL", "info")

if __name__ == "__main__":
    uvicorn.run(
        "webapp.app:app",
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        reload=WEBAPP_DEBUG,
        log_level=str(LOG_LEVEL).lower(),
    )
