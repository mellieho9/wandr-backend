#!/bin/bash

# Deployment script for wandr-batch-processor Cloud Run Job and Scheduler

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ .env file not found. Please copy .env.example to .env and fill in the values."
    exit 1
fi

# Check required variables
required_vars=("PROJECT_ID" "REGION" "JOB_NAME" "SCHEDULER_JOB_NAME" "SA_EMAIL" "IMAGE_NAME")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set in .env"
        exit 1
    fi
done

echo "🚀 Starting deployment..."

# Build and push Docker image
echo "📦 Building Docker image..."
docker build -t $IMAGE_NAME .

echo "📤 Pushing image to registry..."
docker push $IMAGE_NAME

# Delete existing job if it exists
echo "🗑️  Cleaning up existing job..."
gcloud run jobs delete $JOB_NAME --region=$REGION --quiet || echo "Job doesn't exist, continuing..."

# Create new job
echo "🏗️  Creating Cloud Run Job..."
gcloud run jobs create $JOB_NAME \
  --image=$IMAGE_NAME \
  --region=$REGION \
  --memory=2Gi \
  --cpu=2 \
  --task-timeout=3600 \
  --max-retries=1 \
  --set-env-vars="PYTHONPATH=/app,BUCKET_NAME=${BUCKET_NAME}" \
  --set-secrets="VISION_API_KEY=VISION_API_KEY:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest,GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY:latest,NOTION_API_KEY=NOTION_API_KEY:latest,NOTION_PLACES_DB_ID=NOTION_PLACES_DB_ID:latest,NOTION_SOURCE_DB_ID=NOTION_SOURCE_DB_ID:latest"

# Delete existing scheduler if it exists
echo "🗑️  Cleaning up existing scheduler..."
gcloud scheduler jobs delete $SCHEDULER_JOB_NAME --location=$REGION --quiet || echo "Scheduler doesn't exist, continuing..."

# Create scheduler job
echo "⏰ Creating Cloud Scheduler job..."
gcloud scheduler jobs create http $SCHEDULER_JOB_NAME \
    --location=$REGION \
    --schedule="0 8 * * *" \
    --time-zone="UTC" \
    --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
    --http-method=POST \
    --oauth-service-account-email=$SA_EMAIL

echo "✅ Deployment complete!"
echo "📊 To execute job manually: gcloud run jobs execute $JOB_NAME --region=$REGION"
echo "📅 Scheduled to run daily at 8 AM UTC"