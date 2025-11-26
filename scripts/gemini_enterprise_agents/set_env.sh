#!/bin/bash

GOOGLE_CLOUD_PROJECT="insert project id here"
GOOGLE_CLOUD_LOCATION="insert region (i.e. us-east1, us-central1) here"
GOOGLE_GENAI_USE_VERTEXAI=True
MODEL_ID="gemini-2.5-flash"
OAUTH_CLIENT_ID="insert client id here"
OAUTH_CLIENT_SECRET="insert client secret here"
LOCAL_DEV=TRUE
GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/mcp-server-sa.json"