import asyncio
import argparse
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from google.adk.sessions import VertexAiSessionService
from google.adk import Runner, agents
from google.genai import types as genai_types

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from the same directory as this file
load_dotenv(dotenv_path='.env')

PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
LOCATION = os.getenv('GOOGLE_CLOUD_LOCATION')

logger.info(f"PROJECT_ID: {PROJECT_ID}")
logger.info(f"LOCATION: {LOCATION}")
logger.info(f"Gen AI: {os.getenv('GOOGLE_GENAI_USE_VERTEXAI')}")

async def main(session_id: str, message_text: str):
    if not PROJECT_ID or not LOCATION:
        raise EnvironmentError("GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION must be set as environment variables.")
    
    if not session_id:
        raise ValueError("A session_id must be provided.")

    logger.info(f"Attempting to send message to session: {session_id}")

    session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION)

    dummy_runner = Runner(
        agent=agents.LlmAgent(name="DummyAgent"),
        app_name="projects/gsi-gemini-ent/locations/us-central1/reasoningEngines/2670373994774921216", # This must match the app_name used by the main agent
        session_service=session_service
    )

    client_user_id = "external-cx-client"
    new_message = genai_types.Content(parts=[genai_types.Part(text=message_text)])

    async for event in dummy_runner.run_async(
        session_id=session_id,
        user_id=client_user_id,
        new_message=new_message,
    ):
        if event.is_final_response():
            logger.info("Successfully sent message to the session.")

if __name__ == "__main__":
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
