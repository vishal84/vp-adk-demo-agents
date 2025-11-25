# MCP Auth Server

This server provides an authentication layer for the MCP agent.

## Prerequisites

- Google Cloud SDK installed and configured.
- Docker installed.

## Setup and Deployment

### 1. Authenticate Docker with gcloud

Run the following command to configure Docker to use `gcloud` as a credential helper for authenticating to Artifact Registry.

```bash
gcloud auth configure-docker
```

### 2. Build and Push the Docker Image

Replace `<project-id>`, `<region>`, `<repository>`, and `<image-name>` with your specific values.

```bash
export PROJECT_ID=<project-id>
export REGION=<region>
export REPOSITORY=<repository>
export IMAGE_NAME=<image-name>
export IMAGE_TAG=latest

docker build -t $IMAGE_NAME .

docker tag $IMAGE_NAME:latest $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$IMAGE_NAME:$IMAGE_TAG

docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$IMAGE_NAME:$IMAGE_TAG
```

