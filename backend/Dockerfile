# syntax=docker/dockerfile:1

# Multi-stage build: compile dependencies in a full image, run in a slim one so the
# final image carries no build toolchain (smaller, smaller attack surface).

FROM python:3.12-slim AS builder

WORKDIR /build

# Build tooling needed to compile any wheels without prebuilt binaries for this platform
# (e.g. scipy/scikit-learn on less common architectures). Not present in the final image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.12-slim AS runtime

# Never run the app as root inside the container.
RUN groupadd --system app && useradd --system --gid app --home-dir /app app

WORKDIR /app

COPY --from=builder /install /usr/local
COPY app ./app

# Dataset storage (see app/config.py's data_dir default) lives under /app/data — a named
# volume is mounted here in docker-compose.yml so uploads survive container restarts.
RUN mkdir -p /app/data/uploads && chown -R app:app /app

USER app

ENV APP_DATA_DIR=data/uploads \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
