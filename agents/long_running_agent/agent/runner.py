import os
import logging
import uuid
from pathlib import Path
from dotenv import load_dotenv

import agent # Import from your agent.py
from google.adk import Runner
from google.adk.sessions import VertexAiSessionService
from google.genai import types

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

app_name="long_running_agent"
user_id=str("long_running_agent_uid: "+str(uuid.uuid4()))

# Create the ADK runner with VertexAiSessionService
session_service = VertexAiSessionService(
      project=PROJECT_ID,
      location=LOCATION,
      agent_engine_id="2670373994774921216"
)
runner = Runner(
    agent=agent.root_agent,
    app_name=app_name,
    session_service=session_service,
    resumability_config=ResumabilityConfig(
        enable_resumability=True,
        max_wait_time_seconds=300,
    )
)

# Helper method to send query to the runner
async def call_agent(query, session_id, user_id):
  content = types.Content(role='user', parts=[types.Part(text=query)])
  async for event in runner.run_async(
      user_id=user_id, session_id=session_id, new_message=content):
      if event.is_final_response():
          final_response = event.content.parts[0].text
          print("Agent Response: ", final_response)