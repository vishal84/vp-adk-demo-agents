import os
from pathlib import Path
from dotenv import load_dotenv
from google.genai import types
from google.adk.agents import Agent
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.code_executors import VertexAiCodeExecutor

# Load environment variables from the same directory as this file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

plot_agent = Agent(
    model="gemini-2.5-flash",
    name='plot_agent',
    instruction="""Generate and display charts from fictitious data. 
    Use the numpy library to create fictitious data and matplotlib 
    or seaborn to produce visualizations in the form of graphs.
    """,
    code_executor=VertexAiCodeExecutor(
        optimize_data_file=True,
        stateful=True,
    )
)

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="You are an agent that can generate charts from fictitious data.",
    instruction="""Generate and display charts (bar plots, line plots, etc.)
    from fictitious data. To create and display the charts, use the 'plot_agent' tool.
    Use numpy to create fictitious data and matplotlib and seaborn to plot the charts.
    """,
    tools=[AgentTool(agent=plot_agent)],
    generate_content_config=types.GenerateContentConfig(max_output_tokens=10000),
)
