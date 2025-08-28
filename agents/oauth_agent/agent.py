
import datetime
import json
import os
from typing import Any, Dict
from dotenv import load_dotenv
from google.adk.tools.tool_context import ToolContext
from google.adk.tools import BaseTool
from google.oauth2.credentials import Credentials
from google.adk.auth import AuthConfig
from google.adk.auth.auth_credential import (
    AuthCredential,
    AuthCredentialTypes,
    OAuth2Auth,
)
from fastapi.openapi.models import OAuth2
from fastapi.openapi.models import OAuthFlowAuthorizationCode
from fastapi.openapi.models import OAuthFlows
from google.auth.transport.requests import Request
from google.adk.agents import Agent

load_dotenv()

# Load OAuth config from environment
OAUTH_AUTH_URL = str(os.environ.get("OAUTH_AUTH_URL"))
OAUTH_TOKEN_URL = str(os.environ.get("OAUTH_TOKEN_URL"))
OAUTH_CLIENT_ID = os.environ.get("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.environ.get("OAUTH_CLIENT_SECRET")
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/cloud-platform",
]

# Key to store creds in the cache (ToolContext)
CREDS_CACHE_KEY = "user_creds_key"

# Define the AuthScheme
auth_scheme = OAuth2(
    flows=OAuthFlows(
        authorizationCode=OAuthFlowAuthorizationCode(
            authorizationUrl=OAUTH_AUTH_URL,
            tokenUrl=OAUTH_TOKEN_URL,
            scopes={scope: scope for scope in SCOPES},
        )
    )
)

# Define the AuthCredential
# Use environment variables or secrets to store the client secrets
auth_credential = AuthCredential(
    auth_type=AuthCredentialTypes.OAUTH2,
    oauth2=OAuth2Auth(client_id=OAUTH_CLIENT_ID, client_secret=OAUTH_CLIENT_SECRET),
)


def before_tool_auth_callback(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext):
    # You can can skip auth checks for specific tools here
    # Returning None will tell the LLM to continue tool execution
    if tool.name.startswith("yyy") or tool.name.endswith("zzz"):
        return None

    creds = None

    # Check if creds exist in cache (i.e. ToolContext)
    cached_token_info = tool_context.state.get(CREDS_CACHE_KEY)
    if cached_token_info:
        try:
            creds = Credentials.from_authorized_user_info(cached_token_info, SCOPES)
            if not creds.valid and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                tool_context.state[CREDS_CACHE_KEY] = json.loads(
                    creds.to_json()
                )  # Update cache
            elif not creds.valid:
                creds = None  # Invalid, needs re-auth
                tool_context.state[CREDS_CACHE_KEY] = None
        except Exception as e:
            creds = None
            tool_context.state[CREDS_CACHE_KEY] = None

    if creds and creds.valid:
        # Inside your tool function, after obtaining 'creds' (either refreshed or newly exchanged)
        # Cache the new/refreshed tokens
        tool_context.state[CREDS_CACHE_KEY] = json.loads(creds.to_json())

        return None
    else:
        exchanged_credential = tool_context.get_auth_response(
            AuthConfig(
                auth_scheme=auth_scheme,
                raw_auth_credential=auth_credential,
            )
        )

        # If exchanged_credential is not None, then there is already an exchanged credetial from the auth response.
        if exchanged_credential is not None:
            # ADK 1.13.0: exchanged_credential may be an OAuth2Auth or have .oauth2
            if hasattr(exchanged_credential, "oauth2") and exchanged_credential.oauth2 is not None:
                oauth = exchanged_credential.oauth2
            else:
                oauth = exchanged_credential  # Assume it's already an OAuth2Auth

            tool_context.state[CREDS_CACHE_KEY] = {
                "client_id": OAUTH_CLIENT_ID,
                "client_secret": OAUTH_CLIENT_SECRET,
                "token": getattr(oauth, "access_token", None),
                "refresh_token": getattr(oauth, "refresh_token", None),
            }
            return None

        else:
            tool_context.request_credential(
                AuthConfig(
                    auth_scheme=auth_scheme,
                    raw_auth_credential=auth_credential,
                )
            )

            return {"pending": True, "message": "Awaiting user authentication."}

def call_api(text: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        text (str): The users question.

    Returns:
        dict: status and result or error msg.
    """
    if text.lower() == "new york":
        return {
            "status": "success",
            "report": (
                "The weather in New York is sunny with a temperature of 25 degrees"
                " Celsius (77 degrees Fahrenheit)."
            ),
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{text}' is not available.",
        }

root_agent = Agent(
    name="oauth_agent",
    model="gemini-2.5-flash",
    description=(
        "Agent that retrieves an OAuth 2.0 token and uses it for calling a REST API."
    ),
    instruction=(
        """You are an OAuth 2.0 agent who can help users authenticate to Google Cloud IAM 
        with the client credentials provided.
        """
    ),
    tools=[call_api],
    before_tool_callback=before_tool_auth_callback
)