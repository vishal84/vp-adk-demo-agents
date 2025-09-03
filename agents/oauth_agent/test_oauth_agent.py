import os
import sys
import vertexai
import agents.oauth_agent.agent_as as agent_as
from vertexai.preview import reasoning_engines
from dotenv import load_dotenv

# Load environment variables from your .env file
load_dotenv()

# --- Configuration ---
# Ensure these variables are in your .env file
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
OAUTH_ENGINE_ID = os.getenv("OAUTH_ENGINE_ID")

# --- Guardrail: Check if OAUTH_ENGINE_ID was loaded ---
if not OAUTH_ENGINE_ID:
    print("Error: OAUTH_ENGINE_ID not found in environment variables.", file=sys.stderr)
    print("Please check your .env file and ensure the variable is set.", file=sys.stderr)
    sys.exit(1)

# --- Initialize Vertex AI ---
vertexai.init(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
)

# --- Connect to the Deployed Agent ---
print(f"Connecting to agent: {OAUTH_ENGINE_ID}...")

app = reasoning_engines.AdkApp(
    agent=agent_as.root_agent,
    enable_tracing=True,
)

print("Connection successful! 🚀")

# --- Set up a Session ID ---
# Create the session and extract its string ID
session_obj = app.create_session(user_id="u_123")
session_id = session_obj.id

print(f"Using Session ID: {session_id}")
print("-" * 30)

# --- Stream the Response for a Single Message ---
try:
    for event in app.stream_query(
        user_id="u_123",
        session_id=session_id,
        message="Hi, log me in?",
    ):
        print(event)
except Exception as e:
    print(f"\nAn error occurred: {e}")
