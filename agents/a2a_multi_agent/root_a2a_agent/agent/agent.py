"""
Root A2A Agent - A2A Client/Orchestrator

This agent acts as the entry point for user requests and orchestrates
downstream A2A agents. It handles OAuth authentication and passes the
bearer token to downstream agents via the A2A protocol.
"""

import os
import logging
from pathlib import Path
from typing import Callable

import httpx
from fastapi.openapi.models import OAuth2
from fastapi.openapi.models import OAuthFlowAuthorizationCode
from fastapi.openapi.models import OAuthFlows

from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.auth.auth_credential import AuthCredential
from google.adk.auth.auth_credential import AuthCredentialTypes
from google.adk.auth.auth_credential import OAuth2Auth
from google.adk.tools import ToolContext

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
DOWNSTREAM_AGENT_URL = os.getenv("DOWNSTREAM_AGENT_URL", "http://localhost:8001")
CLIENT_ID = os.getenv("CLIENT_ID", "")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")


# =============================================================================
# OAuth2 Configuration
# =============================================================================

auth_scheme = OAuth2(
    flows=OAuthFlows(
        authorizationCode=OAuthFlowAuthorizationCode(
            authorizationUrl="https://accounts.google.com/o/oauth2/auth",
            tokenUrl="https://oauth2.googleapis.com/token",
            refreshUrl="https://oauth2.googleapis.com/token",
            scopes={
                "https://www.googleapis.com/auth/cloud-platform": "Cloud Platform access",
                "https://www.googleapis.com/auth/bigquery": "BigQuery access",
                "https://www.googleapis.com/auth/userinfo.email": "Email access",
                "openid": "OpenID Connect",
            },
        )
    )
)

auth_credential = AuthCredential(
    auth_type=AuthCredentialTypes.OAUTH2,
    oauth2=OAuth2Auth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri="http://127.0.0.1:8000/dev-ui/",
    ),
)


# =============================================================================
# HTTP Client Factory for A2A with Auth Headers
# =============================================================================

def create_a2a_client_factory(tool_context: ToolContext) -> Callable[[], httpx.AsyncClient]:
    """
    Creates a factory function that produces httpx.AsyncClient instances
    with the bearer token from the session state injected into headers.
    
    This enables authenticated A2A calls to downstream agents.
    """
    def client_factory() -> httpx.AsyncClient:
        bearer_token = None
        
        # Try to get bearer token from tool context state
        if tool_context and hasattr(tool_context, 'state'):
            bearer_token = tool_context.state.get("bearer_token")
            
        headers = {
            "Content-Type": "application/json",
        }
        
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
            logger.info("A2A client created with bearer token authentication")
        else:
            logger.warning("A2A client created without bearer token - downstream auth may fail")
            
        return httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(60.0, connect=10.0)
        )
    
    return client_factory


# =============================================================================
# Custom Tool for Capturing Auth Token
# =============================================================================

def capture_auth_token(
    access_token: str,
    tool_context: ToolContext
) -> dict:
    """
    Captures and stores the OAuth access token in session state.
    
    This tool should be called after successful OAuth authentication to
    store the token for use by downstream A2A agents.
    
    Args:
        access_token: The OAuth2 access token to store.
        tool_context: ADK tool context for state management.
        
    Returns:
        dict: Status confirmation.
    """
    tool_context.state["bearer_token"] = access_token
    logger.info("Bearer token captured and stored in session state")
    
    return {
        "status": "success",
        "message": "Authentication token stored successfully. You can now query data."
    }


def get_auth_status(tool_context: ToolContext) -> dict:
    """
    Checks if authentication has been completed.
    
    Args:
        tool_context: ADK tool context for state management.
        
    Returns:
        dict: Authentication status.
    """
    has_token = "bearer_token" in tool_context.state
    
    return {
        "authenticated": has_token,
        "message": "Ready to query data" if has_token else "Please authenticate first"
    }


# =============================================================================
# Remote A2A Agent Configuration
# =============================================================================

# Create the RemoteA2aAgent that connects to the downstream BigQuery agent
# Note: The client_factory will be set up at runtime when we have tool_context
bigquery_remote_agent = RemoteA2aAgent(
    name="bigquery_agent",
    description="A remote agent that can query BigQuery datasets. "
                "Delegate data analysis and SQL query tasks to this agent. "
                "It can list tables, get schemas, and run SQL queries.",
    agent_card_url=f"{DOWNSTREAM_AGENT_URL}/.well-known/agent.json",
)


# =============================================================================
# Root Agent Definition
# =============================================================================

root_agent = LlmAgent(
    name="data_orchestrator",
    model="gemini-2.0-flash",
    description="An orchestrator agent that coordinates data analysis tasks. "
                "It handles user authentication and delegates queries to "
                "specialized downstream agents.",
    instruction="""You are a data orchestration agent that helps users analyze data.

## Your Capabilities:
1. **Authentication**: Help users authenticate with their Google account
2. **Data Analysis**: Delegate data queries to the BigQuery agent

## Workflow:
1. When a user first asks about data, check their authentication status
2. If not authenticated, guide them through the OAuth flow
3. Once authenticated, delegate data queries to the bigquery_agent

## Important Notes:
- Always verify authentication before attempting data queries
- The bigquery_agent can list tables, show schemas, and run SQL queries
- Pass data analysis questions directly to the bigquery_agent
- Summarize results from the bigquery_agent for the user

## Authentication Flow:
When users need to authenticate:
1. The OAuth flow will be initiated automatically
2. After authentication, use capture_auth_token to store the token
3. Then proceed with their data request

You are the coordinator - delegate appropriately and provide clear summaries.
""",
    tools=[capture_auth_token, get_auth_status],
    sub_agents=[bigquery_remote_agent],
    # Auth configuration for OAuth flow
    # auth_scheme=auth_scheme,
    # auth_credential=auth_credential,
)
