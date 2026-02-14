# Multi-Agent A2A Demo

A demonstration of agent-to-agent (A2A) communication using Google's Agent Development Kit (ADK). This demo shows how a root agent can orchestrate downstream agents while passing authentication headers for user-context-aware operations.

## Architecture

```
┌─────────────────┐     A2A + Auth Header     ┌─────────────────────┐
│   Root Agent    │ ─────────────────────────▶│  Downstream Agent   │
│ (Orchestrator)  │                           │    (BigQuery)       │
│                 │                           │                     │
│ - OAuth2 Login  │                           │ - query_bigquery    │
│ - Token Capture │                           │ - get_table_schema  │
│ - RemoteA2aAgent│                           │ - list_tables       │
└─────────────────┘                           └─────────────────────┘
```

## Structure

```
a2a_multi_agent/
├── root_a2a_agent/           # A2A client/orchestrator
│   ├── agent/
│   │   ├── __init__.py
│   │   └── agent.py          # RemoteA2aAgent + OAuth
│   ├── .env.example
│   ├── pyproject.toml
│   └── create_ge_agent.sh
│
└── downstream_a2a_agent/     # A2A server with BigQuery
    ├── agent/
    │   ├── __init__.py
    │   └── agent.py          # BigQuery tools
    ├── .env.example
    ├── pyproject.toml
    └── create_ge_agent.sh
```

## Quick Start

### 1. Set Up Downstream Agent

```bash
cd downstream_a2a_agent

# Copy and configure environment
cp .env.example .env
# Edit .env with your GCP project and BigQuery details

# Install dependencies
uv sync

# Run locally as A2A server
adk api_server --port 8001
```

### 2. Set Up Root Agent

```bash
cd root_a2a_agent

# Copy and configure environment
cp .env.example .env
# Edit .env - set DOWNSTREAM_AGENT_URL=http://localhost:8001

# Install dependencies
uv sync

# Run with ADK dev UI
adk web
```

### 3. Test the Flow

1. Open http://localhost:8000/dev-ui in your browser
2. Authenticate through the OAuth flow
3. Ask questions like:
   - "What tables are available?"
   - "Show me the schema of the sales table"
   - "Query the top 10 customers by revenue"

## Authentication Flow

1. **User authenticates** with the root agent via OAuth2
2. **Root agent stores** the bearer token in session state
3. **RemoteA2aAgent** passes the token to the downstream agent via HTTP headers
4. **Downstream agent** retrieves the token from `tool_context.state`
5. **BigQuery tools** use the token for user-context-aware queries

## Deployment to Agent Engine

### Deploy Downstream Agent First

```bash
cd downstream_a2a_agent
chmod +x create_ge_agent.sh
./create_ge_agent.sh
```

Note the Agent Engine URL from the output.

### Deploy Root Agent

```bash
cd root_a2a_agent
# Update .env with the downstream agent's Agent Engine URL
chmod +x create_ge_agent.sh
./create_ge_agent.sh
```

## Configuration

### Downstream Agent (.env)

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `BIGQUERY_DATASET` | Default BigQuery dataset |
| `BIGQUERY_TABLE` | Default table (optional) |
| `GOOGLE_CLOUD_LOCATION` | Region for deployment |

### Root Agent (.env)

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `DOWNSTREAM_AGENT_URL` | URL of downstream A2A agent |
| `CLIENT_ID` | OAuth2 client ID |
| `CLIENT_SECRET` | OAuth2 client secret |
| `GOOGLE_CLOUD_LOCATION` | Region for deployment |

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- [google-adk](https://google.github.io/adk-docs/) >= 1.18.0
- GCP project with BigQuery and Agent Engine APIs enabled
- OAuth2 credentials configured in GCP Console
