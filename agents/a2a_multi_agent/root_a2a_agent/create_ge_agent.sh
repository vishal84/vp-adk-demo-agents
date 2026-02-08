#!/bin/bash

# =============================================================================
# CREATE AGENT ENGINE AGENT - Root A2A Orchestrator Agent
# =============================================================================
# This script deploys the root A2A orchestrator agent to Agent Engine
# Prerequisites:
# 1. Set up .env file with required variables
# 2. Deploy the downstream agent first and get its URL
# 3. Authenticate with gcloud: gcloud auth application-default login
# 4. Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables
if [ -f .env ]; then
    source .env
    echo "✅ Loaded .env file"
else
    echo "❌ Error: .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# Validate required variables
required_vars=("GOOGLE_CLOUD_PROJECT" "GOOGLE_CLOUD_LOCATION" "DOWNSTREAM_AGENT_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set in .env"
        exit 1
    fi
done

echo "🚀 Deploying Root A2A Orchestrator Agent to Agent Engine..."
echo "   Project: $GOOGLE_CLOUD_PROJECT"
echo "   Location: $GOOGLE_CLOUD_LOCATION"
echo "   Downstream Agent: $DOWNSTREAM_AGENT_URL"

# Sync dependencies
echo "📦 Installing dependencies..."
uv sync

# Build the wheel
echo "🔨 Building agent package..."
uv build

# Deploy to Agent Engine using ADK CLI
echo "🚀 Deploying to Agent Engine..."
adk deploy agent_engine \
    --project "$GOOGLE_CLOUD_PROJECT" \
    --region "$GOOGLE_CLOUD_LOCATION" \
    --agent_folder agent

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Your multi-agent A2A system is now deployed:"
echo "   - Root Agent: Orchestrates requests and handles auth"
echo "   - Downstream Agent: $DOWNSTREAM_AGENT_URL"
echo ""
echo "🔗 Test the agent locally first:"
echo "   adk web"
