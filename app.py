# Entrypoint shim so `uvicorn app:app` works from the repo root or any cwd.
from webapp.app import app  # noqa: F401
