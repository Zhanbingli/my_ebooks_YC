FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install runtime deps first for better caching
COPY pyproject.toml README.md /app/
RUN pip install --no-cache-dir .

# Copy minimal runtime assets (config can be overridden via bind mount)
COPY src /app/src
COPY config /app/config
COPY metadata /app/metadata

EXPOSE 8000

CMD ["python", "-m", "ebook_pipeline.web", "--host", "0.0.0.0", "--port", "8000"]
