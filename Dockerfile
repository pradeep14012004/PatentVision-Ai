# PatentVision AI – FastAPI backend for Hugging Face Docker Spaces.
# Hugging Face Docker Spaces serve on port 7860 by default.
# u2netp (4.6 MB ONNX) is pre-baked so cold starts need no runtime download.
# Single-worker demo configuration; local SQLite and file storage are temporary.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NUMBA_DISABLE_JIT=1 \
    OMP_NUM_THREADS=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/build
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Render (and most cloud hosts) run as non-root UID 1000.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    REMBG_HOME=/home/user/.rembg

WORKDIR /home/user/app

# Pre-bake u2netp weights (4.6 MB) — lighter than u2net (170 MB), fits Render free-tier RAM.
RUN python -c "import os; os.environ['REMBG_HOME']='/home/user/.rembg'; import rembg; rembg.new_session('u2netp')"

COPY --chown=user:user backend/app ./app
COPY --chown=user:user backend/alembic ./alembic
COPY --chown=user:user backend/alembic.ini ./alembic.ini

RUN mkdir -p /home/user/app/storage

# Run migrations then start the server. Single worker: job slots and rate limiter are in-process.
EXPOSE 7860
CMD ["sh", "-c", "python -c \"import os; from app.core.config import get_settings; from app.core.database import normalize_url; u = normalize_url(get_settings().database_url); print('DB target:', u.split('@')[-1] if '@' in u else u)\" && (alembic upgrade head || echo 'WARNING: Alembic migration failed, continuing startup...') && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
