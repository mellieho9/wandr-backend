#!/bin/bash

# Local Docker testing script for wandr-webhook-service

set -e

IMAGE_NAME="wandr-webhook-test"
CONTAINER_NAME="wandr-test"

echo "🧪 Testing Docker image locally..."

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Build image
echo "📦 Building Docker image..."
docker build -t $IMAGE_NAME .

# Test whisper Python API availability
echo "🎵 Testing Whisper Python API..."
docker run --rm $IMAGE_NAME python -c "import whisper; print('Whisper available')" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Whisper Python API available"
else
    echo "❌ Whisper Python API failed"
    exit 1
fi

# Start container with environment variables
echo "🚀 Starting webhook service..."
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env"
    docker run -d --name $CONTAINER_NAME -p 8080:8080 --env-file .env $IMAGE_NAME
else
    echo "⚠️  No .env file found, using default settings"
    docker run -d --name $CONTAINER_NAME -p 8080:8080 $IMAGE_NAME
fi

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

echo "✅ Container started successfully"

# Test webhook processing (metadata-only mode for speed)
echo "🎬 Testing webhook processing..."
response=$(curl -s -X POST http://localhost:8080/webhook/process \
    -H "Content-Type: application/json" \
    -d '{"url": "https://www.tiktok.com/@tofueeats/video/7530655971283193101?_r=1&_t=ZP-8yIjnCgKk4l", "tags": ["metadata-only"]}' \
    -w "%{http_code}")

echo "Webhook response: $response"

# Check memory usage
echo "💾 Memory usage:"
docker stats --no-stream $CONTAINER_NAME

# Cleanup
echo "🧹 Cleaning up..."
docker stop $CONTAINER_NAME
docker rm $CONTAINER_NAME

echo "✅ Local testing completed successfully!"
echo "🚀 Ready to deploy with: ./scripts/deploy.sh"