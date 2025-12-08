import os
import logging
from pathlib import Path
from . import helper

import google.auth
import google.auth.transport.requests
import google.oauth2.id_token
from google.oauth2 import service_account
from google.auth import impersonated_credentials

from fastapi.openapi.models import OAuth2
from fastapi.openapi.models import OAuthFlowAuthorizationCode
from fastapi.openapi.models import OAuthFlows

from google.adk.agents import LlmAgent
from google.adk.auth.auth_credential import AuthCredential
from google.adk.auth.auth_credential import AuthCredentialTypes
from google.adk.auth.auth_credential import OAuth2Auth
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

from dotenv import load_dotenv

# Load environment variables from the same directory as this file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "MCP SERVER URL NOT SET")
SERVICE_ACCOUNT_EMAIL = os.getenv("SERVICE_ACCOUNT_EMAIL")

auth_scheme = OAuth2(
    flows=OAuthFlows(
        authorizationCode=OAuthFlowAuthorizationCode(
            authorizationUrl="https://accounts.google.com/o/oauth2/auth",
            tokenUrl="https://oauth2.googleapis.com/token",
            refreshUrl="https://oauth2.googleapis.com/token",
            scopes={
                "https://www.googleapis.com/auth/cloud-platform": "Cloud platform scope",
                "https://www.googleapis.com/auth/userinfo.email": "Email access scope",
                "https://www.googleapis.com/auth/userinfo.profile": "Profile access scope",
                "openid": "OpenID Connect scope",
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

def get_cloud_run_token(target_url: str) -> str:
    """
    Fetches an ID token for authenticating to a Cloud Run service.
    
    This function uses Application Default Credentials (ADC) to obtain an identity token
    that can be used to authenticate requests to Cloud Run services that require authentication.
    
    Args:
        target_url: The URL of the Cloud Run service to authenticate to.
        
    Returns:
        str: The ID token that can be used in the Authorization header.
        
    Raises:
        Exception: If unable to fetch the ID token (e.g., authentication failure).
        
    Note:
        Requires the caller to have the run.invoker role on the Cloud Run service.
    """
    auth_req = google.auth.transport.requests.Request()

    target_scopes = [
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid"
    ]

    # source_credentials = (
    #     service_account.Credentials.from_service_account_file(
    #         GOOGLE_APPLICATION_CREDENTIALS,
    #         scopes=target_scopes
    #     )
    # )
    logger.info("Loading source credentials from environment (ADC)...")
    source_credentials, _ = google.auth.default()
    audience = target_url.split('/mcp')[0]
    
    logger.info(f"Source Credentials: {helper.context_to_json(source_credentials)}")

    target_credentials = impersonated_credentials.Credentials(
        source_credentials=source_credentials,
        target_principal=SERVICE_ACCOUNT_EMAIL,
        target_scopes = target_scopes,
    )

    jwt_token = impersonated_credentials.IDTokenCredentials(
        target_credentials=target_credentials,
        target_audience=audience,
        include_email=True,
    )

    try:
        # id_token = google.oauth2.id_token.fetch_id_token(auth_req, audience)
        jwt_token.refresh(auth_req)
        id_token = jwt_token.token

        logger.info(f"ID token: {id_token}")

        if not id_token:
            raise ValueError("Failed to fetch ID token: received None")
        return id_token
    except Exception as e:
        print(f"Error fetching Cloud Run ID token for {target_url}: {e}")
        raise

def mcp_header_provider(context) -> dict[str, str]:
    """
    Provides authentication headers for MCP server requests.
    
    Args:
        context: The context object from the MCP toolset.
        
    Returns:
        dict: Headers including the Bearer token for authentication.
        
    Raises:
        Exception: If unable to get Cloud Run token.
    """
    id_token = get_cloud_run_token(MCP_SERVER_URL)
    logger.info(f"Token: \n{id_token}")
    logger.info(f"Context: \n{helper.context_to_json(context)}")

    return {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

cloud_run_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=MCP_SERVER_URL,
    ),
    header_provider=mcp_header_provider,
    auth_scheme=auth_scheme,
    auth_credential=auth_credential
)

root_agent = LlmAgent(
    model="gemini-2.5-pro",
    name="code_snippet_agent",
    instruction="""You are a helpful agent that has access to an MCP tool used to retrieve code snippets.
    - If a user asks what you can do, answer that you can provide code snippets from the MCP tool you have access to.
    - Provide the function name to call to ask for a snippet:
    - `get_snippet("<type>")` where <type> can be sql, python, javascript, json, or go.
    - Always use the MCP tool to get code snippets, never make up code snippets on your own.
    """,
    tools=[cloud_run_mcp],
)
