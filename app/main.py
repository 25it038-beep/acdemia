"""Root-level shim so `gunicorn app.main:app` works when Render runs from the repo root.

The real FastAPI application lives in backend/app. Render's web service runs the
start command from the repository root (unless a Root Directory is configured), so
this package redirects the `app` package to backend/app.
"""

import os
import sys

_BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, _BACKEND_DIR)

# Drop any partially-loaded copies of the root shim so the real backend package is imported
for name in [n for n in list(sys.modules) if n == "app" or n.startswith("app.")]:
    del sys.modules[name]

from app.main import app  # noqa: E402
