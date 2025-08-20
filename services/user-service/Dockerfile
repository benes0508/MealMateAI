# Multi-stage Dockerfile optimized for fast rebuilds
# Stage 1: Dependencies (cached separately)
FROM python:3.11-slim as dependencies

# Configure pip for caching
ENV PIP_CACHE_DIR=/pip_cache
ENV PIP_NO_CACHE_DIR=0

WORKDIR /app

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies with cache mount
RUN --mount=type=cache,target=/pip_cache \
    pip install --cache-dir=/pip_cache -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim as production

WORKDIR /app

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]