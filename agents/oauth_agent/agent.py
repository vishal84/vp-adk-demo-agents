from google.adk.agents import Agent

# Define the root agent for your application
root_agent = Agent(
    name="my_simple_agent",
    model="gemini-1.5-flash",
    instruction="You are a friendly assistant. Your goal is to greet the user warmly."
)
