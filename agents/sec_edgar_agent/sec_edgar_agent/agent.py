from . import patch_adk
import os
import logging
import google.oauth2.id_token
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes
from google.auth.transport.requests import Request
from google.adk.auth.auth_credential import HttpAuth, HttpCredentials

from fastapi.openapi.models import HTTPBearer
from google.adk.tools.openapi_tool.auth.auth_helpers import token_to_scheme_credential
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

MCP_SERVER_URL=str(os.getenv("MCP_SERVER_URL"))
logger.info(f"🔧 Initializing SEC EDGAR Agent with MCP_SERVER_URL: {MCP_SERVER_URL}")

def get_identity_token():
    """Get an ID token to authenticate with the MCP server."""
    target_url = f"{MCP_SERVER_URL}"
    audience = target_url.split('/mcp')[0]
    request = Request()
    id_token = google.oauth2.id_token.fetch_id_token(request, audience)
    return id_token

# Get identity token for manual header configuration with Cloud Run URL as audience
logger.info("🚀 Getting identity token...")
identity_token = get_identity_token()
logger.info(f"Token received: {identity_token[:50] if identity_token else 'None'}...")

headers = {}
if identity_token:
    headers = {
        "Authorization": f"Bearer {identity_token}",
        "Accept": "application/json, text/event-stream"
    }
    logger.info("✓ Authentication headers configured")
else:
    logger.warning("⚠ Warning: No authentication token available")
    
class AgentspaceHttpAuth(HttpAuth):
    scheme: str = "agentspace_auth_resource"
    credentials: HttpCredentials = HttpCredentials()
    agentspace_authentication_resource_auth_id: str

auth_credential = AuthCredential(
    auth_type=AuthCredentialTypes.HTTP,
    http=AgentspaceHttpAuth(agentspace_authentication_resource_auth_id="sec-edgar-auth")
)
auth_scheme = HTTPBearer(bearerFormat='JWT')

sec_edgar_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=MCP_SERVER_URL,
        headers=headers # Note: using both service account headers and auth_credential for now. Service account headers used for listing tools, auth_credential used for tool calls. 
    ),
    auth_scheme=auth_scheme,
    auth_credential=auth_credential
)

# Create the agent
root_agent = Agent(
    name="sec_edgar_agent",
    model="gemini-2.5-flash",
    description="An SEC EDGAR financial data agent that provides company information, filings analysis, financial statements, and insider trading data",
    tools=[sec_edgar_mcp]
)
