FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data/uploads /app/chroma \
    && chown -R appuser:appuser /app
USER appuser

# Bake ChromaDB's ONNX embedding model into the image at build time instead of
# downloading it on the first request. Without this, every fresh
# deploy/restart makes whichever user hits it first wait through a ~80MB
# download mid-analysis (it lazily downloads to ~/.cache/chroma, which isn't
# on a persisted volume).
RUN python -c "from chromadb.utils import embedding_functions; embedding_functions.DefaultEmbeddingFunction()(['warm up'])"

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
