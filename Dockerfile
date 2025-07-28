# Use Python slim base with manual whisper installation for better control
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8080 \
    DISPLAY=:99

# Install system dependencies including whisper
RUN apt-get update && apt-get install -y \
    # OpenCV dependencies
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # FFmpeg for whisper
    ffmpeg \
    # Git for potential package installations
    git \
    # Virtual display for headless browsers
    xvfb \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install whisper globally for CLI usage (lightweight approach)
RUN pip install --no-cache-dir openai-whisper

# Create app directory and user
WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

# Copy requirements first for better caching
COPY --chown=appuser:appuser requirements.txt .

# Install Python dependencies (excluding whisper since it's already installed)
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers for pyktok
RUN playwright install chromium
RUN playwright install-deps

# Switch to non-root user
USER appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Create results directory
RUN mkdir -p results logs

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Default command - start virtual display and run webhook server
CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x16 & python app.py"]