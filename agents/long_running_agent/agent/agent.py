import asyncio
import uuid
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from google.adk import agents
from google.adk import Runner
from google.adk.agents import LlmAgent
from google.adk.runners import ResumabilityConfig
from google.adk.agents import InvocationContext
from google.adk.sessions import VertexAiSessionService
from google.adk.tools import LongRunningFunctionTool
from google.genai import types as genai_types
from pydantic import Field

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from the same directory as this file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

logger.info(f"PROJECT_ID: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
logger.info(f"LOCATION: {os.getenv('GOOGLE_CLOUD_LOCATION')}")
logger.info(f"Gen AI: {os.getenv('GOOGLE_GENAI_USE_VERTEXAI')}")

active_polling_tasks = {}

# --- 1. Define the Long-Running Tool ---
async def monitor_vertex_ai_session(session_id: str) -> dict:
    """
    Starts monitoring a Vertex AI session for new events.
    When called, this tool will pause the agent and wait for an external
    event to be sent to the session by another client or system.
    """
    logger.info(f"TOOL: Starting to monitor session: {session_id}")
    return {"status": "pending", "ticket_id": str(uuid.uuid4())}

monitor_tool = LongRunningFunctionTool(func=monitor_vertex_ai_session)

# --- 2. Background Polling Task ---
async def poll_session_for_events(
    session_id: str,
    user_id: str,
    original_function_call: genai_types.FunctionCall,
    stop_event: asyncio.Event
):
    """
    This function is self-sufficient. It creates its own service and runner
    to interact with the session from the background.
    """
    logger.info("[POLLER] Starting background polling...")
    
    # The poller creates its own service and runner.
    session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION)
    poller_runner = Runner(
        agent=agents.LlmAgent(name="PollerDummyAgent"), # A placeholder agent
        app_name="long-running-monitor", # Must match the app_name of the session
        session_service=session_service
    )

    num_events_seen = 0
    async for _ in session_service.list_events_async(session_id=session_id):
        num_events_seen += 1
    logger.info(f"[POLLER] Initial event count: {num_events_seen}")

    while not stop_event.is_set():
        try:
            await asyncio.sleep(POLLING_INTERVAL_SECONDS)
            all_events = [e async for e in session_service.list_events_async(session_id=session_id)]

            if len(all_events) > num_events_seen:
                logger.info(f"[POLLER] Detected new events! Total events now: {len(all_events)}")
                new_events = all_events[num_events_seen:]
                
                # Find a new message not sent by the main orchestrator or its sub-agent
                message_event_to_process = next((e for e in new_events if e.content and "Agent" not in e.author), None)

                if message_event_to_process:
                    logger.info(f"[POLLER] Found new message to process from author '{message_event_to_process.author}'")
                    response_payload = {
                        "status": "complete",
                        "new_event_author": message_event_to_process.author,
                        "new_event_content": message_event_to_process.content.parts[0].text,
                    }
                    updated_function_response = agents.Part(
                        function_response=agents.FunctionResponse(
                            id=original_function_call.id,
                            name=original_function_call.name,
                            response=response_payload,
                        )
                    )

                    logger.info("[POLLER] Sending FunctionResponse to wake up the agent...")
                    new_message = genai_types.Content(parts=[updated_function_response])
                    async for event in poller_runner.run_async(session_id=session_id, user_id=user_id, new_message=new_message):
                        if event.is_final_response():
                            logger.info(f"[AGENT] Agent's final response: {event.content.parts[0].text}")

                    logger.info("[POLLER] Event processed successfully. Stopping poller.")
                    stop_event.set()
                
                num_events_seen = len(all_events)
        except asyncio.CancelledError:
            logger.info("[POLLER] Poller task cancelled.")
            break
        except Exception as e:
            logger.error(f"[POLLER] An error occurred during polling: {e}", exc_info=True)
            stop_event.set()

root_agent = LlmAgent(
    model="gemini-2.5-pro",
    name="long_running_agent",
    instruction="""You are a session monitoring assistant. Your primary job is to wait for new events.
        When the user asks you to monitor the session, call the `monitor_tool` tool.
        After calling the tool, respond to the user that you have started monitoring and are now waiting for external events.
        When you receive a FunctionResponse with the new event details, you MUST confirm to the user that a new event was detected and summarize its content clearly.
    """,
    tools=[monitor_tool],
    resumability_config=ResumabilityConfig(
        enable_resumability=True,
        max_wait_time_seconds=3600,
    ),
    
)
