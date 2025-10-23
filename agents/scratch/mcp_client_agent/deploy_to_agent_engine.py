import os
import vertexai
from vertexai import agent_engines
from vertexai.preview import reasoning_engines
from dotenv import load_dotenv

from mcp_client_agent.agent import root_agent

load_dotenv()

# Load GCP Project ID
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
STAGING_BUCKET = os.getenv("STAGING_BUCKET")
AGENT_DISPLAY_NAME = os.getenv("AGENT_DISPLAY_NAME")

AUTH_ID = os.getenv("AUTH_ID")
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")

app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

vertexai.init(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    staging_bucket=STAGING_BUCKET,
)

agent_config = {
    "agent_engine": app,
    "display_name": AGENT_DISPLAY_NAME,
    "requirements": [
        "google-cloud-aiplatform[adk,agent_engines]",
        "dotenv",
        "google-auth-oauthlib"
    ],
    "extra_packages": [
        "mcp_client_agent/agent.py"
    ],
    "env_vars": {
        "STAGING_BUCKET": f"{STAGING_BUCKET}",
        "OAUTH_CLIENT_ID": f"{OAUTH_CLIENT_ID}",
        "OAUTH_CLIENT_SECRET": f"{OAUTH_CLIENT_SECRET}",
    }
}

existing_agents = list(
    agent_engines.list(filter=f'display_name="{AGENT_DISPLAY_NAME}"'))

if existing_agents:
    print(f"Number of existing agents found for {AGENT_DISPLAY_NAME}:" + str(
        len(list(existing_agents))))
    print(existing_agents[0].resource_name)

if existing_agents:
    # update the existing agent
    remote_app = agent_engines.update(
        resource_name=existing_agents[0].resource_name, **agent_config)
else:
    # create a new agent
    remote_app = agent_engines.create(**agent_config)
