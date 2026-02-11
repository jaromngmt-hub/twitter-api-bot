# Production-ready Dockerfile for Twitter Monitor Bot
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for database persistence
RUN mkdir -p /app/data /app/logs /app/static

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Volume for database persistence
VOLUME ["/app/data"]

# Default environment
ENV DATABASE_PATH=/app/data/monitor.db

# Expose port for web API
EXPOSE 8000

# Run web API if PORT is set (Render/Railway), otherwise run CLI monitor
CMD ["sh", "-c", "if [ -n \"\$PORT\" ]; then uvicorn api:app --host 0.0.0.0 --port \$PORT; else python main.py run; fi"]
