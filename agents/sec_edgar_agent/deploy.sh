#!/bin/bash

# SEC EDGAR MCP Cloud Run Deployment Script

set -e

# Configuration
PROJECT_ID=${1:-"your-gcp-project-id"}
SERVICE_NAME="sec-edgar-mcp"
REGION=${2:-"us-central1"}
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
SEC_EDGAR_USER_AGENT=${3:-"vishalapatel@google.com"}

echo "🚀 Deploying SEC EDGAR MCP to Google Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "Image: $IMAGE_NAME"
echo "SEC EDGAR User-Agent: $SEC_EDGAR_USER_AGENT"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "."; then
    echo "❌ Error: Please authenticate with gcloud first:"
    echo "gcloud auth login"
    exit 1
fi

# Set the project
echo "📋 Setting GCP project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push the Docker image
echo "🔨 Building Docker image..."
docker build -t $IMAGE_NAME .

echo "📤 Pushing image to Container Registry..."
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 10 \
    --set-env-vars SEC_EDGAR_USER_AGENT="$SEC_EDGAR_USER_AGENT"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "📋 To test the deployment:"
echo "curl $SERVICE_URL/health"
echo ""
echo "📚 To view logs:"
echo "gcloud run logs read $SERVICE_NAME --region=$REGION"
echo ""
echo "🔧 To update the service:"
echo "./deploy.sh $PROJECT_ID $REGION"