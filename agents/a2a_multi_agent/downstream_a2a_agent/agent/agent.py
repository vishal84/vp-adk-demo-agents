"""
Downstream A2A Agent with BigQuery Tools

This agent is exposed as an A2A server and can query BigQuery datasets.
It retrieves the bearer token passed from the upstream A2A client via
the tool_context.state to authenticate BigQuery requests with user context.

The agent card can be customized via environment variables:
- AGENT_NAME: The name of the agent
- AGENT_DESCRIPTION: A description of what the agent does
- AGENT_VERSION: The version of the agent
- AGENT_URL: The URL where the agent is hosted
- AGENT_CAPABILITIES: Comma-separated list of agent capabilities
"""

import os
import logging
from pathlib import Path
from typing import Any

from google.cloud import bigquery
from google.oauth2 import credentials as oauth2_credentials

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext
from google.adk.a2a import AgentCard, AgentSkill, AgentCapabilities

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "")
BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE", "")

# Agent Card Configuration
AGENT_NAME = os.getenv("AGENT_NAME", "bigquery_agent")
AGENT_DESCRIPTION = os.getenv(
    "AGENT_DESCRIPTION",
    "An agent that can query BigQuery datasets using SQL. "
    "It can list tables, get table schemas, and execute SQL queries."
)
AGENT_VERSION = os.getenv("AGENT_VERSION", "1.0.0")
AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8001")
AGENT_PROVIDER_NAME = os.getenv("AGENT_PROVIDER_NAME", "Demo")
AGENT_PROVIDER_URL = os.getenv("AGENT_PROVIDER_URL", "")


def get_bigquery_client(tool_context: ToolContext) -> bigquery.Client:
    """
    Creates a BigQuery client using the bearer token from the upstream agent.
    
    The token is expected to be stored in tool_context.state["bearer_token"]
    by the root A2A agent when making the A2A call.
    """
    bearer_token = tool_context.state.get("bearer_token")
    
    if bearer_token:
        logger.info("Using bearer token from upstream agent for BigQuery auth")
        # Create credentials from the bearer token
        creds = oauth2_credentials.Credentials(token=bearer_token)
        return bigquery.Client(
            project=GOOGLE_CLOUD_PROJECT,
            credentials=creds
        )
    else:
        logger.info("No bearer token found, using Application Default Credentials")
        # Fall back to ADC for local development
        return bigquery.Client(project=GOOGLE_CLOUD_PROJECT)


def query_bigquery(
    sql_query: str, 
    tool_context: ToolContext
) -> dict[str, Any]:
    """
    Executes a SQL query against BigQuery and returns the results.
    
    This tool uses the authentication context passed from the upstream
    A2A agent to execute queries with the user's permissions.
    
    Args:
        sql_query: The SQL query to execute. Use fully qualified table names 
                   (project.dataset.table) or rely on the default dataset.
        tool_context: ADK tool context containing state from upstream agent.
    
    Returns:
        dict: A dictionary with 'status' ('success' or 'error'), 
              'results' (list of rows as dicts) if successful,
              or 'error_message' if failed.
    """
    try:
        client = get_bigquery_client(tool_context)
        
        # Configure the query job
        job_config = bigquery.QueryJobConfig()
        if BIGQUERY_DATASET:
            job_config.default_dataset = f"{GOOGLE_CLOUD_PROJECT}.{BIGQUERY_DATASET}"
        
        logger.info(f"Executing BigQuery: {sql_query[:100]}...")
        
        # Execute query
        query_job = client.query(sql_query, job_config=job_config)
        results = query_job.result()
        
        # Convert to list of dicts
        rows = [dict(row) for row in results]
        
        return {
            "status": "success",
            "results": rows,
            "row_count": len(rows)
        }
        
    except Exception as e:
        logger.error(f"BigQuery error: {e}")
        return {
            "status": "error",
            "error_message": str(e)
        }


def get_table_schema(
    table_name: str,
    tool_context: ToolContext
) -> dict[str, Any]:
    """
    Retrieves the schema for a BigQuery table.
    
    Args:
        table_name: The table name. Can be just the table name (uses default 
                    dataset) or fully qualified (project.dataset.table).
        tool_context: ADK tool context containing state from upstream agent.
    
    Returns:
        dict: A dictionary with 'status' and either 'schema' (list of field 
              definitions) or 'error_message'.
    """
    try:
        client = get_bigquery_client(tool_context)
        
        # Build fully qualified table reference
        if "." not in table_name:
            table_ref = f"{GOOGLE_CLOUD_PROJECT}.{BIGQUERY_DATASET}.{table_name}"
        else:
            table_ref = table_name
            
        logger.info(f"Getting schema for: {table_ref}")
        
        table = client.get_table(table_ref)
        
        schema = [
            {
                "name": field.name,
                "type": field.field_type,
                "mode": field.mode,
                "description": field.description or ""
            }
            for field in table.schema
        ]
        
        return {
            "status": "success",
            "table": table_ref,
            "schema": schema,
            "num_rows": table.num_rows,
            "description": table.description or ""
        }
        
    except Exception as e:
        logger.error(f"Schema retrieval error: {e}")
        return {
            "status": "error",
            "error_message": str(e)
        }


def list_tables(tool_context: ToolContext) -> dict[str, Any]:
    """
    Lists all tables in the configured BigQuery dataset.
    
    Args:
        tool_context: ADK tool context containing state from upstream agent.
    
    Returns:
        dict: A dictionary with 'status' and either 'tables' (list of table 
              info) or 'error_message'.
    """
    try:
        client = get_bigquery_client(tool_context)
        
        dataset_ref = f"{GOOGLE_CLOUD_PROJECT}.{BIGQUERY_DATASET}"
        logger.info(f"Listing tables in: {dataset_ref}")
        
        tables = client.list_tables(dataset_ref)
        
        table_list = [
            {
                "table_id": table.table_id,
                "table_type": table.table_type,
                "full_table_id": f"{table.project}.{table.dataset_id}.{table.table_id}"
            }
            for table in tables
        ]
        
        return {
            "status": "success",
            "dataset": dataset_ref,
            "tables": table_list,
            "table_count": len(table_list)
        }
        
    except Exception as e:
        logger.error(f"Table listing error: {e}")
        return {
            "status": "error",
            "error_message": str(e)
        }


# =============================================================================
# Agent Card Configuration
# =============================================================================

# Define agent skills based on the available tools
agent_skills = [
    AgentSkill(
        id="query_bigquery",
        name="Execute SQL Queries",
        description="Execute SQL queries against BigQuery datasets and return results."
    ),
    AgentSkill(
        id="get_table_schema",
        name="Get Table Schema",
        description="Retrieve the schema and structure of a BigQuery table."
    ),
    AgentSkill(
        id="list_tables",
        name="List Tables",
        description="List all available tables in the configured BigQuery dataset."
    ),
]

# Define agent capabilities
agent_capabilities = AgentCapabilities(
    streaming=True,
    pushNotifications=False,
    stateTransitionHistory=False,
)

# Build provider info if URL is provided
provider_info = None
if AGENT_PROVIDER_URL:
    from google.adk.a2a import AgentProvider
    provider_info = AgentProvider(
        organization=AGENT_PROVIDER_NAME,
        url=AGENT_PROVIDER_URL,
    )

# Create the agent card
agent_card = AgentCard(
    name=AGENT_NAME,
    description=AGENT_DESCRIPTION,
    url=AGENT_URL,
    version=AGENT_VERSION,
    skills=agent_skills,
    capabilities=agent_capabilities,
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    provider=provider_info,
)


# =============================================================================
# Agent Definition
# =============================================================================

# Define the agent
root_agent = LlmAgent(
    name=AGENT_NAME,
    model="gemini-2.0-flash",
    description=AGENT_DESCRIPTION,
    instruction="""You are a helpful data analyst agent with access to BigQuery.

You can help users:
1. List available tables in the dataset using the list_tables tool
2. Get the schema/structure of a table using the get_table_schema tool  
3. Execute SQL queries using the query_bigquery tool

When a user asks about data:
- First understand what tables and data are available if needed
- Help formulate appropriate SQL queries
- Execute queries and explain the results clearly

Important notes:
- Always use proper SQL syntax for BigQuery (Standard SQL)
- Be careful with queries that might return large result sets - suggest LIMIT clauses
- Explain any errors clearly and suggest fixes

You are operating as a downstream agent in an A2A architecture. Authentication 
context is passed automatically from the upstream agent.
""",
    tools=[query_bigquery, get_table_schema, list_tables],
    a2a_config=agent_card,
)

