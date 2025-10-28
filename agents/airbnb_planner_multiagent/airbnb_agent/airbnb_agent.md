# Airbnb Agent Code Explanation

## Overview
The Airbnb Agent is responsible for handling accommodation search requests using the A2A protocol and Google ADK. It leverages a set of MCP tools to interact with external services and provides streaming responses to users.

## Main Components
- **`__main__.py`**: Entry point for the agent server. Initializes the MCP client, loads tools, and starts the Uvicorn server with the A2AStarletteApplication. Manages application lifecycle and resource cleanup.
- **`agent_executor.py`**: Defines `AirbnbAgentExecutor`, which bridges user requests to the underlying agent. Handles streaming results, task state updates, and error handling.
- **`airbnb_agent.py`**: Implements the `AirbnbAgent` class, which wraps a LangGraph React agent using Google Generative AI or Vertex AI. Handles tool invocation, response formatting, and error management.
- **`README.md`**: Provides setup instructions, security disclaimers, and usage notes for the Airbnb agent.

## Flow
1. The server starts and loads MCP tools via `MultiServerMCPClient`.
2. Incoming requests are handled by `AirbnbAgentExecutor`, which streams results from the agent.
3. The agent uses LangGraph and the provided tools to search for accommodations and respond to user queries.
4. Responses are formatted and streamed back to the user, with error handling and input requests managed as needed.

## Key Patterns
- Async server bootstrapping
- Tool-based agent orchestration
- Streaming response handling
- Secure input validation

## Security Notes
All data from external agents and tools should be treated as untrusted. Input validation and prompt sanitization are critical to prevent vulnerabilities.
