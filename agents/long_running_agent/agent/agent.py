import asyncio
import uuid
import os
import logging
from typing import AsyncGenerator, Dict, Any

from google.adk import agents
from google.adk.sessions import VertexAiSessionService, Session
from google.adk.tools import LongRunningFunctionTool
from google.adk.runner import Runner
from google.adk.runtime import ResumabilityConfig
from google.genai import types as genai_types

# --- Configuration ---
# Configure logging for better visibility
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# These will be automatically populated when deployed on Agent Engine
# For local testing, ensure these environment variables are set in your terminal.
PROJECT_ID = os.environ.get("GCP_PROJECT")
LOCATION = os.environ.get("GCP_LOCATION")
POLLING_INTERVAL_SECONDS = 5

# --- 1. Define the Long-Running Tool ---
async def monitor_vertex_ai_session(session_id: str) -> dict:
    """
    Starts monitoring a Vertex AI session for new events.
    This is a long-running tool that will return a pending status.
    The agent will pause until a FunctionResponse is received.
    """
    logger.info(f"TOOL: Starting to monitor session: {session_id}")
    return {"status": "pending", "ticket_id": str(uuid.uuid4())}

monitor_tool = LongRunningFunctionTool(
    func=monitor_vertex_ai_session,
    description="A tool to monitor a Vertex AI session for new events."
)

# --- 2. Define the Agent ---
monitoring_agent = agents.LlmAgent(
    name="MonitoringAgent",
    instruction=(
        "You are a session monitoring assistant. Your primary job is to wait for new events. "
        "When the user asks you to monitor the session, call the `monitor_vertex_ai_session` tool. "
        "After calling the tool, respond to the user that you have started monitoring and are now waiting for external events. "
        "When you receive a FunctionResponse with the new event details, you MUST confirm to the user that a new event was detected and summarize its content clearly."
    ),
    tools=[monitor_tool],
    model="gemini-1.5-pro-latest"
)

# --- 3. Background Polling Task ---
async def poll_session_for_events(
    runner: Runner,
    session_service: VertexAiSessionService,
    session_id: str,
    user_id: str,
    original_function_call: agents.FunctionCall,
    stop_event: asyncio.Event
):
    """
    Polls the session service for new events in a background loop.
    When a new message is detected, it sends a FunctionResponse to the
    paused agent to 'wake it up' and process the new information.
    """
    logger.info("[POLLER] Starting background polling...")
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
                
                message_event_to_process = None
                for event in new_events:
                    if event.content and event.author != runner.agent.name:
                        message_event_to_process = event
                        logger.info(f"[POLLER] Found new message to process from author '{event.author}'")
                        break

                if message_event_to_process:
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
                    async for event in runner.run_async(
                        session_id=session_id,
                        user_id=user_id,
                        new_message=agents.Message(parts=[updated_function_response]),
                    ):
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

# --- 4. Main Agent Execution Logic & Runner Setup ---
# This dictionary will store active polling tasks, keyed by session ID.
active_polling_tasks = {}

async def run_agent_turn(runner: Runner, session_id: str, user_id: str, message: agents.Message):
    """Handles a single turn of the conversation and manages polling tasks."""
    original_function_call = None
    
    # Run the agent to get its response to the user's message.
    async for event in runner.run_async(session_id=session_id, user_id=user_id, new_message=message):
        if event.is_final_response():
            logger.info(f"Agent initial response: {event.content.parts[0].text}")
        if event.actions and event.actions.function_call:
            original_function_call = event.actions.function_call
            logger.info(f"Agent is calling a tool: {event.actions.tool_code}")

    # If the agent called our long-running tool, start the background poller for this session.
    if original_function_call and original_function_call.name == monitor_tool.name:
        if session_id in active_polling_tasks:
            logger.warning(f"Polling task for session {session_id} already exists. Not starting a new one.")
            return

        logger.info(f"Starting background polling task for session {session_id}...")
        stop_event = asyncio.Event()
        polling_task = asyncio.create_task(
            poll_session_for_events(
                runner=runner,
                session_service=runner.session_service,
                session_id=session_id,
                user_id=user_id,
                original_function_call=original_function_call,
                stop_event=stop_event,
            )
        )
        active_polling_tasks[session_id] = (polling_task, stop_event)

# This is the entry point for the ADK Runner when deployed on Agent Engine
if __name__ == "__main__":
    if not PROJECT_ID or not LOCATION:
        raise EnvironmentError(
            "GCP_PROJECT and GCP_LOCATION must be set as environment variables for local testing."
        )

    # Initialize the session service.
    session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION)
    
    # Initialize the Runner. RESUMABLE is critical for long-running tools.
    runner = Runner(
        agent=monitoring_agent,
        app_name="long-running-monitor",
        session_service=session_service,
        resumability_config=ResumabilityConfig.RESUMABLE,
    )
    
    # Expose the runner's handler function for the web server (like Flask or FastAPI).
    # When deployed, Agent Engine's infrastructure will call this handler.
    # To run locally, you would typically wrap this in a local web server.
    handler = runner.get_handler()
    logger.info("Runner handler created. Ready for deployment or local web server integration.")

    # Example of how to run a test turn locally for debugging:
    async def local_test():
        test_session_id = f"local-test-session-{uuid.uuid4()}"
        test_user_id = "local-user"
        logger.info(f"--- Running Local Test with Session ID: {test_session_id} ---")
        
        # Create the session manually for local test
        await session_service.create_session(
            app_name="long-running-monitor", session_id=test_session_id, user_id=test_user_id
        )

        # 1. Ask the agent to start monitoring
        await run_agent_turn(
            runner,
            session_id=test_session_id,
            user_id=test_user_id,
            message=agents.Message("Please start monitoring this session for new events.")
        )

        logger.info("\n--- Agent is now polling in the background. ---")
        logger.info("--- Run the `client_simulator.py` script in another terminal ---")
        logger.info(f"--- Use the session ID: {test_session_id} ---\n")

        # Keep the local test running to allow the poller to work
        polling_task, stop_event = active_polling_tasks.get(test_session_id)
        if polling_task:
            await polling_task # Wait for the poller to finish

    # To run the local test, uncomment the line below:
    # asyncio.run(local_test())

