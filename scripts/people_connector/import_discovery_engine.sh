#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "Error: .env file not found."
    exit 1
fi

if [ -z "$DATA_STORE_ID" ]; then
    echo "❌ Error: DATA_STORE_ID is not set in .env. Please add it."
    echo "Example: DATA_STORE_ID=\"my-data-store-id\""
    exit 1
fi

echo "🚀 --- Starting Vertex AI Search data import ---"
echo "Project ID: ${GOOGLE_CLOUD_PROJECT}"
echo "Location: ${GOOGLE_CLOUD_LOCATION}"
echo "Data Store ID: ${DATA_STORE_ID}"

# Run the data conversion script to ensure we have the correct format
echo "🔄 Converting data to Discovery Engine format..."
python3 src/prepare_discovery_engine_data.py

IMPORT_FILE="data/organization_data_discovery_engine.json"

if [ ! -f "$IMPORT_FILE" ]; then
    echo "❌ Error: Converted file '$IMPORT_FILE' not found."
    exit 1
fi

echo "📤 Importing documents to Data Store using Python Client..."

# Path to the virtual environment python that has google-cloud-discoveryengine installed
VENV_PYTHON="../../agents/vertex_ai_search_agent/.venv/bin/python"

# Override location to global for Vertex AI Search if needed, or try to use the one from env.
# Often Data Stores are global.
export GOOGLE_CLOUD_LOCATION="global"

if [ -f "$VENV_PYTHON" ]; then
    echo "Using venv python: $VENV_PYTHON"
    "$VENV_PYTHON" src/upload_documents.py
else
    echo "⚠️  Venv python not found at $VENV_PYTHON. Trying system python3..."
    python3 src/upload_documents.py
fi

if [ $? -eq 0 ]; then
    echo "✅ Import completed successfully."
else
    echo "❌ Import failed."
fi
