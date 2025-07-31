#!/bin/bash

# Deployment script for wandr-webhook-service Cloud Run Service

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ .env file not found. Please copy .env.example to .env and fill in the values."
    exit 1
fi

# Check required variables
required_vars=("PROJECT_ID" "REGION" "SERVICE_NAME")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set in .env"
        exit 1
    fi
done

# Auto-generate IMAGE_NAME from PROJECT_ID and SERVICE_NAME using Artifact Registry
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${SERVICE_NAME}"
echo "🏷️  Generated image name: $IMAGE_NAME"

echo "🚀 Starting webhook service deployment..."

# Create Artifact Registry repository if it doesn't exist
echo "📋 Setting up Artifact Registry..."
gcloud artifacts repositories create $SERVICE_NAME \
  --repository-format=docker \
  --location=$REGION \
  --description="Wandr webhook service container images" \
  --quiet || echo "Repository already exists"

# Configure Docker authentication for Artifact Registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Build and push Docker image
echo "📦 Building Docker image..."
docker buildx build -t $IMAGE_NAME --platform linux/amd64 .

echo "📤 Pushing image to Artifact Registry..."
docker push $IMAGE_NAME

# Deploy Cloud Run Service
echo "🏗️  Deploying Cloud Run Service..."
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_NAME \
  --region=$REGION \
  --memory=2Gi \
  --cpu=2 \
  --timeout=3600 \
  --max-instances=10 \
  --min-instances=0 \
  --allow-unauthenticated \
  --set-env-vars="PYTHONPATH=/app,HOST=0.0.0.0" \
  --set-secrets="VISION_API_KEY=VISION_API_KEY:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest,GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY:latest,NOTION_API_KEY=NOTION_API_KEY:latest,NOTION_PLACES_DB_ID=NOTION_PLACES_DB_ID:latest"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo "📋 Webhook endpoints:"
echo "   • POST $SERVICE_URL/webhook/process - Process webhook requests"
echo "   • GET  $SERVICE_URL/webhook/health - Health check"
echo "   • GET  $SERVICE_URL/webhook/status - Service status"
echo ""
echo "💡 Configure your Notion webhook to POST to: $SERVICE_URL/webhook/process"