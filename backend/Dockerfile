# ── Stage 1: Build ───────────────────────────────────────────────────────────
# Python 3.12 — all deps have prebuilt cp312 manylinux wheels; zero Rust/C compilation
FROM python:3.12-slim AS builder

WORKDIR /app

# Only install build essentials needed for asyncpg C extension (has pre-built wheel,
# but libpq-dev is needed at install time on some platforms)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip/setuptools/wheel first — critical to resolve cp312 manylinux wheels correctly
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --only-binary=:all: \
        pydantic pydantic-core pydantic-settings \
        numpy scikit-learn lxml Pillow grpcio cryptography bcrypt asyncpg websockets && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    libmagic1 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

# Production: gunicorn + uvicorn workers (not --reload)
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-"]