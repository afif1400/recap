FROM python:3.11-slim

# System deps for pdf/image parsing.
RUN apt-get update && apt-get install -y --no-install-recommends \
      libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# HF Spaces runs as a non-root user — make sure caches go somewhere writable.
ENV HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default to mock backend on HF until MI300X tunnel is configured via env var.
ENV RECAP_BACKEND=mock

EXPOSE 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
