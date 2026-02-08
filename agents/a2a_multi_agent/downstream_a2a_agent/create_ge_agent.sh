#!/bin/bash

# =============================================================================
# CREATE AGENT ENGINE AGENT - Downstream BigQuery Agent
# =============================================================================
# This script deploys the downstream BigQuery agent to Agent Engine
# Prerequisites:
# 1. Set up .env file with required variables
# 2. Authenticate with gcloud: gcloud auth application-default login
# 3. Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh

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
required_vars=("GOOGLE_CLOUD_PROJECT" "GOOGLE_CLOUD_LOCATION")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set in .env"
        exit 1
    fi
done

echo "🚀 Deploying Downstream BigQuery Agent to Agent Engine..."
echo "   Project: $GOOGLE_CLOUD_PROJECT"
echo "   Location: $GOOGLE_CLOUD_LOCATION"

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
echo "📋 Next steps:"
echo "   1. Note the Reasoning Engine resource name from the output above"
echo "   2. Update the root agent's .env with the downstream agent URL"
echo "   3. Deploy the root agent"
echo ""
echo "🔗 Test the agent locally first:"
echo "   adk web"
