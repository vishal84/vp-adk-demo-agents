from collections.abc import Callable
import asyncio

import httpx

from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    SendMessageRequest,
    SendMessageResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    TaskQueryParams,
    GetTaskRequest,
    GetTaskResponse,
    JSONRPCErrorResponse,
)
from dotenv import load_dotenv


load_dotenv()

TaskCallbackArg = Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback = Callable[[TaskCallbackArg, AgentCard], Task]


class RemoteAgentConnections:
    """A class to hold the connections to the remote agents."""

    def __init__(self, agent_card: AgentCard, agent_url: str):
        print(f'agent_card: {agent_card}')
        print(f'agent_url: {agent_url}')
        self._httpx_client = httpx.AsyncClient(timeout=30)
        self.agent_client = A2AClient(
            self._httpx_client, agent_card, url=agent_url
        )
        self.card = agent_card

    def get_agent(self) -> AgentCard:
        return self.card

    async def send_message(
        self, message_request: SendMessageRequest
    ) -> SendMessageResponse:
        return await self.agent_client.send_message(message_request)

    async def get_task(self, task_id: str) -> GetTaskResponse:
        """Get the status and results of a task by ID."""
        request = GetTaskRequest(id=task_id, params=TaskQueryParams(id=task_id))
        return await self.agent_client.get_task(request)

    async def wait_for_task_completion(
        self, task_id: str, max_wait_seconds: int = 60, poll_interval: float = 1.0
    ) -> Task:
        """Poll a task until it completes or fails.
        
        Args:
            task_id: The ID of the task to poll
            max_wait_seconds: Maximum time to wait for completion
            poll_interval: Seconds between polling attempts
            
        Returns:
            The completed Task object
            
        Raises:
            TimeoutError: If task doesn't complete within max_wait_seconds
            RuntimeError: If task fails
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait_seconds:
                raise TimeoutError(
                    f"Task {task_id} did not complete within {max_wait_seconds} seconds"
                )
            
            response = await self.get_task(task_id)
            
            # Check if response is an error
            if isinstance(response.root, JSONRPCErrorResponse):
                raise RuntimeError(f"Task query failed: {response.root.error}")

            # Otherwise it's a success response
            task = response.root.result

            # Normalize and check state
            state_raw = None
            if task and getattr(task, 'status', None):
                state_raw = getattr(task.status, 'state', None)

            state_str = str(state_raw).lower() if state_raw is not None else None
            # Debug: print polled state each iteration
            print(f"[wait_for_task_completion] task={task_id} state={state_str}")

            # Normalize common variants: taskstate.completed, task_state_completed, COMPLETED, etc.
            normalized = state_str or ""
            # Replace separators with underscore for easier matching
            normalized = normalized.replace(".", "_").replace("-", "_").strip()
            
            if (
                normalized == "completed"
                or normalized.endswith("_completed")
                or "completed" in normalized
            ):
                return task
            # If the remote agent requires user input, return the task so caller can surface the prompt
            if (
                normalized == "input_required"
                or normalized.endswith("_input_required")
                or "input_required" in normalized
            ):
                return task
            if (
                normalized == "failed"
                or normalized.endswith("_failed")
                or "failed" in normalized
                or normalized == "cancelled"
                or normalized == "canceled"
                or normalized.endswith("_cancelled")
                or normalized.endswith("_canceled")
                or "cancelled" in normalized
                or "canceled" in normalized
            ):
                error_msg = task.status.message if getattr(task.status, 'message', None) else "Unknown error"
                raise RuntimeError(f"Task {task_id} failed: {error_msg}")
            
            await asyncio.sleep(poll_interval)
