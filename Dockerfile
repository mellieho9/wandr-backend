# Multi-stage build for smaller final image
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --user -r /tmp/requirements.txt

# Intermediate stage for system dependencies
FROM python:3.11-slim AS runtime-builder

# Install system dependencies that distroless needs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    ffmpeg \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Create app structure
WORKDIR /app
RUN useradd --create-home --shell /bin/bash appuser

# Create directories with proper ownership
RUN mkdir -p results logs && chown -R appuser:appuser /app

USER appuser

# Install Playwright browsers
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH
RUN playwright install chromium

# Copy application code
COPY --chown=appuser:appuser . .

# Final production stage - using slim instead of distroless for compatibility
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    DISPLAY=:99 \
    PYTHONPATH=/app \
    PATH=/home/appuser/.local/bin:$PATH

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    ffmpeg \
    xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create user
RUN useradd --create-home --shell /bin/bash appuser

# Copy everything from runtime-builder
COPY --from=runtime-builder --chown=appuser:appuser /app /app
COPY --from=runtime-builder --chown=appuser:appuser /home/appuser/.local /home/appuser/.local
COPY --from=runtime-builder --chown=appuser:appuser /home/appuser/.cache /home/appuser/.cache

WORKDIR /app
USER appuser

# Expose port
EXPOSE 8080

# Create startup script
RUN printf '#!/bin/bash\nset -e\n\n# Start virtual display in background\nXvfb :99 -screen 0 1024x768x16 -ac +extension GLX +render -noreset &\nsleep 2\n\n# Start gunicorn\nexec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 300 --preload "app:create_app()"\n' > /app/start.sh && \
    chmod +x /app/start.sh

# Default command
CMD ["/app/start.sh"]