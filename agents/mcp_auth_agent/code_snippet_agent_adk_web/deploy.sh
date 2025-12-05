#!/bin/bash
set -e

# BEFORE RUNNING THIS SCRIPT:
# 1. Ensure you have the Google Cloud SDK installed and configured.
# 2. Authenticate with Google Cloud using `gcloud auth login`.
# 3. Set the desired Google Cloud project and location in a .env file or export them as environment variables:
#    - GOOGLE_CLOUD_PROJECT: Your Google Cloud project ID.
#    - GOOGLE_CLOUD_LOCATION: The region for Cloud Build (e.g., us-central1).
# 4. Run the following command to grant your Compute Engine default service account the necessary permissions:
#    gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
#      --member="serviceAccount:YOUR_COMPUTE_ENGINE_DEFAULT_SERVICE_ACCOUNT" \
#      --role="roles/cloudbuild.builds.builder"

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    source .env
fi

# Set defaults if not provided
GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION}

echo "🚀 Starting Cloud Build with the following configuration:"
echo "   Project: ${GOOGLE_CLOUD_PROJECT}"
echo "   Location: ${GOOGLE_CLOUD_LOCATION}"

# Submit the build job to Cloud Build
gcloud builds submit \
  --config=cloudbuild.yaml \
  --project="${GOOGLE_CLOUD_PROJECT}" \
  --region="${GOOGLE_CLOUD_LOCATION}"

echo "✅ Cloud Build completed successfully!"
