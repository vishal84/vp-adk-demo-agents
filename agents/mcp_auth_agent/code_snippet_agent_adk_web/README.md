# Code Snippet Agent (ADK Web)

This agent is designed to be deployed as a web service using the Agent Development Kit (ADK).

## Deployment

To deploy this agent, use the provided `deploy.sh` script. This script triggers a Google Cloud Build job defined in `cloudbuild.yaml`.

The deployment process performs the following steps:
1.  **Cloud Build**: Executes the build steps to package and deploy the agent.
2.  **Infrastructure as Code**: Uses Terraform to provision necessary resources.
3.  **Service Account Creation**: Creates a dedicated service account for the agent.
4.  **Impersonation Grants**: Grants the user specified in `terraform/terraform.tfvars` (via the `username` variable) the permission to impersonate the newly created service account. This allows for secure access and management.

### Usage

Ensure you have your environment variables set (or a `.env` file) and run:

```bash
./deploy.sh
```

## Local Development

You can run the agent locally for development and testing purposes using `uv`.

To start the agent in web mode:

```bash
uv run adk web
```
