"""Entry shim for Render's Python runtime.

Render runs `uvicorn main:app` from rootDir (backend/), so this module
bridges to the real FastAPI app at app/main.py.
"""

from app.main import app
