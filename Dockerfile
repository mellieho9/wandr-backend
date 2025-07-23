# Use Python 3.11 slim for better performance
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8080

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # OpenCV dependencies
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # FFmpeg for video processing
    ffmpeg \
    # Git for potential package installations
    git \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app directory and user
WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

# Copy requirements first for better caching
COPY --chown=appuser:appuser requirements.txt .

# Install Python dependencies as root, then switch to appuser
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Create results directory
RUN mkdir -p results logs

# Set Python path
ENV PYTHONPATH=/app

# Add a simple web server for Cloud Run health checks
RUN echo 'from flask import Flask\n\
app = Flask(__name__)\n\
\n\
@app.route("/")\n\
def health():\n\
    return {"status": "healthy", "service": "wandr-backend"}\n\
\n\
@app.route("/process", methods=["POST"])\n\
def process():\n\
    import subprocess\n\
    result = subprocess.run(["python", "main.py", "--process-pending-urls"], capture_output=True, text=True)\n\
    return {"success": result.returncode == 0, "output": result.stdout, "error": result.stderr}\n\
\n\
if __name__ == "__main__":\n\
    import os\n\
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))' > app.py

# Add Flask to requirements if not present
RUN pip install flask

# Expose port
EXPOSE 8080

# Default command - web server for Cloud Run
CMD ["python", "app.py", "--process-pending-urls"]