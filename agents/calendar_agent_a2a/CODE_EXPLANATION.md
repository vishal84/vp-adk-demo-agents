# Calendar Agent A2A - Code Explanation

## Overview

The Calendar Agent A2A is a demonstration of building an Agent-to-Agent (A2A) protocol-compliant calendar management agent using Google's Agent Development Kit (ADK). This agent can be deployed to Google Cloud Run and integrated with Gemini Enterprise AgentSpace, enabling it to communicate with other agents through the standardized A2A protocol.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Calendar Agent A2A                       │
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │   agent.py   │─────▶│agent_executor│                     │
│  │  (ADK Agent) │      │    .py       │                     │
│  └──────────────┘      └──────────────┘                     │
│         │                     │                             │
│         │                     ▼                             │
│         │            ┌─────────────────┐                    │
│         │            │  A2A Server     │                    │
│         └───────────▶│  (__main__.py)  │                    │
│                      └─────────────────┘                    │
│                              │                              │
└──────────────────────────────┼──────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Task Store         │
                    │ (InMemory/AlloyDB)   │
                    └──────────────────────┘
```

---

## Core Files

### 1. `__main__.py` - Server Entry Point

**Purpose**: Bootstraps and runs the A2A-compliant HTTP server.

**Key Components**:

#### a. Server Configuration
```python
@click.command()
@click.option('--host', default='localhost')
@click.option('--port', default=10002)
async def main(host, port):
```
- Uses Click for CLI arguments
- Defaults to localhost:10002 for local development
- Async main function to support async operations throughout

#### b. Agent Card Definition
```python
agent_card = AgentCard(
    name=calendar_agent.name,
    description=calendar_agent.description,
    version='1.0.0',
    url=os.environ['APP_URL'],
    default_input_modes=['text', 'text/plain'],
    default_output_modes=['text', 'text/plain'],
    capabilities=AgentCapabilities(streaming=True),
    skills=[...]
)
```
- **Agent Card**: Self-describing metadata following A2A protocol
- Defines capabilities, I/O modes, and skills
- `APP_URL` must be set to the agent's public endpoint
- Declares streaming support for real-time responses

#### c. Task Store Selection
```python
use_alloy_db_str = os.getenv('USE_ALLOY_DB', 'False')
if use_alloy_db_str.lower() == 'true':
    # Production: AlloyDB with connection pooling
    engine, connector = await create_sqlalchemy_engine(...)
    task_store = DatabaseTaskStore(engine)
else:
    # Development: In-memory store
    task_store = InMemoryTaskStore()
```
- **InMemoryTaskStore**: Simple, for development/testing
- **DatabaseTaskStore**: Persistent, production-ready with AlloyDB
- AlloyDB connector handles IAM auth and connection pooling

#### d. Request Handler & A2A App
```python
request_handler = DefaultRequestHandler(
    agent_executor=ADKAgentExecutor(agent=calendar_agent),
    task_store=task_store,
)

a2a_app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=request_handler
)
```
- **DefaultRequestHandler**: Manages A2A protocol requests
- **ADKAgentExecutor**: Bridges A2A protocol to ADK agent
- **A2AStarletteApplication**: Implements A2A HTTP endpoints

#### e. AlloyDB Integration
```python
async def create_sqlalchemy_engine(
    inst_uri: str,
    user: str,
    password: str,
    db: str,
    refresh_strategy: str = 'background',
) -> tuple[sqlalchemy.ext.asyncio.engine.AsyncEngine, AsyncConnector]:
```
- **AsyncConnector**: Google Cloud AlloyDB connector
- **refresh_strategy**: 'background' for long-running servers, 'lazy' for serverless
- Uses IAM authentication for secure database access
- Connection pooling via SQLAlchemy async engine

---

### 2. `agent.py` - ADK Agent Definition

**Purpose**: Defines the core agent logic and capabilities using Google ADK.

```python
def create_calendar_event(event_details: dict) -> dict:
    """Create a calendar event with the provided details."""
    return {
        'status': 'success',
        'message': f"Event '{event_details['title']}' created successfully.",
    }

root_agent = Agent(
    name='calendar_agent_a2a',
    model="gemini-2.5-flash",
    description='Agent to manage calendar events.',
    instruction='You are a helpful agent who can manage calendar events.',
    tools=[create_calendar_event],
)
```

**Key Points**:
- **Tool**: `create_calendar_event` - Mock implementation for demonstration
- **Model**: Uses Gemini 2.5 Flash for fast responses
- **Instruction**: System prompt guiding the agent's behavior
- In production, this would integrate with actual calendar APIs (Google Calendar, Outlook, etc.)

**Tool Schema**:
- ADK automatically generates function schemas from Python type hints
- The LLM receives these schemas and knows when to call the tool
- Return values should be JSON-serializable

---

### 3. `agent_executor.py` - A2A to ADK Bridge

**Purpose**: Executes ADK agents in response to A2A protocol requests.

#### Class: `ADKAgentExecutor`

**Initialization**:
```python
def __init__(self, agent, status_message='Processing request...', artifact_name='response'):
    self.agent = agent
    self.runner = Runner(
        app_name=agent.name,
        agent=agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
```
- **Runner**: ADK component that orchestrates agent execution
- **Services**: In-memory services for artifacts, sessions, and memory
- Configurable status message and artifact naming

**Execution Flow**:
```python
async def execute(self, context: RequestContext, event_queue: EventQueue):
    # 1. Extract user query from A2A message
    query = context.get_user_input()
    task = context.current_task or new_task(context.message)
    
    # 2. Update task status
    await updater.update_status(
        TaskState.working,
        new_agent_text_message(self.status_message, ...)
    )
    
    # 3. Get or create session
    session = await self.runner.session_service.get_session(...)
    if not session:
        session = await self.runner.session_service.create_session(...)
    
    # 4. Run ADK agent
    content = types.Content(role='user', parts=[types.Part.from_text(query)])
    async for event in self.runner.run_async(...):
        if event.is_final_response():
            # Extract response text
            response_text += part.text
    
    # 5. Return response as A2A artifact
    await updater.add_artifact([Part(root=TextPart(text=response_text))], ...)
    await updater.complete()
```

**Key Concepts**:
- **RequestContext**: A2A request metadata (message, task, user)
- **EventQueue**: Async queue for publishing task updates
- **TaskUpdater**: Helper to update task state and artifacts
- **Session Management**: Persists conversation context across requests
- **Streaming**: ADK events are processed asynchronously

**Error Handling**:
```python
except Exception as e:
    await updater.update_status(
        TaskState.failed,
        new_agent_text_message(f'Error: {e!s}', ...),
        final=True,
    )
```
- Gracefully handles exceptions
- Reports errors back to caller via A2A protocol

---

### 4. `pyproject.toml` - Dependencies

```toml
[project]
name = "calendar-agent-a2a"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "a2a-sdk>=0.3.0",           # A2A protocol implementation
    "starlette>=0.46.1",         # ASGI web framework
    "uvicorn>=0.34.0",           # ASGI server
    "click>=8.1.8",              # CLI argument parsing
    "google-adk>=1.7.0",         # Agent Development Kit
    "python-dotenv>=1.1.0",      # Environment variable management
    "asyncpg>=0.30.0",           # Async PostgreSQL driver
    "google-cloud-alloydb-connector[asyncpg]>=1.9.0",  # AlloyDB connector
    "litellm>=1.40.0",           # Multi-LLM abstraction (optional)
]
```

**Dependency Roles**:
- **a2a-sdk**: Core A2A protocol types and utilities
- **google-adk**: Agent orchestration, LLM integration, tools
- **starlette + uvicorn**: Lightweight, production-ready HTTP server
- **AlloyDB libs**: Production database for task persistence
- **litellm**: Enables switching between different LLM providers

---

### 5. `Dockerfile` - Containerization

```dockerfile
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

EXPOSE 8080
WORKDIR /app
COPY . ./
RUN uv sync
ENTRYPOINT ["sh", "-c", "uv run . --host 0.0.0.0 --port $PORT"]
```

**Build Strategy**:
- **Base Image**: Python 3.13 slim (minimal footprint)
- **UV**: Fast Python package manager (replaces pip + venv)
- **Port**: Exposes 8080, Cloud Run provides `$PORT` env var
- **Entry Point**: Runs agent via `uv run .` (uses `__main__.py`)

**Benefits**:
- Fast builds (uv caches dependencies)
- Small image size (~200MB)
- Secure (slim base, no unnecessary tools)

---

### 6. `create_ge_agent.sh` - Gemini Enterprise Integration

**Purpose**: Registers the agent in Gemini Enterprise AgentSpace.

**Workflow**:
```bash
# 1. Load environment variables
source .env

# 2. Validate configuration
required_vars=("GOOGLE_CLOUD_PROJECT" "AGENT_NAME" "AGENT_URL" ...)

# 3. Build Agent Card JSON
JSON_AGENT_CARD_VALUE_RAW=$(cat <<EOF
{
    "capabilities": { "streaming": true },
    "url": "${AGENT_URL}",
    "skills": [...]
}
EOF
)

# 4. Escape JSON for API payload
JSON_AGENT_CARD_VALUE_ESCAPED=$(printf '%s' "$JSON_AGENT_CARD_VALUE_RAW" | jq -Rs .)

# 5. Create agent via Discovery Engine API
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "${DISCOVERY_ENGINE_API_BASE_URL}/v1alpha/.../agents" \
  -d "$REQUEST_BODY"
```

**Key Points**:
- **Agent Card**: Self-describing metadata (same as in `__main__.py`)
- **Discovery Engine API**: Google's agent registry
- **IAM Authentication**: Uses gcloud credentials
- **Idempotency**: Safe to run multiple times (checks existence)

**Required Environment Variables**:
- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `GOOGLE_CLOUD_LOCATION`: Region (e.g., 'us-central1')
- `AGENT_NAME`: Unique identifier
- `AGENT_URL`: Public endpoint (Cloud Run URL)
- `GE_APP`: AgentSpace application ID
- `ASSISTANT_ID`: Target assistant in AgentSpace

---

### 7. `delete_ge_agent.sh` - Cleanup Script

**Purpose**: Removes the agent from Gemini Enterprise AgentSpace.

```bash
# Safety check: require confirmation
read -p "Are you sure you want to continue? (y/n) "

# DELETE request to Discovery Engine API
curl -X DELETE \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://discoveryengine.googleapis.com/v1alpha/$AGENT_RESOURCE_NAME"
```

**Safety Features**:
- Interactive confirmation prompt
- Validates `.env` file exists
- Requires `AGENT_RESOURCE_NAME` (full resource path)

---

## Deployment Workflows

### Local Development

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
echo "GOOGLE_API_KEY=your_key" > .env
echo "APP_URL=http://localhost:10002" >> .env

# 3. Run locally
uv run . --host localhost --port 10002
```

### Cloud Run Deployment

```bash
# 1. Deploy to Cloud Run
gcloud run deploy calendar-agent-a2a \
    --source=. \
    --port=8080 \
    --region=us-central1 \
    --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=true,APP_URL=TEMPORARY_URL

# 2. Update with actual service URL
gcloud run services update calendar-agent-a2a \
    --update-env-vars=APP_URL={your-cloud-run-url}

# 3. Register in AgentSpace
./create_ge_agent.sh
```

### With AlloyDB (Production)

```bash
# 1. Create secrets
gcloud secrets create alloy_db_user --data-file=user.txt
gcloud secrets create alloy_db_pass --data-file=pass.txt

# 2. Deploy with database
gcloud run deploy calendar-agent-a2a \
    --update-secrets=DB_USER=alloy_db_user:latest,DB_PASS=alloy_db_pass:latest \
    --set-env-vars=USE_ALLOY_DB=True,DB_INSTANCE=projects/.../instances/primary

# 3. Grant IAM permissions
gcloud projects add-iam-policy-binding {project} \
    --member=serviceAccount:a2a-service-account@{project}.iam.gserviceaccount.com \
    --role=roles/alloydb.client
```

---

## A2A Protocol Integration

### Agent Card Schema

The agent card is the agent's "business card" in the A2A ecosystem:

```json
{
  "name": "calendar_agent_a2a",
  "description": "Agent to manage calendar events",
  "version": "1.0.0",
  "url": "https://your-agent.run.app",
  "capabilities": {
    "streaming": true
  },
  "skills": [
    {
      "id": "add_calendar_event",
      "name": "Add Calendar Event",
      "description": "Creates a new calendar event",
      "examples": ["Add a meeting tomorrow at 10 AM"]
    }
  ]
}
```

### Message Flow

```
Client                  A2A Server              ADK Agent
  │                         │                       │
  │──SendMessage───────────▶│                       │
  │  (contextId, taskId)    │                       │
  │                         │──execute()───────────▶│
  │                         │                       │
  │                         │◀──event stream────────│
  │                         │  (working, artifacts) │
  │                         │                       │
  │◀──TaskUpdate────────────│                       │
  │  (status: working)      │                       │
  │                         │                       │
  │◀──TaskUpdate────────────│                       │
  │  (artifact: response)   │                       │
  │                         │                       │
  │◀──TaskUpdate────────────│                       │
  │  (status: completed)    │                       │
```

### Task States

1. **pending**: Task created, not started
2. **working**: Agent is processing
3. **input_required**: Agent needs user input
4. **completed**: Task finished successfully
5. **failed**: Task encountered an error
6. **cancelled**: Task was cancelled

---

## Security Considerations

### IAM & Authentication

**Service Account**:
```bash
# Create dedicated service account
gcloud iam service-accounts create a2a-service-account

# Grant minimal required permissions
gcloud projects add-iam-policy-binding {project} \
  --member=serviceAccount:a2a-service-account@{project}.iam.gserviceaccount.com \
  --role=roles/aiplatform.user \
  --role=roles/secretmanager.secretAccessor
```

**Public vs Private**:
- **Private**: IAM-based auth, internal GCP clients only
- **Public**: Agent-level auth via agent card's `securitySchemes`

### Input Validation

**⚠️ Security Warning** (from README):
> All data received from an external agent—including but not limited to its AgentCard, messages, artifacts, and task statuses—should be handled as untrusted input.

**Best Practices**:
1. Validate all incoming data structures
2. Sanitize text before using in prompts (prevent injection)
3. Limit message sizes to prevent DoS
4. Rate limit requests per client

### Secrets Management

```bash
# Store secrets in Secret Manager, not in code
gcloud secrets create api_key --data-file=key.txt

# Mount as env vars in Cloud Run
--update-secrets=API_KEY=api_key:latest
```

---

## Testing

### Local Testing
```bash
# Terminal 1: Start agent
uv run . --host localhost --port 10002

# Terminal 2: Test with CLI
cd /path/to/cli
uv run . --agent http://localhost:10002
```

### Cloud Run Testing
```bash
# Authenticate and interact
uv run . --agent https://your-agent.run.app \
  --bearer-token "$(gcloud auth print-identity-token)"
```

### Example Interaction
```
> Add a meeting with the team tomorrow at 2 PM

Agent: Event 'team meeting' created successfully.
```

---

## Extension Points

### 1. Add Real Calendar Integration

Replace mock implementation in `agent.py`:
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def create_calendar_event(event_details: dict) -> dict:
    creds = Credentials.from_authorized_user_file('token.json')
    service = build('calendar', 'v3', credentials=creds)
    
    event = {
        'summary': event_details['title'],
        'start': {'dateTime': event_details['start']},
        'end': {'dateTime': event_details['end']},
    }
    
    created_event = service.events().insert(
        calendarId='primary',
        body=event
    ).execute()
    
    return {
        'status': 'success',
        'event_id': created_event['id'],
        'link': created_event['htmlLink']
    }
```

### 2. Add More Tools

```python
def list_calendar_events(start_date: str, end_date: str) -> list:
    """List calendar events in a date range."""
    # Implementation

def delete_calendar_event(event_id: str) -> dict:
    """Delete a calendar event by ID."""
    # Implementation

root_agent = Agent(
    name='calendar_agent_a2a',
    model="gemini-2.5-flash",
    tools=[
        create_calendar_event,
        list_calendar_events,
        delete_calendar_event
    ],
)
```

### 3. Add Memory/Context

```python
from google.adk.memory.base_memory_service import BaseMemoryService

# Replace InMemoryMemoryService with persistent memory
from custom_memory_service import AlloyDBMemoryService

runner = Runner(
    agent=agent,
    memory_service=AlloyDBMemoryService(engine),
    # ...
)
```

### 4. Add Authentication

Update agent card:
```python
agent_card = AgentCard(
    # ... existing fields
    security_schemes={
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer"
        }
    },
    security=[{"bearerAuth": []}]
)
```

Validate in executor:
```python
async def execute(self, context: RequestContext, event_queue: EventQueue):
    # Extract and validate bearer token
    auth_header = context.message.metadata.get('Authorization')
    if not auth_header or not validate_token(auth_header):
        raise UnauthorizedError("Invalid credentials")
    # ... rest of execution
```

---

## Performance Considerations

### 1. Connection Pooling
- AlloyDB connector handles connection pooling automatically
- Configure pool size via SQLAlchemy engine settings
- Use `refresh_strategy='lazy'` for serverless (Cloud Run)

### 2. Caching
- ADK sessions are cached in memory
- For production, consider Redis-backed session store
- Cache agent card responses (rarely changes)

### 3. Streaming
- Agent supports streaming for real-time updates
- Reduces perceived latency for long-running tasks
- Use `capabilities.streaming=true` in agent card

### 4. Concurrency
- Uvicorn handles concurrent requests efficiently
- Scale horizontally on Cloud Run (auto-scaling)
- Consider task queue for batch operations

---

## Monitoring & Observability

### Cloud Run Metrics
- Request latency
- Error rate
- CPU/memory usage
- Active instances

### Application Logs
```python
import logging
logger = logging.getLogger(__name__)

# In agent_executor.py
logger.info(f"Processing request for user: {user_id}")
logger.error(f"Failed to process: {e}", exc_info=True)
```

### Tracing
- Cloud Trace integration (automatic with Cloud Run)
- Add custom spans for detailed profiling

---

## Troubleshooting

### Common Issues

**1. Agent Card Validation Errors**
- Ensure `APP_URL` is set correctly
- Verify all required fields are present
- Check JSON escaping in `create_ge_agent.sh`

**2. Database Connection Failures**
- Verify AlloyDB instance is running
- Check IAM permissions (alloydb.client role)
- Validate connection string format

**3. Authentication Errors**
- Ensure service account has necessary roles
- Check secrets are mounted correctly
- Verify gcloud credentials are fresh

**4. Model/LLM Errors**
- Check API key is valid (GOOGLE_API_KEY)
- For Vertex AI, ensure project/location are set
- Verify model name is correct (gemini-2.5-flash)

---

## Summary

The Calendar Agent A2A demonstrates:

1. **A2A Protocol Compliance**: Self-describing agent card, standardized message format
2. **ADK Integration**: Modern agent framework with LLM orchestration
3. **Production-Ready**: Cloud Run deployment, AlloyDB persistence, IAM security
4. **Extensible**: Easy to add tools, integrate real APIs, customize behavior
5. **Observable**: Structured logging, Cloud monitoring, tracing

This architecture can be adapted for any domain-specific agent: travel booking, document processing, data analysis, etc.
