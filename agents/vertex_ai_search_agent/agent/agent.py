import os
import logging
from anyio import Path
from google.adk.agents import Agent
from google.adk.tools import VertexAiSearchTool
from dotenv import load_dotenv

# Load environment variables from the same directory as this file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# Configuration
DATASTORE_ID = os.getenv("FULL_DATASTORE_ID")
MODEL_ID=os.getenv("MODEL_ID")

root_agent = Agent(
    name="vertex_search_agent",
    model=MODEL_ID,
    instruction="Answer questions using Vertex AI Search to find information from internal documents. Always cite sources when available.",
    description="Enterprise document search assistant with Vertex AI Search capabilities",
    tools=[VertexAiSearchTool(data_store_id=DATASTORE_ID)]
)
