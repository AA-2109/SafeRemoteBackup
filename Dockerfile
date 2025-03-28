# Safe Remote Backup - Docker Configuration
#
# This Dockerfile sets up a secure environment for running the Safe Remote Backup application.
# It uses Python 3.11 slim image as the base and implements security best practices.
#
# Author: Your Name
# Version: 1.0.0

# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd -m -r -s /bin/bash appuser \
    && mkdir -p /app/uploads /app/backups /app/logs /app/data /app/certs \
    && chown -R appuser:appuser /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set permissions
RUN chown -R appuser:appuser /app \
    && chmod -R 755 /app \
    && chmod -R 777 /app/uploads /app/backups /app/logs /app/data

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run the application
CMD ["python", "app/app.py"]
