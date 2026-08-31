# Cricket AI Council - Multi-stage Dockerfile

# ─── Base ─────────────────────────────────────────────────────────────────────
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ─── Dependencies ─────────────────────────────────────────────────────────────
FROM base as deps

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─── Runtime ──────────────────────────────────────────────────────────────────
FROM base as runtime

# Copy dependencies
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY workflow.py mcp_server.py config.py ./
COPY analysis/ analysis/
COPY rag/ rag/
COPY app/ app/
COPY ui/ ui/
COPY data/ data/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run FastAPI
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
