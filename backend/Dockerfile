FROM python:3.11-slim

WORKDIR /app

# System deps (minimal).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ML dependencies are optional — skip failures to keep the image lightweight.
COPY requirements-ml.txt .
RUN pip install --no-cache-dir -r requirements-ml.txt || true

COPY . .

# Railway sets $PORT dynamically. Default to 8000 for local use.
EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

