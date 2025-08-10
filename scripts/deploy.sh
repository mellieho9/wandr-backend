#!/bin/bash

# Deployment script for wandr-backend Cloud Run Job

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
# scripts/deploy.sh (around lines 26-31)
base_name="$(echo "$SERVICE_NAME" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9-]/-/g; s/^-+//; s/-+$//; s/-{2,}/-/g' \
  | cut -c1-59)"
JOB_NAME="${base_name}-job"
echo "🏷️  Generated image name: $IMAGE_NAME"
echo "🏷️  Job name: $JOB_NAME"

echo "🚀 Starting job deployment..."
# Create Artifact Registry repository if it doesn't exist
echo "📋 Setting up Artifact Registry..."
if ! gcloud artifacts repositories describe "$SERVICE_NAME" \
  --location="$REGION" \
  --project="$PROJECT_ID" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$SERVICE_NAME" \
    --repository-format=docker \
    --location="$REGION" \
    --project="$PROJECT_ID" \
    --description="Wandr backend job container images" \
    --quiet
fi
# Configure Docker authentication for Artifact Registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Build and push Docker image
echo "📦 Building Docker image..."
docker build -t $IMAGE_NAME .

echo "📤 Pushing image to Artifact Registry..."
docker push $IMAGE_NAME

# Deploy Cloud Run Job
echo "🏗️  Deploying Cloud Run Job..."
gcloud run jobs create $JOB_NAME \
  --image=$IMAGE_NAME \
  --region=$REGION \
  --memory=2Gi \
  --cpu=2 \
  --max-retries=3 \
  --task-timeout=3600 \
  --set-env-vars="PYTHONPATH=/app" \
  --set-secrets="VISION_API_KEY=VISION_API_KEY:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest,GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY:latest,NOTION_API_KEY=NOTION_API_KEY:latest,NOTION_PLACES_DB_ID=NOTION_PLACES_DB_ID:latest,NOTION_SOURCE_DB_ID=NOTION_SOURCE_DB_ID:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest" \
  --quiet || \
gcloud run jobs update $JOB_NAME \
  --image=$IMAGE_NAME \
  --region=$REGION \
  --memory=2Gi \
  --cpu=2 \
  --max-retries=3 \
  --task-timeout=3600 \
  --set-env-vars="PYTHONPATH=/app" \
  --set-secrets="VISION_API_KEY=VISION_API_KEY:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest,GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY:latest,NOTION_API_KEY=NOTION_API_KEY:latest,NOTION_PLACES_DB_ID=NOTION_PLACES_DB_ID:latest,NOTION_SOURCE_DB_ID=NOTION_SOURCE_DB_ID:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest" \
  --quiet
  
echo "💡 Manual execution: gcloud run jobs execute $JOB_NAME --region=$REGION"