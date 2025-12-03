#!/bin/bash
set -e

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    source .env
fi

# Set defaults if not provided
REGION=${REGION}
REPO_NAME=${REPO_NAME}
SERVICE_NAME=${SERVICE_NAME}
PROJECT_ID=${PROJECT_ID}

echo "🚀 Starting Cloud Build with the following configuration:"
echo "   Project: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo "   Repository: ${REPO_NAME}"
echo "   Service: ${SERVICE_NAME}"

# Submit the build with substitutions
gcloud builds submit \
  --config=cloudbuild.yaml \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --substitutions="_REGION=${REGION},_REPO_NAME=${REPO_NAME},_SERVICE_NAME=${SERVICE_NAME}"

echo "✅ Cloud Build completed successfully!"
