# SEC EDGAR MCP - Google Cloud Run Deployment

This guide explains how to deploy the SEC EDGAR MCP server to Google Cloud Run.

## Prerequisites

1. **Google Cloud SDK**: Install and configure `gcloud`
   ```bash
   # Install gcloud SDK
   curl https://sdk.cloud.google.com | bash
   source ~/.bashrc
   
   # Authenticate
   gcloud auth login
   gcloud auth application-default login
   ```

2. **Docker**: Ensure Docker is installed and running
   ```bash
   docker --version
   ```

3. **GCP Project**: Have a GCP project with billing enabled

## Quick Deployment

1. **Run the deployment script**:
   ```bash
   ./deploy.sh YOUR_PROJECT_ID us-central1
   ```

   Replace `YOUR_PROJECT_ID` with your actual GCP project ID.

## Manual Deployment Steps

If you prefer manual deployment:

### 1. Set up environment
```bash
export PROJECT_ID="your-gcp-project-id"
export SERVICE_NAME="sec-edgar-mcp"
export REGION="us-central1"
```

### 2. Enable APIs
```bash
gcloud config set project $PROJECT_ID
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 3. Build and push Docker image
```bash
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME .
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME
```

### 4. Deploy to Cloud Run
```bash
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 10 \
    --set-env-vars SEC_EDGAR_USER_AGENT="SEC EDGAR MCP Cloud Run server@yourname.com"
```

## Configuration

### Environment Variables

- `SEC_EDGAR_USER_AGENT`: **Required**. Set to your name and email for SEC compliance
  ```
  SEC_EDGAR_USER_AGENT="Your Name your.email@company.com"
  ```

### Resource Allocation

The default configuration allocates:
- **Memory**: 1 GiB (adjust based on usage)
- **CPU**: 1 vCPU
- **Timeout**: 3600 seconds (1 hour)
- **Max instances**: 10

## Usage

Once deployed, the service will be available via HTTP. The service URL will be displayed after deployment.

### MCP Client Configuration

For MCP clients, use the service URL with the `streamable-http` transport:

```json
{
  "mcpServers": {
    "sec-edgar": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-fetch",
        "https://your-service-url"
      ]
    }
  }
}
```

### Testing the Deployment

```bash
# Health check
curl https://your-service-url/health

# List available tools
curl https://your-service-url/tools
```

## Monitoring and Logs

### View logs
```bash
gcloud run logs read $SERVICE_NAME --region=$REGION
```

### Monitor performance
```bash
gcloud run services describe $SERVICE_NAME --region=$REGION
```

## Updating the Service

To update the service with new code:

1. Build and push new image:
   ```bash
   docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME .
   docker push gcr.io/$PROJECT_ID/$SERVICE_NAME
   ```

2. Deploy update:
   ```bash
   gcloud run deploy $SERVICE_NAME \
       --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
       --region $REGION
   ```

Or simply run the deployment script again:
```bash
./deploy.sh $PROJECT_ID $REGION
```

## Troubleshooting

### Common Issues

1. **Authentication errors**: Ensure you're logged in with `gcloud auth login`
2. **Permission errors**: Check IAM roles (Cloud Run Admin, Storage Admin)
3. **Memory errors**: Increase memory allocation in deployment
4. **Timeout errors**: Increase timeout or optimize queries

### Debug locally
```bash
# Build and run locally
docker build -t sec-edgar-mcp .
docker run -p 8080:8080 -e SEC_EDGAR_USER_AGENT="Test User test@example.com" sec-edgar-mcp

# Test HTTP endpoint
curl http://localhost:8080/health
```

## Security Considerations

- The service is deployed with `--allow-unauthenticated` for easy testing
- For production, consider adding authentication:
  ```bash
  gcloud run deploy $SERVICE_NAME --no-allow-unauthenticated
  ```
- Use IAM to control access to the service
- Consider VPC networking for internal services

## Costs

Cloud Run pricing is based on:
- Request volume
- CPU time
- Memory usage
- Network egress

With the default configuration, costs should be minimal for development use.