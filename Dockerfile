FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-editable

COPY . .

# --- Production stage ---
FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Non-root user
RUN groupadd -r classgen && useradd -r -g classgen -d /app classgen

WORKDIR /app

# Copy built venv and app code
COPY --from=builder /app /app

# Ensure static dir exists and is writable
RUN mkdir -p /app/static && chown -R classgen:classgen /app/static

USER classgen

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Use --workers for production concurrency
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
