# Production Dockerfile for Multilingual NLP API
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt requirements_api.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements_api.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data adaptive_learning

# Create non-root user for security
RUN useradd -m -u 1000 nlpuser && \
    chown -R nlpuser:nlpuser /app

# Switch to non-root user
USER nlpuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with gunicorn for production
CMD ["gunicorn", "-c", "gunicorn_config.py", "api:app"]
