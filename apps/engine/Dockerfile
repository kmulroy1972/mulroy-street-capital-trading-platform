FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-base.txt .
RUN pip install --no-cache-dir -r requirements-base.txt

# Copy application code
COPY apps/engine apps/engine
COPY packages packages

# Create non-root user
RUN useradd -m -u 1000 trader && chown -R trader:trader /app
USER trader

# Create logs directory
RUN mkdir -p /app/logs

# Health check script
COPY scripts/health_check.py .

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python health_check.py

# Run the engine
CMD ["python", "-u", "apps/engine/main.py"]