import os
from json import load
from dotenv import load_dotenv
from google.adk.agents import Agent

load_dotenv()

MODEL_ID = os.getenv("MODEL_ID")

# Define the root agent for your application
root_agent = Agent(
    name="my_simple_agent",
    model=f"{MODEL_ID}",
    instruction="You are a friendly assistant. Your goal is to greet the user warmly."
)
