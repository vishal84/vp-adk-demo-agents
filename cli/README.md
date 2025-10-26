# A2A CLI

The CLI is a small host application that demonstrates the capabilities of an `A2AClient`. It supports reading a server's `AgentCard` and text-based collaboration with a remote agent. All content received from the A2A server is printed to the console.

The client will use streaming if the server supports it.

## Prerequisites

- Python 3.12 or higher
- UV
- A running A2A server

## Running the CLI

1. Navigate to the CLI sample directory:

    ```bash
    cd samples/python/hosts/cli
    ```

2. Run the example client

    ```sh
    uv run . --agent [url-of-your-a2a-server]
    ```

   for example `--agent https://sample-a2a-agent-908687846511.us-central1.run.app`. More command line options are documented in the source code.

3. To test the calendar agent A2A example via CLI:

    Deploy to Cloud Run from agents/calendar_agent_a2a folder:
    ```sh
    gcloud run deploy calendar-agent-a2a --port 8080 --source=. --no-allow-unauthenticated --region="us-central1" --memory="1Gi" --project="gsi-agentspace" --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT="gsi-agentspace",GOOGLE_CLOUD_LOCATION="us-central1",APP_URL="https://calendar-agent-a2a-505636788486.us-central1.run.app"
    ```

    Navigate to cli directory and start a2a client pointing to a2a server:
    ```sh
    uv run . --agent https://calendar-agent-a2a-505636788486.us-central1.run.app/ --bearer-token "$(gcloud auth print-identity-token)"
    ```

## Disclaimer

Important: The sample code provided is for demonstration purposes and illustrates the mechanics of the Agent-to-Agent (A2A) protocol. When building production applications, it is critical to treat any agent operating outside of your direct control as a potentially untrusted entity.

All data received from an external agent—including but not limited to its AgentCard, messages, artifacts, and task statuses—should be handled as untrusted input. For example, a malicious agent could provide an AgentCard containing crafted data in its fields (e.g., description, name, skills.description). If this data is used without sanitization to construct prompts for a Large Language Model (LLM), it could expose your application to prompt injection attacks.  Failure to properly validate and sanitize this data before use can introduce security vulnerabilities into your application.

Developers are responsible for implementing appropriate security measures, such as input validation and secure handling of credentials to protect their systems and users.
