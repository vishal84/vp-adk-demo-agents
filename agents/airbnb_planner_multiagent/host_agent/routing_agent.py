# pylint: disable=logging-fstring-interpolation
import asyncio
import json
import os
import uuid

from typing import Any, cast

import httpx

from a2a.client import A2ACardResolver
from a2a.types import (
    AgentCard,
    MessageSendParams,
    Part,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    JSONRPCErrorResponse,
    Task,
    TextPart,
)
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.tool_context import ToolContext
from remote_agent_connection import (
    RemoteAgentConnections,
    TaskUpdateCallback,
)


load_dotenv()


def convert_part(part: Part, tool_context: ToolContext):
    """Convert a part to text. Only text parts are supported."""
    # Try to cast to TextPart if it has text
    try:
        text_part = cast(TextPart, part)
        if text_part.text:
            return text_part.text
    except Exception:
        pass
    
    return str(part)


def convert_parts(parts: list[Part], tool_context: ToolContext):
    """Convert parts to text."""
    rval = []
    for p in parts:
        rval.append(convert_part(p, tool_context))
    return rval


def extract_message_text(message: Any, tool_context: ToolContext) -> str:
    """Extract human-readable text from a TaskStatus.message or similar object."""
    try:
        parts = getattr(message, 'parts', None)
        if parts and isinstance(parts, list):
            texts = convert_parts(parts, tool_context)
            return "\n".join([t for t in texts if t])
    except Exception:
        pass
    # Fallback to str if unknown shape
    return str(message) if message is not None else ""


def create_send_message_payload(
    text: str, task_id: str | None = None, context_id: str | None = None
) -> dict[str, Any]:
    """Helper function to create the payload for sending a task."""
    payload: dict[str, Any] = {
        'message': {
            'role': 'user',
            'parts': [{'type': 'text', 'text': text}],
            'messageId': uuid.uuid4().hex,
        },
    }

    if task_id:
        payload['message']['taskId'] = task_id

    if context_id:
        payload['message']['contextId'] = context_id
    return payload


class RoutingAgent:
    """The Routing agent.

    This is the agent responsible for choosing which remote seller agents to send
    tasks to and coordinate their work.
    """

    def __init__(
        self,
        task_callback: TaskUpdateCallback | None = None,
    ):
        self.task_callback = task_callback
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents: str = ''

    async def _async_init_components(
        self, remote_agent_addresses: list[str]
    ) -> None:
        """Asynchronous part of initialization."""
        # Use a single httpx.AsyncClient for all card resolutions for efficiency
        async with httpx.AsyncClient(timeout=30) as client:
            for address in remote_agent_addresses:
                card_resolver = A2ACardResolver(
                    client, address
                )  # Constructor is sync
                try:
                    card = (
                        await card_resolver.get_agent_card()
                    )  # get_agent_card is async

                    remote_connection = RemoteAgentConnections(
                        agent_card=card, agent_url=address
                    )
                    self.remote_agent_connections[card.name] = remote_connection
                    self.cards[card.name] = card
                except httpx.ConnectError as e:
                    print(
                        f'ERROR: Failed to get agent card from {address}: {e}'
                    )
                except Exception as e:  # Catch other potential errors
                    print(
                        f'ERROR: Failed to initialize connection for {address}: {e}'
                    )

        # Populate self.agents using the logic from original __init__ (via list_remote_agents)
        agent_info = []
        for agent_detail_dict in self.list_remote_agents():
            agent_info.append(json.dumps(agent_detail_dict))
        self.agents = '\n'.join(agent_info)

    @classmethod
    async def create(
        cls,
        remote_agent_addresses: list[str],
        task_callback: TaskUpdateCallback | None = None,
    ) -> 'RoutingAgent':
        """Create and asynchronously initialize an instance of the RoutingAgent."""
        instance = cls(task_callback)
        await instance._async_init_components(remote_agent_addresses)
        return instance

    def create_agent(self) -> Agent:
        """Create an instance of the RoutingAgent."""
        return Agent(
            model='gemini-2.5-flash-lite',
            name='Routing_agent',
            instruction=self.root_instruction,
            before_model_callback=self.before_model_callback,
            description=(
                'This Routing agent orchestrates the decomposition of the user asking for weather forecast or airbnb accommodation'
            ),
            tools=[
                self.send_message,
            ],
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        """Generate the root instruction for the RoutingAgent."""
        current_agent = self.check_active_agent(context)
        return f"""
        **Role:** You are an expert Routing Delegator. Your primary function is to accurately delegate user inquiries regarding weather or accommodations to the appropriate specialized remote agents.

        **Core Directives:**

        * **Task Delegation:** Utilize the `send_message` function to assign actionable tasks to remote agents.
        * **Contextual Awareness for Remote Agents:** If a remote agent repeatedly requests user confirmation, assume it lacks access to the         full conversation history. In such cases, enrich the task description with all necessary contextual information relevant to that         specific agent.
        * **Autonomous Agent Engagement:** Never seek user permission before engaging with remote agents. If multiple agents are required to         fulfill a request, connect with them directly without requesting user preference or confirmation.
        * **Transparent Communication:** Always present the complete and detailed response from the remote agent to the user.
        * **User Confirmation Relay:** If a remote agent asks for confirmation, and the user has not already provided it, relay this         confirmation request to the user.
        * **Focused Information Sharing:** Provide remote agents with only relevant contextual information. Avoid extraneous details.
        * **No Redundant Confirmations:** Do not ask remote agents for confirmation of information or actions.
        * **Tool Reliance:** Strictly rely on available tools to address user requests. Do not generate responses based on assumptions. If         information is insufficient, request clarification from the user.
        * **Prioritize Recent Interaction:** Focus primarily on the most recent parts of the conversation when processing requests.
        * **Active Agent Prioritization:** If an active agent is already engaged, route subsequent related requests to that agent using the         appropriate task update tool.

        **Agent Roster:**

        * Available Agents: `{self.agents}`
        * Currently Active Seller Agent: `{current_agent['active_agent']}`
                """

    def check_active_agent(self, context: ReadonlyContext):
        state = context.state
        if (
            'session_id' in state
            and 'session_active' in state
            and state['session_active']
            and 'active_agent' in state
        ):
            return {'active_agent': f'{state["active_agent"]}'}
        return {'active_agent': 'None'}

    def before_model_callback(
        self, callback_context: CallbackContext, llm_request
    ):
        state = callback_context.state
        if 'session_active' not in state or not state['session_active']:
            if 'session_id' not in state:
                state['session_id'] = str(uuid.uuid4())
            state['session_active'] = True

    def list_remote_agents(self):
        """List the available remote agents you can use to delegate the task."""
        if not self.cards:
            return []

        remote_agent_info = []
        for card in self.cards.values():
            print(f'Found agent card: {card.model_dump(exclude_none=True)}')
            print('=' * 100)
            remote_agent_info.append(
                {'name': card.name, 'description': card.description}
            )
        return remote_agent_info

    async def send_message(
        self, agent_name: str, task: str, tool_context: ToolContext
    ):
        """Sends a task to remote seller agent.

        This will send a message to the remote agent named agent_name.

        Args:
            agent_name: The name of the agent to send the task to.
            task: The comprehensive conversation context summary
                and goal to be achieved regarding user inquiry and purchase request.
            tool_context: The tool context this method runs in.

        Yields:
            A dictionary of JSON data.
        """
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f'Agent {agent_name} not found')
        state = tool_context.state
        state['active_agent'] = agent_name
        client = self.remote_agent_connections[agent_name]

        if not client:
            raise ValueError(f'Client not available for {agent_name}')
        
        # Only use existing task_id if we're continuing a conversation with this specific agent
        # Check if there's an existing task for this agent in this context
        agent_task_key = f'task_id_{agent_name}'
        task_id = state.get(agent_task_key)  # Will be None for new conversations

        if 'context_id' in state:
            context_id = state['context_id']
        else:
            context_id = str(uuid.uuid4())
            state['context_id'] = context_id

        message_id = ''
        metadata = {}
        if 'input_message_metadata' in state:
            metadata.update(**state['input_message_metadata'])
            if 'message_id' in state['input_message_metadata']:
                message_id = state['input_message_metadata']['message_id']
        if not message_id:
            message_id = str(uuid.uuid4())

        payload = {
            'message': {
                'role': 'user',
                'parts': [
                    {'type': 'text', 'text': task}
                ],  # Use the 'task' argument here
                'messageId': message_id,
                'contextId': context_id,  # Always include context_id
            },
        }

        # Only include taskId if we're continuing an existing task
        if task_id:
            payload['message']['taskId'] = task_id

        message_request = SendMessageRequest(
            id=message_id, params=MessageSendParams.model_validate(payload)
        )
        send_response: SendMessageResponse = await client.send_message(
            message_request=message_request
        )
        print(
            'send_response',
            send_response.model_dump_json(exclude_none=True, indent=2),
        )

        # If the remote reports the referenced task is already terminal (e.g., completed),
        # clear the saved task id and retry once without taskId to start a new task.
        if not isinstance(send_response.root, SendMessageSuccessResponse):
            if isinstance(send_response.root, JSONRPCErrorResponse):
                err = send_response.root.error
                msg = (getattr(err, 'message', '') or '').lower()
                code = getattr(err, 'code', None)
                if task_id and (
                    'terminal state' in msg or 'completed' in msg or code == -32602
                ):
                    print(
                        f"Task {task_id} is terminal per remote server; clearing saved task id and retrying without taskId."
                    )
                    if agent_task_key in state:
                        # Avoid `del` to satisfy type checkers; mark as None
                        state[agent_task_key] = None
                    # Build a fresh payload without taskId
                    new_message_id = str(uuid.uuid4())
                    payload2 = {
                        'message': {
                            'role': 'user',
                            'parts': [{'type': 'text', 'text': task}],
                            'messageId': new_message_id,
                            'contextId': context_id,
                        },
                    }
                    message_request2 = SendMessageRequest(
                        id=new_message_id,
                        params=MessageSendParams.model_validate(payload2),
                    )
                    send_response = await client.send_message(
                        message_request=message_request2
                    )
                    print(
                        'send_response (retry)',
                        send_response.model_dump_json(
                            exclude_none=True, indent=2
                        ),
                    )
            # If still not success after potential retry, surface an error to the UI
            if not isinstance(
                send_response.root, SendMessageSuccessResponse
            ):
                if isinstance(send_response.root, JSONRPCErrorResponse):
                    err = send_response.root.error
                    return {
                        "response": f"❌ Failed to send message: {getattr(err, 'message', 'Unknown error')}",
                        "agent": agent_name,
                    }
                return {
                    "response": "❌ Failed to send message: Unknown non-success response",
                    "agent": agent_name,
                }

        if not isinstance(send_response.root.result, Task):
            print('received non-task response. Aborting get task ')
            return None

        initial_task = send_response.root.result
        
        # Store the task_id for this agent so future messages can continue the conversation
        state[agent_task_key] = initial_task.id
        
        # Now poll for task completion
        try:
            print(f"Polling for task completion: {initial_task.id}")
            final_task = await client.wait_for_task_completion(
                initial_task.id, max_wait_seconds=120, poll_interval=1.0
            )
            
            # Normalize state string
            state_val = getattr(getattr(final_task, 'status', None), 'state', None)
            state_str = str(state_val).lower() if state_val is not None else 'unknown'
            print(f"Task terminal state: {state_str} (Task ID: {final_task.id})")

            # If the remote agent is asking for user input, surface that message immediately
            if state_str in ("input_required", "task_state_input_required"):
                prompt_text = extract_message_text(getattr(final_task.status, 'message', None), tool_context)
                if not prompt_text:
                    prompt_text = "The remote agent requires your input to proceed. Please provide the requested details."
                return {
                    "response": f"⏸️ {agent_name} requires your input to proceed:\n\n{prompt_text}",
                    "agent": agent_name,
                    "task_id": final_task.id,
                    "state": state_str,
                }

            print(f"Task completed! Task ID: {final_task.id}")
            print(f"Task status: {state_str}")
            print(f"Number of artifacts: {len(final_task.artifacts) if final_task.artifacts else 0}")
            
            # Extract and format the response from artifacts
            response_text = ""
            if final_task.artifacts:
                for i, artifact in enumerate(final_task.artifacts):
                    print(f"Artifact {i}: {artifact.name if hasattr(artifact, 'name') else 'unnamed'}")
                    if getattr(artifact, 'parts', None):
                        print(f"  Parts count: {len(artifact.parts)}")
                        for j, part in enumerate(artifact.parts):
                            text = convert_part(part, tool_context)
                            print(f"  Part {j} text length: {len(text) if text else 0}")
                            if text:
                                response_text += text + "\n"
            
            if not response_text:
                # Fallback to any status message text if artifacts are empty
                response_text = extract_message_text(getattr(final_task.status, 'message', None), tool_context)
                if not response_text:
                    response_text = "Task finished but no response content was provided by the remote agent."
            
            print(f"Final response text length: {len(response_text)}")
            print(f"Response preview: {response_text[:200]}...")
            
            # If the conversation reached a terminal state other than input_required,
            # clear the saved task id so future messages start a fresh task.
            if (
                state_str in ("completed", "task_state_completed")
                or "failed" in state_str
                or "cancel" in state_str
            ):
                if agent_task_key in state:
                    state[agent_task_key] = None

            # Return a dict with a 'response' key so the UI extracts and displays it
            return {
                "response": response_text,
                "agent": agent_name,
                "task_id": final_task.id,
                "state": state_str,
            }
            
        except TimeoutError as e:
            # Keep task id for potential continuation
            return {"response": f"⏱️ The request timed out after 120 seconds. Error: {str(e)}"}
            
        except RuntimeError as e:
            # Clear saved task id on terminal failure
            if agent_task_key in state:
                state[agent_task_key] = None
            return {"response": f"❌ The request failed. Error: {str(e)}"}


def _get_initialized_routing_agent_sync() -> Agent:
    """Synchronously creates and initializes the RoutingAgent."""

    async def _async_main() -> Agent:
        routing_agent_instance = await RoutingAgent.create(
            remote_agent_addresses=[
                os.getenv('AIR_AGENT_URL', 'http://localhost:10002'),
                os.getenv('WEA_AGENT_URL', 'http://localhost:10001'),
            ]
        )
        return routing_agent_instance.create_agent()

    try:
        return asyncio.run(_async_main())
    except RuntimeError as e:
        if 'asyncio.run() cannot be called from a running event loop' in str(e):
            print(
                f'Warning: Could not initialize RoutingAgent with asyncio.run(): {e}. '
                'This can happen if an event loop is already running (e.g., in Jupyter). '
                'Consider initializing RoutingAgent within an async function in your application.'
            )
        raise


root_agent = _get_initialized_routing_agent_sync()
