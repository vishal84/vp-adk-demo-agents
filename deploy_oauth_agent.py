import os
import vertexai
from vertexai import agent_engines
from vertexai.preview import reasoning_engines
from dotenv import load_dotenv

# Import your agent definition from its nested location
from agents.oauth_agent.agent import root_agent

load_dotenv()

# --- Configuration ---
# Load all necessary variables from your .env file
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
STAGING_BUCKET = os.getenv("STAGING_BUCKET")

AGENT_DISPLAY_NAME = os.getenv("AGENT_DISPLAY_NAME")
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")


# --- Initialize Vertex AI ---
vertexai.init(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    staging_bucket=STAGING_BUCKET,
)

# --- Package the Agent for Deployment ---
app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

# --- Deploy to Agent Engine ---
print("Deploying agent to Vertex AI Agent Engine...")

remote_app = agent_engines.create(
    agent_engine=app,
    display_name=f"{AGENT_DISPLAY_NAME}",
    # --- POTENTIAL CHANGE 1: REQUIREMENTS ---
    # If your agent uses other libraries (e.g., for OAuth), add them here.
    # requirements=["google-cloud-aiplatform[adk,agent_engines]", "google-auth-oauthlib"],
    requirements=[
        "google-cloud-aiplatform[adk,agent_engines]",
        "dotenv", # If you use load_dotenv in the agent itself
        "google-auth-oauthlib" # A common one for OAuth
    ],
    # This correctly points to your nested agent code
    extra_packages=["./agents"],
    # --- CRITICAL CHANGE 2: ENVIRONMENT VARIABLES ---
    # You MUST pass all environment variables the agent needs to run on the server.
    # The .env file is NOT sent to the cloud.
    env_vars={
        "STAGING_BUCKET": f"{STAGING_BUCKET}",
        # Add all other required variables for your agent here
        "OAUTH_CLIENT_ID": f"{OAUTH_CLIENT_ID}",
        "OAUTH_CLIENT_SECRET": f"{OAUTH_CLIENT_SECRET}",
    }
)

print(f"Agent deployed successfully! 🚀")
print(f"Resource Name: {remote_app.resource_name}")
