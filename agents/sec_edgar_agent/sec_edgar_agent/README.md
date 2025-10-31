# ATK Agent - SEC EDGAR Financial Data Assistant

A comprehensive financial data agent built with Google's Agent Development Kit (ADK) that provides access to SEC EDGAR data through MCP integration.

## Features

- 📈 **Company Information** - Lookup companies by ticker, get CIK numbers, company facts
- 📊 **SEC Filings Analysis** - Access and analyze 10-K, 10-Q, 8-K, and other SEC filings
- 💰 **Financial Statements** - Income statements, balance sheets, cash flow statements
- 👥 **Insider Trading Data** - Form 4 analysis, insider transaction summaries
- 🔍 **XBRL Concept Extraction** - Extract specific financial concepts from filings
- 🤖 **Built with Google ADK** - Robust agent capabilities with MCP integration

## Setup

### 1. Install Dependencies

This project uses `uv` for dependency management:

```bash
uv sync
```

### 2. Configure for Vertex AI

This agent is configured to use Vertex AI for its generative AI capabilities.

1.  **Authenticate with Google Cloud:**
    If you haven't already, authenticate with the Google Cloud CLI:
    ```bash
    gcloud auth login
    gcloud auth application-default login
    ```

2.  **Set up your environment:**
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```

3.  **Edit the `.env` file** and set the following variables:
    ```
    GOOGLE_GENAI_USE_VERTEXAI=TRUE
    GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
    GOOGLE_CLOUD_LOCATION="your-gcp-region" # e.g., us-central1
    STAGING_BUCKET="gs://your-gcs-bucket-name"
    ```
    - `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID.
    - `GOOGLE_CLOUD_LOCATION`: The Google Cloud region to use.
    - `STAGING_BUCKET`: A Google Cloud Storage bucket for temporary files.

### 3. Run the Agent

If running the agent locally you can use service account impersonation to avoid downloading a service account key which can be a security risk. To do so you will need to impersonate a service account with required permissions needed to run this code sample.

Create a service account in __IAM & Admin__ and ensure you assign the following __IAM Roles__ to it:
- Cloud Run Service Invoker
- Logs Writer
- Storage Admin
- Vertex AI User

Authenticate with the gcloud CLI using the following:
```
gcloud auth application-default login --impersonate-service-account {SERVICE_ACCOUNT_EMAIL}
```

This will open a web browser prompting you to log in to your IAM user's account but will impersonate the service account and store its credentials to a location on your workstation. An example is below after successfully logging in:
```
Credentials saved to file: [/Users/(username)/.config/gcloud/application_default_credentials.json]
```

Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to the temporary location of the credentials on your local machine (from above):
```
export GOOGLE_APPLICATION_CREDENTIALS=/Users/(username)/.config/gcloud/application_default_credentials.json
```

You can now run the agent locally using `adk web`.

#### Web UI (Recommended)
```bash
uv run adk web
```

#### Terminal Interface
```bash
uv run adk run sec_edgar_agent
```

#### Python Script
```bash
uv run python agent.py
```

## Available SEC EDGAR Tools

The agent has access to all tools from our deployed SEC EDGAR MCP server:

### Company Tools
- `get_cik_by_ticker(ticker)` - Get CIK number for a company
- `get_company_info(identifier)` - Detailed company information
- `search_companies(query)` - Search companies by name
- `get_company_facts(identifier)` - Key financial metrics

### Filing Tools
- `get_recent_filings(identifier, form_type, days, limit)` - Recent SEC filings
- `get_filing_content(identifier, accession_number)` - Specific filing content
- `analyze_8k(identifier, accession_number)` - 8-K filing analysis
- `get_filing_sections(identifier, accession_number, form_type)` - Filing sections

### Financial Tools
- `get_financials(identifier, statement_type)` - Financial statements
- `get_segment_data(identifier, segment_type)` - Revenue segment data
- `get_key_metrics(identifier, metrics)` - Key financial metrics
- `compare_periods(identifier, metric, start_year, end_year)` - Period comparisons
- `get_xbrl_concepts(identifier, accession_number, concepts)` - XBRL extraction

### Insider Trading Tools
- `get_insider_transactions(identifier, form_types, days, limit)` - Insider transactions
- `get_insider_summary(identifier, days)` - Insider trading summary
- `analyze_form4_transactions(identifier, days, limit)` - Form 4 analysis

## Example Queries

Ask the agent questions like:

- "What's the latest 10-K filing for Apple?"
- "Get the financial statements for NVIDIA"
- "Show me recent insider trading for Tesla"
- "What are Microsoft's revenue segments?"
- "Find companies with 'tech' in their name"
- "Get the cash flow statement for Amazon"

## MCP Server Integration

This agent connects to our deployed SEC EDGAR MCP server at:
```
https://sec-edgar-mcp-{PROJECT_NUMBER}.{REGION}.run.app/mcp
```

### Authentication
The agent automatically handles authentication to the Cloud Run service:
- **Google Cloud Authentication**: Uses `gcloud auth print-access-token` for Bearer token authentication
- **Fallback Mode**: If gcloud is unavailable, falls back to unauthenticated requests
- **Automatic Setup**: Authentication headers are configured automatically at startup

**Prerequisites for Authentication:**
- Google Cloud SDK installed and configured
- Authenticated with `gcloud auth login`
- Appropriate IAM permissions for the Cloud Run service

The server provides real-time access to SEC EDGAR data with deterministic responses and exact financial values.

## Project Structure

```
ATK-agent/
├── agent.py           # Main agent implementation with MCP integration
├── .env.example       # Environment configuration template
├── .env              # Your API keys (create from .env.example)
├── pyproject.toml    # Project dependencies
└── README.md         # This file
```

## Google ADK Documentation

- [Official Documentation](https://google.github.io/adk-docs/)
- [MCP Tools Guide](https://google.github.io/adk-docs/tools/mcp-tools/)
- [GitHub Repository](https://github.com/google/adk-python)

## Next Steps

1. Add authentication for better MCP server access
2. Implement caching for frequently requested data
3. Add visualization capabilities for financial data
4. Extend with additional financial analysis tools
5. Deploy to Google Cloud for production use