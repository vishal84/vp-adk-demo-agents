#!/bin/bash

# =============================================================================
# CREATE GEMINI ENTERPRISE AGENT
# =============================================================================
# This script surfaces an agent running on Agent Engine in Gemini Enterprise
# Run this AFTER creating and deploying the agent to Agent Engine

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
required_vars=("GOOGLE_CLOUD_PROJECT" "GOOGLE_CLOUD_PROJECT_NUMBER" "GOOGLE_CLOUD_LOCATION" "GE_APP" "ASSISTANT_ID" "AGENT_NAME" "AGENT_DISPLAY_NAME" "AGENT_DESCRIPTION" "AGENT_URL" "PROTOCOL_VERSION")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set in .env"
        exit 1
    fi
done

echo "🚀 Creating AgentSpace Agent..."
echo "   Project: $GOOGLE_CLOUD_PROJECT"
echo "   Agent Name: $AGENT_NAME"
echo "   Display Name: $AGENT_DISPLAY_NAME"

# --- Script Body ---
AUTH_TOKEN=$(gcloud auth print-access-token)
DISCOVERY_ENGINE_API_BASE_URL="https://discoveryengine.googleapis.com"

# Prepare the JSON for jsonAgentCard. It must be a string.
JSON_AGENT_CARD_VALUE_RAW=$(cat <<EOF
{
    "capabilities": { "streaming": true },
    "defaultInputModes": ["text"],
    "defaultOutputModes": ["text"],
    "description": "${AGENT_DESCRIPTION}",
    "name": "${AGENT_DISPLAY_NAME}",
    "preferredTransport": "HTTP+JSON",
    "protocolVersion": "${PROTOCOL_VERSION}",
    "skills": [
        {
            "description": "Creates a new calendar event.",
            "examples": [
                "Add a calendar event for my meeting tomorrow at 10 AM."
            ],
            "id": "${AGENT_NAME}",
            "inputModes": ["text/plain"],
            "name": "${AGENT_DISPLAY_NAME}",
            "outputModes": ["text/plain"],
            "tags": ["calendar", "event", "create"]
        }
    ],
    "supportsAuthenticatedExtendedCard": true,
    "url": "${AGENT_URL}",
    "version": "1.0.0"
}
EOF
)

# Escape the raw JSON to be a valid JSON string.
JSON_AGENT_CARD_VALUE_ESCAPED=$(printf '%s' "$JSON_AGENT_CARD_VALUE_RAW" | jq -Rs .)

# Prepare the main request body using a heredoc for clarity.
REQUEST_BODY=$(cat <<EOF
{
        "name": "projects/${GOOGLE_CLOUD_PROJECT_NUMBER}/locations/${GOOGLE_CLOUD_LOCATION}/collections/default_collection/engines/${GE_APP}/assistants/${ASSISTANT_ID}/agents/${AGENT_NAME}",
        "displayName": "${AGENT_DISPLAY_NAME}",
        "description": "${AGENT_DESCRIPTION}",
        "a2aAgentDefinition": {
            "jsonAgentCard": ${JSON_AGENT_CARD_VALUE_ESCAPED}
        }
}
EOF
)

echo "📡 Making API request..."
response=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${GOOGLE_CLOUD_PROJECT}" \
  "${DISCOVERY_ENGINE_API_BASE_URL}/v1alpha/projects/${GOOGLE_CLOUD_PROJECT}/locations/global/collections/default_collection/engines/${GE_APP}/assistants/${ASSISTANT_ID}/agents" \
  -d "$REQUEST_BODY")

printf '%s\n' "$response"

# Extract response body and status code
http_code=$(printf '%s' "$response" | tail -n1)
response_body=$(printf '%s' "$response" | sed '$d')

echo "📋 Response:"
echo "$response_body" | jq . 2>/dev/null || echo "$response_body"

if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
    echo "✅ Agent created successfully!"
    echo "   Agent Name: $AGENT_NAME"
    echo "   Display Name: $AGENT_DISPLAY_NAME"
    echo "   Next step: Test the agent in AgentSpace web interface"
else
    echo "❌ Failed to create agent (HTTP $http_code)"
    echo "   Check your configuration and try again"
    exit 1
fi
