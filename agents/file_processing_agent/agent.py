from google.adk.agents import LlmAgent
from google.adk.tools.load_artifacts_tool import load_artifacts_tool

def file_processing_function(file):
    # Implement your custom file processing logic here
    return f"Processed content of the file: {file.name}"

# Define your custom agent
file_processing_agent = LlmAgent(
    name="file_processing_agent",
    model="gemini-pro",
    instruction="""Your task is to process user-uploaded files.
    When a file is uploaded, you must first use the `load_artifacts_tool` to access it.
    After loading the file, use the `file_processing_function` to process its content.
    Finally, confirm to the user that the file has been processed.""",
    tools=[load_artifacts_tool, file_processing_function],
)