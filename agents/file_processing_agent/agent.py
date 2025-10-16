from google.adk.agents import LlmAgent
from google.adk.tools.load_artifacts_tool import load_artifacts_tool
from pathlib import Path

def file_processing_function(file_path: str) -> str:
    """Process a file and return the analyzed content. Supports images (.png, .jpg, .jpeg) and PDF documents.
    
    Args:
        file_path: The path or name of the file to process
        
    Returns:
        A string containing the analysis of the file
    """
    # Get file extension
    file_extension = Path(file_path).suffix.lower()
    
    # Supported formats
    image_formats = ['.png', '.jpg', '.jpeg']
    document_formats = ['.pdf']
    
    if file_extension in image_formats:
        return f"""Image Analysis for {file_path}:
                - File Type: Image ({file_extension})
                - Format: {file_extension.upper().replace('.', '')}
                - Status: Ready for visual analysis
                - Capabilities: Can analyze visual content, detect objects, read text, identify patterns
                - Instructions: Use this file with vision-capable models to extract information from the image"""
    
    elif file_extension in document_formats:
        return f"""Document Analysis for {file_path}:
                - File Type: PDF Document
                - Format: PDF
                - Status: Ready for document analysis
                - Capabilities: Can extract text, analyze structure, identify sections, read tables
                - Instructions: Use this file to extract and analyze document content"""
    
    else:
        return f"""File Processing for {file_path}:
                - File Type: {file_extension if file_extension else 'Unknown'}
                - Status: Unsupported format
                - Supported formats: Images (.png, .jpg, .jpeg) and Documents (.pdf)
                - Please upload a file in one of the supported formats"""

# Define your custom agent
root_agent = LlmAgent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction="""Your task is to process and analyze user-uploaded files including images and PDF documents.
    
    **Workflow:**
    1. When a file is uploaded, first use the `load_artifacts_tool` to access it.
    2. Then use the `file_processing_function` to identify the file type and get processing instructions.
    3. Based on the file type:
       - **Images (.png, .jpg, .jpeg)**: Analyze the visual content, describe what you see, identify objects, read any text present, and provide insights.
       - **PDF Documents (.pdf)**: Extract and analyze the text content, summarize key information, identify document structure.
    4. Provide a comprehensive analysis to the user based on the file content.
    
    **Important Instructions:**
    - Always check the user's most recent turn for uploaded files (artifacts) before responding.
    - If a file is present, immediately use that file as the primary context for your answer.
    - DO NOT ask the user to upload a file if one has already been provided.
    - Acknowledge the file type and provide detailed analysis based on its content.
    - For unsupported formats, inform the user about supported formats (.png, .jpg, .jpeg, .pdf).
    """,
    tools=[load_artifacts_tool, file_processing_function],
)
