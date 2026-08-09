"""Render autofill compatibility: `gunicorn your_application.wsgi`.

Render's default (autofilled) Start Command for Python services is
`gunicorn your_application.wsgi`, run from the repository root. The real
FastAPI application lives in backend/app, so expose it as `wsgi` here.
"""

import os
import sys

_BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, _BACKEND_DIR)

# Drop any partially-loaded copies of the root shims so the real backend package is imported
for name in [n for n in list(sys.modules) if n == "app" or n.startswith("app.")]:
    del sys.modules[name]

from app.main import app as wsgi  # noqa: E402
