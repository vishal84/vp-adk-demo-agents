import asyncio
import argparse
import os
import logging
from google.adk.sessions import VertexAiSessionService
from google.adk.runner import Runner
from google.adk import agents

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
# Ensure these environment variables are set in your terminal.
PROJECT_ID = os.environ.get("GCP_PROJECT")
LOCATION = os.environ.get("GCP_LOCATION")

async def main(session_id: str, message_text: str):
    """
    Connects to an existing ADK session and sends a message to it,
    simulating an external client interaction.
    """
    if not PROJECT_ID or not LOCATION:
        raise EnvironmentError("GCP_PROJECT and GCP_LOCATION must be set as environment variables.")
    
    if not session_id:
        raise ValueError("A session_id must be provided.")

    logger.info(f"Attempting to send message to session: {session_id}")

    # We need a session service to interact with the backend.
    session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION)

    # We use a "dummy" runner here. Its main purpose is to provide the
    # run_async method to correctly format and send the event.
    # The agent within it doesn't matter for this operation.
    dummy_runner = Runner(
        agent=agents.LlmAgent(name="DummyAgent"), # A placeholder agent
        app_name="long-running-monitor", # Must match the app_name of the session
        session_service=session_service
    )

    # Use a unique user ID to simulate a different client.
    client_user_id = "external-client-123"

    # The run_async call will add a new message event to the session history.
    # The background poller in your main agent will detect this new event.
    async for event in dummy_runner.run_async(
        session_id=session_id,
        user_id=client_user_id,
        new_message=agents.Message(message_text),
    ):
        # We don't need to process the dummy agent's response,
        # just log that the message was sent.
        if event.is_final_response():
            logger.info("Successfully sent message to the session.")

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Send a message to an active ADK session.")
    parser.add_argument("session_id", type=str, help="The ID of the session to interact with.")
    parser.add_argument(
        "--message",
        type=str,
        default="Hello from an external client! This is a test.",
        help="The message to send."
    )
    args = parser.parse_args()
    
    asyncio.run(main(args.session_id, args.message))

