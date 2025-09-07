# ADK Demo Agents

## Agents

To run the sample ADK agents in this project you must navigate to the `/agents` directory.

### Running the Agent Locally with `adk web`

To run the `oauth_agent` locally for development:

1.  **Navigate to the `agents` directory.**
    ```bash
    cd agents
    ```

2.  **Set the `LOCAL_DEV` environment variable to `TRUE`.** This ensures the agent runs with the local development configuration.
    ```bash
    export LOCAL_DEV=TRUE
    ```

3.  **Start the ADK development server.**
    ```bash
    uv run adk web
    ```

4.  **Open the ADK web interface** in your browser (usually at `http://localhost:8080`).

5.  **Select the `oauth_agent` folder** from the agent selection UI to start the agent.

