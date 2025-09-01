import os
import json
import sys
from datetime import datetime
import time

from dotenv import load_dotenv

from fastapi.openapi.models import OAuth2, OAuthFlowAuthorizationCode, OAuthFlows
import vertexai
from vertexai.preview import reasoning_engines

from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.auth import AuthConfig, AuthCredential, AuthCredentialTypes, OAuth2Auth

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

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
STAGING_BUCKET = os.getenv("STAGING_BUCKET")

MODEL_ID = os.getenv("MODEL_ID")

# --- Guardrail: Check if all necessary variables are loaded ---
required_vars = {
    "OAUTH_CLIENT_ID": OAUTH_CLIENT_ID,
    "OAUTH_CLIENT_SECRET": OAUTH_CLIENT_SECRET,
    "GOOGLE_CLOUD_PROJECT": GOOGLE_CLOUD_PROJECT,
    "GOOGLE_CLOUD_LOCATION": GOOGLE_CLOUD_LOCATION,
    "STAGING_BUCKET": STAGING_BUCKET,
    "MODEL_ID": MODEL_ID,
}
missing_vars = [name for name, value in required_vars.items() if not value]
if missing_vars:
    print(f"Error: Missing environment variables: {', '.join(missing_vars)}", file=sys.stderr)
    print("Please check your .env file and ensure all variables are set.", file=sys.stderr)
    sys.exit(1)

# Key to retrieve/store creds in the session state.
TOKEN_STATE_KEY = "oauth_tool_tokens"


# --- Initialize Vertex AI ---
vertexai.init(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    staging_bucket=STAGING_BUCKET,
)
print(f"Vertex AI initialized for project {GOOGLE_CLOUD_PROJECT} in {GOOGLE_CLOUD_LOCATION}.")


# --- Helper Function: Get User Email from Credentials ---
def _get_user_email_from_creds(creds: Credentials) -> str | None:
    """Fetches user email using provided Google OAuth credentials."""
    try:
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
                creds = Credentials(
                    token=access_token,
                    refresh_token=refresh_token,
                    token_uri=GOOGLE_TOKEN_URL,
                    client_id=OAUTH_CLIENT_ID,
                    client_secret=OAUTH_CLIENT_SECRET,
                    scopes=SCOPES_LIST, # Use the list of scope strings here
                )
                print("Auth Tool: Received new tokens via ADK's auth_response.")
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


# --- Tool: get_user_email_tool ---
def get_user_email_tool(tool_context: ToolContext):
    """
    Outputs the authenticated user's email address from the session state.
    This tool should be called by the agent after successful authentication.
    """
    print("\n--- Running get_user_email_tool ---")
    user_email = tool_context.state.get('_user_email')
    if user_email and user_email != "Not authenticated": # Check for default value
        print(f"Tool: Retrieved user email: {user_email}")
        return {"result": f"Your authenticated email address is: {user_email}"}
    else:
        print("Tool: User email not found in state. Authentication might be required.")
        return {"result": "I don't have your email address. Have you authenticated yet? Please ask me to authenticate you first."}


# --- Define the Root Agent ---
root_agent = LlmAgent(
    name="root_agent",
    model=str(MODEL_ID),
    instruction=f"""
    You are a helpful end user authentication agent.
    Your primary goal is to help users authenticate via Google OAuth2 and retrieve their profile information, specifically their email address.

    Here is some current context about the user's authentication status:
    - Current server timezone: {{_tz}}
    - Current server datetime: {{_time}}
    - User's email (if authenticated): {{_user_email}}

    When the user first interacts, or if they explicitly ask to authenticate, log in, or verify their identity, you must use the `authenticate_user_tool` to guide them through the OAuth process.
    Once successfully authenticated, or if you already know their email from the context, you can use the `get_user_email_tool` to display or confirm their email address.
    If the user is already authenticated, you should confirm their email or state that they are already logged in.
    """,
    tools=[
        authenticate_user_tool,
        get_user_email_tool
    ],
    before_agent_callback=[prereq_setup]
)

# --- Initialize ADK App ---
app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

print("\nADK App created successfully. This file defines your agent for deployment.")
