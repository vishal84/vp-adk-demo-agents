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

required_vars=("GOOGLE_CLOUD_PROJECT" "DATASET_ID" "TABLE_ID" "DATA_FILE" "SCHEMA_FILE")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set in .env"
        exit 1
    fi
done

# --- Script Logic ---
echo "🚀 --- Starting BigQuery data import ---"
echo "Project ID: ${GOOGLE_CLOUD_PROJECT}"
echo "Dataset ID: ${DATASET_ID}"
echo "Table ID: ${TABLE_ID}"
echo "Data file: ${DATA_FILE}"
echo "Schema file: ${SCHEMA_FILE}"

# Check if the data file exists
if [ ! -f "${DATA_FILE}" ]; then
  echo "Error: Data file '${DATA_FILE}' not found."
  exit 1
fi

# Check if the schema file was created successfully
if [ ! -f "${SCHEMA_FILE}" ]; then
  echo "Error: Schema file '${SCHEMA_FILE}' could not be created."
  exit 1
fi

# Construct the full table reference
TABLE_REF="${PROJECT_ID}:${DATASET_ID}.${TABLE_ID}"

# Attempt to create the table first. If it exists, bq load will append/overwrite.
echo "Checking if table '${TABLE_REF}' exists..."
if bq show --format=prettyjson "${TABLE_REF}" > /dev/null 2>&1; then
  echo "Table '${TABLE_REF}' already exists. Overwriting/appending data."
  # Use --autodetect if you don't want to specify schema and want BQ to infer.
  # For consistent results with a known schema, specifying is better.
  bq load \
    --source_format=NEWLINE_DELIMITED_JSON \
    --schema="${SCHEMA_FILE}" \
    --replace \
    "${TABLE_REF}" \
    "${DATA_FILE}"
else
  echo "Table '${TABLE_REF}' does not exist. Creating and loading data."
  bq load \
    --source_format=NEWLINE_DELIMITED_JSON \
    --schema="${SCHEMA_FILE}" \
    "${TABLE_REF}" \
    "${DATA_FILE}"
fi

# Check the exit status of the bq command
if [ $? -eq 0 ]; then
  echo "--- Data import successful! ---"
  echo "You can view your data at: https://console.cloud.google.com/bigquery?project=${PROJECT_ID}&p=${PROJECT_ID}&d=${DATASET_ID}&t=${TABLE_ID}&page=table"
else
  echo "--- Data import failed. Please check the error messages above. ---"
fi

# Clean up the temporary schema file
# rm "${SCHEMA_FILE}"
# echo "Cleaned up temporary schema file: ${SCHEMA_FILE}"
