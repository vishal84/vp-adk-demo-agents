from google.adk.agents import Agent
from google.adk.code_executors import BuiltInCodeExecutor

prompt = """Create detailed python scripts for the data, execute it and generate 
    visualization charts, bars, graphs or any other visualization techniques
    and show the image with proper axes and legends."""

root_agent = Agent(
    model='gemini-2.0-flash',
    name='plot_agent',
    description='A helpful code execution assistant.',
    instruction=prompt,
    code_executor=BuiltInCodeExecutor()
)
