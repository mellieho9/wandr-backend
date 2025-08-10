# Stage 1: Build dependencies and install Python packages
FROM --platform=linux/amd64 python:3.11-slim AS builder

# Install build dependencies for Debian
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libglib2.0-dev \
    libcairo2-dev \
    libgirepository1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --user -r /tmp/requirements.txt

# Stage 2: Install Playwright and browsers (heavy stage)
FROM --platform=linux/amd64 python:3.11-slim AS playwright-installer

# Install minimal runtime dependencies for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    bash \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

USER appuser

# Copy Python packages from builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Install only Chromium browser (no firefox/webkit downloaded)
RUN playwright install chromium && \
    rm -rf /home/appuser/.cache/pip && \
    rm -rf /home/appuser/.cache/playwright-python && \
    find /home/appuser/.local -name "*.pyc" -delete && \
    find /home/appuser/.local -name "__pycache__" -type d -exec rm -rf {} + || true

# Stage 3: Final lightweight runtime
FROM --platform=linux/amd64 python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    DISPLAY=:99 \
    PYTHONPATH=/app \
    PATH=/home/appuser/.local/bin:$PATH

# Install minimal runtime dependencies (NO ffmpeg - not needed!)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    xvfb \
    bash \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && useradd --create-home --shell /bin/bash appuser

WORKDIR /app
RUN mkdir -p results logs && chown -R appuser:appuser /app

# Copy Python packages and Playwright browsers from previous stages
COPY --from=playwright-installer --chown=appuser:appuser /home/appuser/.local /home/appuser/.local

USER appuser

# Copy application code (this should be last for better caching)
COPY --chown=appuser:appuser . .

# Start virtual display and run command
CMD ["/bin/bash", "-c", "Xvfb :99 -screen 0 1024x768x16 -ac +extension GLX +render -noreset & while ! xdpyinfo -display :99 >/dev/null 2>&1; do sleep 0.1; done && python3 app.py --process-pending-urls"]