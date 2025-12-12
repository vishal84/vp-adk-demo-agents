#!/bin/bash
set -e  # Exit on any error

# Load environment variables
if [ -f .env ]; then
  source .env
  echo "✅ Loaded .env file"
else
  echo "❌ Error: .env file not found. Please copy .env.example to .env and configure it."
  exit 1
fi

# Validate required variables
required_vars=("GOOGLE_CLOUD_PROJECT" "AS_APP")
for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "❌ Error: Required environment variable $var is not set in .env"
    exit 1
  fi
done

echo "🔍 Fetching list of agents for project '$GOOGLE_CLOUD_PROJECT' and app '$AS_APP'..."

# API call to list agents
RESPONSE=$(curl -s -X GET \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: $GOOGLE_CLOUD_PROJECT" \
  "https://discoveryengine.googleapis.com/v1alpha/projects/$GOOGLE_CLOUD_PROJECT/locations/global/collections/default_collection/engines/$AS_APP/assistants/default_assistant/agents")

# Format as console readable list using jq
if echo "$RESPONSE" | jq -e '.agents' > /dev/null; then
  echo -e "\n--- Agents List ---\n"
  echo "$RESPONSE" | jq -r '
    .agents[] | 
    "Agent ID:     \(.name | split("/") | last)",
    "Display Name: \(.displayName // "N/A")",
    "Description:  \(.description // "N/A")",
    "----------------------------------------"
  '
else
  echo "No agents found or error in response."
  echo "Raw response: $RESPONSE"
fi

echo -e "\n✅ Script finished."
