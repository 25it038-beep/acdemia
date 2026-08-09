"""Render autofill compatibility: `uvicorn main:app --host 0.0.0.0 --port $PORT`.

The real FastAPI application lives in backend/app. Render's autofill sometimes
defaults to `uvicorn main:app`, so expose the app at the root.
"""

import os
import sys

_BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, _BACKEND_DIR)

for name in [n for n in list(sys.modules) if n == "app" or n.startswith("app.")]:
    del sys.modules[name]

from app.main import app  # noqa: E402