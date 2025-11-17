#!/bin/bash

# =============================================================================
# This script uploads unstructured documents and their metadata to a 
# Vertex AI Search (formerly Gen App Builder) data store.
#
# Pre-requisites:
# 1. Google Cloud SDK (gcloud) is installed and authenticated.
#    Run `gcloud auth application-default login`.
# 2. A Google Cloud project with the Vertex AI Search API enabled.
# 3. A Vertex AI Search data store has been created.
# 4. A GCS bucket to stage the data for import.
#
# What this script does:
# 1. Creates a local directory with sample documents and a metadata.jsonl file.
# 2. Uploads these files to your GCS bucket.
# 3. Kicks off an import job in your Vertex AI Search data store.
# =============================================================================

source .env

# --- Configuration ---
PROJECT_ID="$GOOGLE_CLOUD_PROJECT"
LOCATION="$GOOGLE_CLOUD_LOCATION"
DATA_STORE_ID="$DATA_STORE_ID"
GCS_BUCKET="$STAGING_BUCKET" # Just the bucket name, no "gs://" prefix
DATA_DIR="data"

# Original PDF data files:
# gs://cloud-samples-data/gen-app-builder/search/stanford-cs-224

# Exit on error
set -e

# Construct the GCS URI for the metadata file
GCS_METADATA_URI="gs://$GCS_BUCKET/metadata.jsonl"

echo "Starting data import into data store '$DATA_STORE_ID'..."

# Import the data into the data store
gcloud discovery-engine data-stores import "$DATA_STORE_ID" \
  --project="$PROJECT_ID" \
  --location="$LOCATION" \
  --gcs-source="$GCS_METADATA_URI" \
  --reconciliation-mode=INCREMENTAL # Options: INCREMENTAL, FULL

echo ""
echo "Import process started. You can monitor the progress in the Google Cloud Console."
echo "It may take some time for the documents to be indexed."

# Clean up local temporary data
echo "Cleaning up local directory '$DATA_DIR' நான்க"
rm -rf "$DATA_DIR"

echo "Script finished successfully."