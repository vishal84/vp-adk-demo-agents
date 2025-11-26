#!/bin/bash

# =============================================================================
# VALIDATE AGENT ENGINE AND AGENTSPACE CONFIGURATION
# =============================================================================
# This script validates your .env configuration for Agent Engine and AgentSpace

set -e

# Load environment variables
if [ -f .env ]; then
    source .env
    echo "✅ Loaded .env file"
else
    echo "❌ Error: .env file not found"
    exit 1
fi

echo ""
echo "📋 Configuration Summary:"
echo "   Project: $GOOGLE_CLOUD_PROJECT"
echo "   Location: $GOOGLE_CLOUD_LOCATION"
echo "   AS_APP: $AS_APP"
echo "   ASSISTANT_ID: $ASSISTANT_ID"
echo "   REASONING_ENGINE: $REASONING_ENGINE"
echo ""

AUTH_TOKEN=$(gcloud auth print-access-token)

# =============================================================================
# 1. Validate Reasoning Engine
# =============================================================================
echo "🔍 Validating Reasoning Engine..."
if [ -z "$REASONING_ENGINE" ]; then
    echo "   ⚠️  REASONING_ENGINE not set in .env"
else
    response=$(curl -s -w "\n%{http_code}" \
      -H "Authorization: Bearer ${AUTH_TOKEN}" \
      "https://${GOOGLE_CLOUD_LOCATION}-aiplatform.googleapis.com/v1/${REASONING_ENGINE}")
    
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo "   ✅ Reasoning Engine exists"
        echo "$response_body" | jq -r '.displayName' 2>/dev/null | sed 's/^/      Display Name: /'
    else
        echo "   ❌ Reasoning Engine NOT found (HTTP $http_code)"
        echo "$response_body" | jq . 2>/dev/null || echo "$response_body"
    fi
fi

echo ""

# =============================================================================
# 2. List all Reasoning Engines in project
# =============================================================================
echo "📝 Listing all Reasoning Engines in project..."
response=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  "https://${GOOGLE_CLOUD_LOCATION}-aiplatform.googleapis.com/v1/projects/${GOOGLE_CLOUD_PROJECT}/locations/${GOOGLE_CLOUD_LOCATION}/reasoningEngines")

http_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    engine_count=$(echo "$response_body" | jq '.reasoningEngines | length' 2>/dev/null || echo "0")
    echo "   Found $engine_count reasoning engine(s)"
    echo "$response_body" | jq -r '.reasoningEngines[]? | "   - \(.name)\n     Display: \(.displayName)"' 2>/dev/null
else
    echo "   ❌ Failed to list reasoning engines (HTTP $http_code)"
    echo "$response_body" | jq . 2>/dev/null || echo "$response_body"
fi

echo ""

# =============================================================================
# 3. Validate AgentSpace App (Engine)
# =============================================================================
echo "🔍 Validating AgentSpace App..."
if [ -z "$AS_APP" ]; then
    echo "   ⚠️  AS_APP not set in .env"
else
    response=$(curl -s -w "\n%{http_code}" \
      -H "Authorization: Bearer ${AUTH_TOKEN}" \
      -H "X-Goog-User-Project: ${GOOGLE_CLOUD_PROJECT}" \
      "https://discoveryengine.googleapis.com/v1alpha/projects/${GOOGLE_CLOUD_PROJECT}/locations/global/collections/default_collection/engines/${AS_APP}")
    
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo "   ✅ AgentSpace App exists"
        echo "$response_body" | jq -r '.displayName' 2>/dev/null | sed 's/^/      Display Name: /'
    else
        echo "   ❌ AgentSpace App NOT found (HTTP $http_code)"
        echo "$response_body" | jq . 2>/dev/null || echo "$response_body"
    fi
fi

echo ""

# =============================================================================
# 4. Validate Assistant
# =============================================================================
echo "🔍 Validating Assistant..."
if [ -z "$AS_APP" ] || [ -z "$ASSISTANT_ID" ]; then
    echo "   ⚠️  AS_APP or ASSISTANT_ID not set in .env"
else
    response=$(curl -s -w "\n%{http_code}" \
      -H "Authorization: Bearer ${AUTH_TOKEN}" \
      -H "X-Goog-User-Project: ${GOOGLE_CLOUD_PROJECT}" \
      "https://discoveryengine.googleapis.com/v1alpha/projects/${GOOGLE_CLOUD_PROJECT}/locations/global/collections/default_collection/engines/${AS_APP}/assistants/${ASSISTANT_ID}")
    
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo "   ✅ Assistant exists"
        echo "$response_body" | jq -r '.displayName' 2>/dev/null | sed 's/^/      Display Name: /'
    else
        echo "   ❌ Assistant NOT found (HTTP $http_code)"
        echo "$response_body" | jq . 2>/dev/null || echo "$response_body"
    fi
fi

echo ""

# =============================================================================
# 5. List Agents in Assistant
# =============================================================================
echo "📝 Listing Agents in Assistant..."
if [ -z "$AS_APP" ] || [ -z "$ASSISTANT_ID" ]; then
    echo "   ⚠️  AS_APP or ASSISTANT_ID not set in .env"
else
    response=$(curl -s -w "\n%{http_code}" \
      -H "Authorization: Bearer ${AUTH_TOKEN}" \
      -H "X-Goog-User-Project: ${GOOGLE_CLOUD_PROJECT}" \
      "https://discoveryengine.googleapis.com/v1alpha/projects/${GOOGLE_CLOUD_PROJECT}/locations/global/collections/default_collection/engines/${AS_APP}/assistants/${ASSISTANT_ID}/agents")
    
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        agent_count=$(echo "$response_body" | jq '.agents | length' 2>/dev/null || echo "0")
        echo "   Found $agent_count agent(s)"
        echo "$response_body" | jq -r '.agents[]? | "   - \(.name | split("/") | last)\n     Display: \(.displayName)"' 2>/dev/null
    else
        echo "   ❌ Failed to list agents (HTTP $http_code)"
        echo "$response_body" | jq . 2>/dev/null || echo "$response_body"
    fi
fi

echo ""
echo "✅ Validation complete!"
