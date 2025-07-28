#!/bin/bash

# Local Docker testing script for wandr-webhook-service

set -e

IMAGE_NAME="wandr-webhook-test"
CONTAINER_NAME="wandr-test"

echo "🧪 Testing Docker image locally..."

# Build image
echo "📦 Building Docker image..."
docker build -t $IMAGE_NAME .

# Test whisper CLI availability
echo "🎵 Testing Whisper CLI..."
docker run --rm $IMAGE_NAME whisper --help > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Whisper CLI available"
else
    echo "❌ Whisper CLI failed"
    exit 1
fi

# Start container
echo "🚀 Starting webhook service..."
docker run -d --name $CONTAINER_NAME -p 8080:8080 $IMAGE_NAME

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# Test health endpoint
echo "🏥 Testing health endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/webhook/health)
if [ "$response" = "200" ]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed (HTTP $response)"
    docker logs $CONTAINER_NAME
    docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME
    exit 1
fi

# Test status endpoint
echo "📊 Testing status endpoint..."
curl -s http://localhost:8080/webhook/status

# Test webhook processing (metadata-only mode for speed)
echo "🎬 Testing webhook processing..."
response=$(curl -s -X POST http://localhost:8080/webhook/process \
    -H "Content-Type: application/json" \
    -d '{"url": "https://www.tiktok.com/@fiyahfeasts/video/7530880767518313759?_r=1&_t=ZP-8yOFzN9bUQJ", "tags": ["audio-only"]}' \
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