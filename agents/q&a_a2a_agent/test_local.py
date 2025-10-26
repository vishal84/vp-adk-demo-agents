import os
import asyncio
from pprint import pprint

import vertexai
from vertexai.preview import reasoning_engines

from .agent_card import qna_agent_card
from .agent_executor import QnAAgentExecutor
from .utils import build_get_request, build_post_request

from dotenv import load_dotenv
load_dotenv()

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
STAGING_BUCKET = os.getenv("STAGING_BUCKET")

vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION, staging_bucket=STAGING_BUCKET)

async def main():
    a2a_agent = reasoning_engines.A2aAgent(agent_card=qna_agent_card, agent_executor_builder=QnAAgentExecutor)
    a2a_agent.set_up()

    print("--- Testing Agent Card ---" )
    request = build_get_request(None)
    response = await a2a_agent.handle_authenticated_agent_card(
        request=request, context=None
    )
    pprint(response)

    print("\n--- Sending Query ---" )
    message_data = {
        "message": {
            "messageId": f"msg-{os.urandom(8).hex()}",
            "content": [{"text": "What is the capital of France?"}],
            "role": "ROLE_USER",
        },
    }
    request = build_post_request(message_data)
    response = await a2a_agent.on_message_send(request=request, context=None)
    pprint(response)

    task_id = response["task"]["id"]
    print(f"The Task ID is: {task_id}")

    print("\n--- Getting Response (Polling) --- ")
    while True:
        task_data = {"id": task_id}
        request = build_get_request(task_data)
        response = await a2a_agent.on_get_task(request=request, context=None)
        pprint(response)

        state = response["status"]["state"]
        if state in ["TASK_STATE_COMPLETED", "TASK_STATE_FAILED"]:
            print(f"Task finished with state: {state}")
            if state == "TASK_STATE_COMPLETED":
                if "artifacts" in response:
                    for artifact in response["artifacts"]:
                        if artifact["parts"] and "text" in artifact["parts"][0]:
                            print(f"**Answer**:\n {artifact['parts'][0]['text']}")
                        else:
                            print("Could not extract text from artifact parts.")
                else:
                    print("'artifacts' key not found in the completed response.")
            else:
                print("Task failed.")
            break
        print("Task not yet completed, waiting...")
        await asyncio.sleep(1)  # Use asyncio.sleep for async context

if __name__ == "__main__":
    asyncio.run(main())