# SEC EDGAR MCP Server & ADK Agent

A comprehensive financial data platform combining a FastMCP 2.0 server for SEC EDGAR data access with a Google ADK agent for intelligent financial analysis.

## 🏗️ Architecture

```
Google ADK Agent ←→ SEC EDGAR MCP Server ←→ SEC EDGAR Database
```

- **MCP Server**: FastMCP 2.0 implementation providing SEC financial data tools
- **ADK Agent**: Google Agent Development Kit client with natural language interface  
- **Deployment**: Google Cloud Run with Docker containerization

## 🚀 Quick Start

### Deploy MCP Server
```bash
./deploy.sh learnagentspace us-central1
```

### Run ADK Agent
```bash
cd sec_edgar_agent
cp .env.example .env  # Change environment variables for the agent in this file
gcloud auth login     # Authenticate for MCP server access
cd ..
uv sync
uv run adk web
```

## 📊 Available Data

- **Company Information**: CIK lookup, company facts, search
- **SEC Filings**: 10-K, 10-Q, 8-K analysis and content extraction
- **Financial Statements**: Income, balance sheet, cash flow with exact XBRL values
- **Insider Trading**: Form 4 analysis, transaction summaries, sentiment tracking

## 🔧 Components

### `/sec_edgar_mcp/`
FastMCP 2.0 server with 20+ financial tools. Deployed at:
```
https://sec-edgar-mcp-371617986509.us-central1.run.app/mcp
```
**Authentication**: Requires Google Cloud authentication (Bearer token)

### `/sec_edgar_agent/`
Google ADK agent with MCP integration for natural language financial queries.

### Deployment Files
- `Dockerfile` - Container configuration
- `deploy.sh` - Cloud Run deployment script
- `DEPLOYMENT.md` - Detailed deployment guide

## 📝 Example Queries

Ask the ADK agent:
- "What's Apple's latest 10-K filing?"
- "Get NVIDIA's financial statements"
- "Show me recent insider trading for Tesla"
- "What are Microsoft's revenue segments?"

## 🛠️ Development

**Requirements:**
- Python 3.12+ with `uv`
- Docker for deployment
- Google AI Studio API key for ADK agent
- Google Cloud SDK for deployment

**Local Development:**
```bash
# MCP Server
cd sec_edgar_mcp
uv run python -m sec_edgar_mcp.server

# ADK Agent  
cd ADK_AGENT
uv run python agent.py
```

## 📚 Documentation

- [SEC EDGAR MCP Documentation](./sec_edgar_mcp/README.md)
- [ADK Agent Guide](./ADK_AGENT/README.md)
- [Deployment Instructions](./DEPLOYMENT.md)
- [Google ADK Docs](https://google.github.io/adk-docs/)

Built for BCG with deterministic SEC data responses and exact financial precision.