import os
import json
import sys
import google.cloud.logging
from datetime import datetime
import time

from dotenv import load_dotenv

import vertexai
from vertexai.preview import reasoning_engines

from google.adk.agents import LlmAgent, Agent
from google.adk.agents.callback_context import CallbackContext

from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.adk.tools.tool_context import ToolContext

from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes, OAuth2Auth
from google.adk.auth.auth_tool import AuthConfig

from fastapi.openapi.models import OAuth2, OAuthFlowAuthorizationCode, OAuthFlows
from google.auth.transport.requests import Request
import google.oauth2.id_token

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

# Load environment variables from .env file
load_dotenv()
print("loading .env")

# --- Configuration ---
# Standard Google OAuth Endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Load OAuth config from environment
OAUTH_CLIENT_ID = os.environ.get("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.environ.get("OAUTH_CLIENT_SECRET")

# Define SCOPES as a dictionary for ADK, with descriptions for the Dev UI consent screen.
SCOPES_DICT = {
    "openid": "OpenID Connect scope for user identity.",
    "https://www.googleapis.com/auth/userinfo.email": "View your email address.",
    "https://www.googleapis.com/auth/cloud-platform": "Access Google Cloud services on your behalf."
}
# Convert SCOPES_DICT keys to a list for the Credentials object
SCOPES_LIST = list(SCOPES_DICT.keys())

# Load GCP Project ID
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")

MODEL_ID = os.getenv("MODEL_ID")

# --- Guardrail: Check if all necessary variables are loaded ---
required_vars = {
    "OAUTH_CLIENT_ID": OAUTH_CLIENT_ID,
    "OAUTH_CLIENT_SECRET": OAUTH_CLIENT_SECRET,
    "GOOGLE_CLOUD_PROJECT": GOOGLE_CLOUD_PROJECT,
    "GOOGLE_CLOUD_LOCATION": GOOGLE_CLOUD_LOCATION,
    "MODEL_ID": MODEL_ID,
}
missing_vars = [name for name, value in required_vars.items() if not value]
if missing_vars:
    print(f"Error: Missing environment variables: {', '.join(missing_vars)}", file=sys.stderr)
    print("Please check your .env file and ensure all variables are set.", file=sys.stderr)
    sys.exit(1)

print(f"--- OAuth2 Debug Info ---")
print(f"OAUTH_CLIENT_ID: {OAUTH_CLIENT_ID}")
print("Please ensure your Google Cloud OAuth 2.0 Client ID is configured with the correct redirect URIs.")
print("For local development with 'adk web', the redirect URI is typically 'http://localhost:8080/oauth2/callback'.")
print("--- End OAuth2 Debug Info ---")

# Key to retrieve/store creds in the session state.
TOKEN_STATE_KEY = "oauth_tool_tokens"

# --- Initialize Vertex AI ---
vertexai.init(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
)
print(f"Vertex AI initialized for project {GOOGLE_CLOUD_PROJECT} in {GOOGLE_CLOUD_LOCATION}.")

# --- Helper Function: Get User Email from Credentials ---
def _get_user_email_from_creds(creds: Credentials) -> str | None:
    """Fetches user email using provided Google OAuth credentials."""
    try:
        print(f"access token ", creds.token)
        user_info_service = build('oauth2', 'v2', credentials=creds)
        user_info = user_info_service.userinfo().get().execute()
        return user_info.get('email')
    except Exception as e:
        print(f"Error fetching user info with provided credentials: {e}", file=sys.stderr)
        return None

# --- Callback: prereq_setup (Runs before agent processes each turn) ---
def prereq_setup(callback_context: CallbackContext):
    """
    This callback runs before the agent processes each turn.
    It checks for existing authentication and populates user email if available,
    and adds current time context.
    """
    print("\n**** PREREQ SETUP (before_agent_callback) ****")

    # Initialize context variables with default values to prevent KeyError
    callback_context.state['_tz'] = "Unknown"
    callback_context.state['_time'] = "Unknown"
    callback_context.state['_user_email'] = "Not authenticated" # Default value

    # Add current datetime and timezone to state for agent's context
    try:
        callback_context.state['_tz'] = time.tzname[time.daylight]
        now = datetime.now()
        callback_context.state["_time"] = now.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Warning: Could not determine timezone or datetime: {e}", file=sys.stderr)

    # Check for existing authentication and populate user email if available
    if TOKEN_STATE_KEY in callback_context.state:
        try:
            stored_tokens = callback_context.state[TOKEN_STATE_KEY]
            creds = Credentials.from_authorized_user_info(stored_tokens, SCOPES_LIST)

            # Attempt to refresh token proactively if expired
            if creds and creds.expired and creds.refresh_token:
                print("Callback: Attempting to refresh expired token proactively.")
                creds.refresh(Request())
                # Update stored tokens if refresh was successful
                callback_context.state[TOKEN_STATE_KEY] = json.loads(creds.to_json())
                print("Callback: Token refreshed successfully.")

            if creds and creds.valid:
                user_email = _get_user_email_from_creds(creds)
                if user_email:
                    callback_context.state['_user_email'] = user_email
                    print(f"Callback: User already authenticated as {user_email} (from session state).")
                else:
                    # If email couldn't be retrieved despite valid creds
                    callback_context.state['_user_email'] = "Authenticated, but email not found"
                    
            else:
                # If credentials are no longer valid, clear them to force re-auth
                print("Callback: Stored tokens invalid/expired, clearing from state.")
                del callback_context.state[TOKEN_STATE_KEY]
                # Ensure _user_email is reset if tokens are invalid
                callback_context.state['_user_email'] = "Not authenticated"

        except Exception as e:
            print(f"Callback: Error processing stored tokens: {e}. Clearing state.", file=sys.stderr)
            if TOKEN_STATE_KEY in callback_context.state:
                del callback_context.state[TOKEN_STATE_KEY]
            # Ensure _user_email is reset on error
            callback_context.state['_user_email'] = "Not authenticated (Error during token processing)"

# --- Tool: authenticate_user_tool ---
def authenticate_user_tool(tool_context: ToolContext):
    """
    Handles the Google OAuth 2.0 authorization code flow within the ADK agent.
    This tool initiates the OAuth flow if credentials are not present or valid,
    and stores valid credentials in the session state.
    """
    print("\n--- Running authenticate_user_tool ---")
    creds = None

    # Check if valid tokens exist in the session state
    if TOKEN_STATE_KEY in tool_context.state:
        try:
            stored_tokens = tool_context.state[TOKEN_STATE_KEY]
            creds = Credentials.from_authorized_user_info(stored_tokens, SCOPES_LIST)
            print("Auth Tool: Loaded credentials from session state.")
        except Exception as e:
            print(f"Auth Tool: Error loading stored credentials: {e}. Will attempt re-authentication.", file=sys.stderr)
            creds = None # Force re-auth if loading fails
            # Clear invalid tokens from state
            if TOKEN_STATE_KEY in tool_context.state:
                del tool_context.state[TOKEN_STATE_KEY]
            if '_user_email' in tool_context.state:
                del tool_context.state['_user_email']

    # If credentials are not valid (or didn't exist/loaded), try to refresh or request new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Attempt to refresh the token if expired and refresh_token is available
            try:
                creds.refresh(Request())
                print("Auth Tool: Token refreshed successfully.")
            except Exception as e:
                print(f"Auth Tool: Failed to refresh token: {e}. Will request new authorization.", file=sys.stderr)
                creds = None # Force full re-auth if refresh fails
        else:
            # Define the OAuth scheme as required by ADK
            auth_scheme = OAuth2(
                flows=OAuthFlows(
                    authorizationCode=OAuthFlowAuthorizationCode(
                        authorizationUrl=GOOGLE_AUTH_URL,
                        tokenUrl=GOOGLE_TOKEN_URL,
                        scopes=SCOPES_DICT, # Pass the dictionary of scopes here
                    )
                )
            )
            # Define the raw authentication credential
            auth_credential = AuthCredential(
                auth_type=AuthCredentialTypes.OAUTH2,
                oauth2=OAuth2Auth(
                    client_id=OAUTH_CLIENT_ID, client_secret=OAUTH_CLIENT_SECRET
                ),
            )
            auth_config = AuthConfig(
                auth_scheme=auth_scheme, raw_auth_credential=auth_credential
            )

            # Check if an OAuth response is available (e.g., user just completed the flow)
            auth_response = tool_context.get_auth_response(auth_config)

            if auth_response and auth_response.oauth2:
                # ADK exchanged the access token already for us
                access_token = auth_response.oauth2.access_token
                refresh_token = auth_response.oauth2.refresh_token
                id_token = auth_response.oauth2.id_token
                creds = Credentials(
                    token=access_token,
                    id_token=id_token,
                    refresh_token=refresh_token,
                    token_uri=GOOGLE_TOKEN_URL,
                    client_id=OAUTH_CLIENT_ID,
                    client_secret=OAUTH_CLIENT_SECRET,
                    scopes=SCOPES_LIST, # Use the list of scope strings here
                )
                print(f"Auth Tool: Received new tokens via ADK's auth_response. {creds.id_token} (id token) {creds.token} (auth token)")
            else:
                # If there's no auth response, request the user to go through the OAuth flow
                tool_context.request_credential(auth_config)
                # Return a message to the LLM to inform the user that authentication is pending.
                return {
                    "tool_code": "oauth_pending",
                    "panel_markdown": "Please allow pop-ups and complete the OAuth authorization process to proceed. This is required for me to access your Google profile.",
                    "response": "Authentication required. Please check the pop-up window or follow the instructions in the Dev UI to authorize."
                }

    # If we have valid credentials at this point, store them and return success
    if creds and creds.valid:
        # Store credentials (as JSON-serializable dict) in session state for future use
        tool_context.state[TOKEN_STATE_KEY] = json.loads(creds.to_json())
        user_email = _get_user_email_from_creds(creds)

        if user_email:
            tool_context.state['_user_email'] = user_email # Store email in state for access by agent instruction

            print(f"Auth Tool: Authentication successful for {user_email}.")
            return {"result": f"Authentication successful for {user_email}. You can now proceed."}
        else:
            print("Auth Tool: Authentication successful, but could not retrieve user email.")
            return {"result": "Authentication successful, but I could not retrieve your email. Please check the granted scopes or try again."}
    else:
        # Fallback if somehow no valid creds were obtained
        print("Auth Tool: Authentication process incomplete or failed after all attempts.")
        return {"result": "Authentication process incomplete or failed. Please try again."}

# --- Define the MCP Toolset ---
def get_id_token():
    """Get an ID token to authenticate with the MCP server."""
    target_url = "https://zoo-mcp-server-505636788486.us-central1.run.app/mcp/"
    audience = target_url.split('/mcp/')[0]
    request = Request()
    id_token = google.oauth2.id_token.fetch_id_token(request, audience)
    return id_token

mcp_tools = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://zoo-mcp-server-505636788486.us-central1.run.app/mcp/",
        headers={
            "Authorization": f"Bearer { get_id_token() }",
        },
    )
)

# --- Define the Agents and Sub-Agents ---
zoo_mcp_tool_agent = Agent(
    name="zoo_mcp_tool_agent",
    model=str(MODEL_ID),
    instruction=f"""
    You are a helpful agent for the Zoo MCP tool.
    Your primary goal is to assist users in interacting with the Zoo MCP server.
    You can lookup the list of tools the MCP server has to offer and return them.
    You can also call the tools to get information about animals in the zoo.
    Answer any questions related to zoo animals as if you were a zookeeper.
    """,
    tools=[
        mcp_tools
    ]
)

root_agent = LlmAgent(
    name="root_agent",
    model=str(MODEL_ID),
    instruction=f"""
    You are a helpful end user authentication agent.
    Your primary goal is to help users authenticate via Google OAuth2 and retrieve their profile information, specifically their email address.
    After authenticating, you can use the tools from the MCP toolset to answer questions.

    Here is some current context about the user's authentication status:
    - Current server timezone: {{{{_tz}}}}
    - Current server datetime: {{{{_time}}}}
    - User's email (if authenticated): {{{{_user_email}}}}

    When the user first interacts, or if they explicitly ask to authenticate, log in, or verify their identity, you must call ONLY the `authenticate_user_tool` to guide them through the OAuth process. Do not call any other tool until authentication is complete.
    If the user is already authenticated, you should confirm their email or state that they are already logged in, but do not call authentication again.
    Use the `zoo_mcp_tool_agent` to interact with the Zoo MCP server after authentication is complete.
    """,
    sub_agents=[
        zoo_mcp_tool_agent
    ],
    tools=[
        authenticate_user_tool,
    ],
    before_agent_callback=[prereq_setup],
)

# --- Initialize ADK App ---
app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)