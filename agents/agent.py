
import datetime
import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi.openapi.models import OAuth2
from fastapi.openapi.models import OAuthFlowAuthorizationCode
from fastapi.openapi.models import OAuthFlows

import vertexai
from vertexai.preview import reasoning_engines
from vertexai import agent_engines

from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


load_dotenv()

# Load OAuth config from environment
OAUTH_AUTH_URL = os.environ.get("OAUTH_AUTH_URL")
OAUTH_TOKEN_URL = str(os.environ.get("OAUTH_TOKEN_URL"))
OAUTH_CLIENT_ID = os.environ.get("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.environ.get("OAUTH_CLIENT_SECRET")
SCOPES = os.environ.get("SCOPES")

# Load GCP Project ID
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
STAGING_BUCKET = os.getenv("STAGING_BUCKET")
MODEL_ID = os.getenv("MODEL_ID")
AGENT_DISPLAY_NAME = os.getenv("AGENT_DISPLAY_NAME")
AUTH_ID = os.getenv("AUTH_ID")

# Key to retrieve/store creds in the cache (state)
TOKEN_KEY = f"temp:{AUTH_ID}"

def whoami(callback_context: CallbackContext, creds):
    user_info_service = build('oauth2', 'v2', credentials=creds)
    user_info = user_info_service.userinfo().get().execute()
    user_email = user_info.get('email')
    callback_context.state['_user_email'] = user_email

    print(f"User's email address: {user_email}")

def auth_setup(callback_context: CallbackContext):
    print("**** PREREQ SETUP ****")
    access_token = callback_context.state[TOKEN_KEY]
    creds = Credentials(token=access_token)
    whoami(callback_context, creds)

def output_user_info(tool_context: ToolContext):
    user_email = tool_context.state.get('_user_email')
    print(f"User's email address: {user_email}")
    return user_email

# Root agent delegates to the sub-agent (follow sample pattern)
root_agent = LlmAgent(
    model=str(MODEL_ID),
    name="root_agent",
    instruction="""
    You are a helpful end user authentication agent.

    You will authenticate users via OAuth2 and retrieve their profile information.
    After authentication use your tool `output_user_info` to output the user's email address.
    """,
    tools=[output_user_info],
    before_agent_callback=[auth_setup]
)


def deploy_agent_engine_app():
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
            "python-dotenv>=1.0.1",
            "google-adk==1.13.0",
            "google-cloud-aiplatform[adk,agent-engines]==1.110.0"
        ]
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

    return None

if __name__ == "__main__":
    deploy_agent_engine_app()
