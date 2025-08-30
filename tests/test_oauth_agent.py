import os
import uuid
import sys
import vertexai
from vertexai import agent_engines
from dotenv import load_dotenv

# Load environment variables from your .env file
load_dotenv()

# --- Configuration ---
# Ensure these variables are in your .env file
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
ENGINE_ID = os.getenv("ENGINE_ID")

# --- Guardrail: Check if ENGINE_ID was loaded ---
if not ENGINE_ID:
    print("Error: ENGINE_ID not found in environment variables.", file=sys.stderr)
    print("Please check your .env file and ensure the variable is set.", file=sys.stderr)
    sys.exit(1)

# --- Initialize Vertex AI ---
vertexai.init(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
)

# --- Connect to the Deployed Agent ---
print(f"Connecting to agent: {ENGINE_ID}...")
remote_app = agent_engines.AgentEngine(f"{ENGINE_ID}")
remote_app.create()
print("Connection successful! 🚀")

# --- Set up a Session ID ---
# For conversational history, you create and reuse a simple string ID.
session_id = str(uuid.uuid4())
print(f"Using Session ID: {session_id}")
print("-" * 30)

# --- Stream the Response for a Single Message ---
try:
    message = "Hello?"
    print(f"You: {message}")
    print("Agent: ", end="", flush=True)  # Prepare to print stream on one line

    # Use .query() with the stream=True parameter.
    # The message parameter is 'input', not 'message'.
    stream = remote_app.query(
        input=message,
        session_id=session_id,
        stream=True,
    )

    # Iterate over the generator to print the response in real-time.
    for chunk in stream:
        # The content of each chunk is in the 'output' attribute.
        print(chunk.output, end="", flush=True)

    print()  # Adds a newline after the full response is received.

except Exception as e:
    print(f"\nAn error occurred: {e}")

