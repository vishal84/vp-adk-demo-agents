#!/bin/bash
set -e # Exit on any error

# Load environment variables
if [ -f .env ]; then
  source .env
  echo "✅ Loaded .env file"
else
  echo "❌ Error: .env file not found. Please copy .env.example to .env and configure it."
  exit 1
fi

# Validate required variables
required_vars=("GOOGLE_CLOUD_PROJECT" "AGENT_RESOURCE_NAME")
for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "❌ Error: Required environment variable $var is not set in .env"
    exit 1
  fi
done

echo "🔴 This script will permanently delete the following agent:"
echo "   $AGENT_RESOURCE_NAME"
echo ""
read -p "Are you sure you want to continue? (y/n) " -n 1 -r
echo # Move to a new line

if [[ !$REPLY =~ ^[Yy]$ ]]
then
    echo "Aborted by user."
    exit 1
fi

echo ""
echo "🔥 Deleting agent..."

# API call to delete an agent
curl -X DELETE \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: $GOOGLE_CLOUD_PROJECT" \
  "https://discoveryengine.googleapis.com/v1alpha/$AGENT_RESOURCE_NAME"

echo -e "\n\n✅ Script finished. The agent has been deleted."
