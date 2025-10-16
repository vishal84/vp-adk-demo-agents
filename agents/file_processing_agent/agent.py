from google.adk.agents import LlmAgent
from google.adk.tools.load_artifacts_tool import load_artifacts_tool

def file_processing_function(file_name: str) -> str:
    """Process a file and return the processed content.
    
    Args:
        file_name: The name of the file to process
        
    Returns:
        A string containing the processed file content
    """
    # Implement your custom file processing logic here
    return f"Processed content of the file: {file_name}"

# Define your custom agent
root_agent = LlmAgent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction="""Your task is to process user-uploaded files.
    When a file is uploaded, you must first use the `load_artifacts_tool` to access it.
    After loading the file, use the `file_processing_function` to process its content.
    Finally, confirm to the user that the file has been processed.
    
    Additional instructions:
    - Always use the `load_artifacts_tool` to load the file before processing.
    - Always check the user's most recent turn for uploaded files (artifacts) before responding.
    - If a file is present, immediately use that file as the primary context for your answer.
    - DO NOT ask the user to upload a file if one has already been provided in the current or previous turn. Acknowledge the file and process with the user's request.
    """,
    tools=[load_artifacts_tool, file_processing_function],
)
