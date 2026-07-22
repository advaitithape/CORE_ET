# ── Industrial Knowledge Intelligence — backend image ──────────────────────
# Ships CODE ONLY: no plant documents are baked into the image. The knowledge
# base boots empty and is populated at runtime through the upload UI.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# application code (data/ and outputs/ are excluded via .dockerignore)
COPY backend/ backend/
COPY agents/ agents/
COPY knowledge/ knowledge/
COPY pipeline/ pipeline/
COPY dataset/ dataset/

# runtime state lives here (uploads, ingestion manifest, embedding cache)
RUN mkdir -p data/uploads outputs

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn backend.app:app --host 0.0.0.0 --port ${PORT}"]
