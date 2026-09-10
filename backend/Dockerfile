FROM python:3.11-slim@sha256:9534e5a8e315485d4061ed659af0fd78a284c015f9b73661b41d6bab25604534

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir pip==26.2.1 setuptools==84.0.0 \
    && pip install --no-cache-dir --require-hashes -r requirements.txt

COPY app ./app

RUN useradd --uid 10001 --create-home reviewer \
    && mkdir -p /app/data/review-v2/uploads \
    && chown -R reviewer:reviewer /app/data
USER reviewer
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 REVIEW_DATA_DIR=/app/data/review-v2

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
