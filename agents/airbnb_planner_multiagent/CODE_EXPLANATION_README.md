# Airbnb Planner Multiagent System: Code Explanation & Flow

## Overview
This folder ties together the explanations for each agent in the `airbnb_planner_multiagent` system and describes the overall flow and orchestration between agents. The system consists of three main agents:
- **Host Agent**: Central router and orchestrator, provides the frontend and delegates tasks.
- **Airbnb Agent**: Handles accommodation search and booking queries.
- **Weather Agent**: Handles weather information and forecast queries.

## Agent Roles & Responsibilities
- **Host Agent**: Receives user input, determines intent, and routes requests to the appropriate specialized agent. Maintains session state and context, ensuring seamless multi-agent collaboration.
- **Airbnb Agent**: Uses MCP tools and LLMs to search for accommodations, returning results and handling follow-up queries.
- **Weather Agent**: Uses MCP tools and external APIs to provide weather alerts and forecasts, including geocoding for city/state queries.

## Flow Between Agents
1. **User Interaction**: The user interacts with the Host Agent via a Gradio frontend.
2. **Intent Detection & Routing**: The Host Agent analyzes the request and decides whether it pertains to accommodation or weather.
3. **Task Delegation**: The Host Agent delegates the request to the Airbnb Agent or Weather Agent using the A2A protocol.
4. **Remote Agent Execution**: The selected agent processes the request, possibly invoking external tools/APIs, and streams results back.
5. **Response Aggregation**: The Host Agent receives the response and presents it to the user, relaying any follow-up input requests as needed.
6. **Session Management**: The Host Agent tracks active agents and session state to ensure context continuity and correct routing for multi-turn conversations.

## Routing Logic
- The Host Agent uses the `RoutingAgent` class to maintain connections to remote agents and delegate tasks based on user intent.
- If a remote agent requires additional input, the Host Agent relays the request to the user and continues the conversation.
- The Host Agent can engage multiple agents in parallel if the user request spans multiple domains (e.g., "Find an Airbnb in LA and tell me the weather there").

## Security Considerations
- All data from remote agents and external tools is treated as untrusted.
- Input validation, prompt sanitization, and secure handling of agent cards, messages, and artifacts are essential to prevent vulnerabilities.

## Extension Points
- Add new specialized agents by implementing their own A2A server and tools, then registering them with the Host Agent's routing logic.
- Extend the Host Agent's routing logic to support more complex multi-agent workflows and richer session management.

## References
- See individual agent explanations:
  - [Airbnb Agent](./airbnb_agent/airbnb_agent.md)
  - [Host Agent](./host_agent/host_agent.md)
  - [Weather Agent](./weather_agent/weather_agent.md)

---
This documentation provides a high-level overview and technical breakdown of the multiagent system, supporting onboarding, extension, and troubleshooting for developers.