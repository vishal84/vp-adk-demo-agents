from google.adk.agents import LlmAgent
from google.adk.tools.load_artifacts_tool import load_artifacts_tool
from google.adk.tools.tool_context import ToolContext
from pathlib import Path
from typing import Dict, Any
import io
from PIL import Image
import PyPDF2

def file_processing_function(file_name: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Process and analyze files from uploaded artifacts. Extracts content from images and PDFs.
    
    Args:
        file_name: The name of the file to process
        tool_context: The tool context containing uploaded artifacts
        
    Returns:
        A dictionary containing the extracted content and analysis
    """
    # Get artifacts from tool context state
    artifacts = tool_context.state.get('artifacts', [])
    
    if not artifacts:
        return {
            "status": "error",
            "message": "No artifacts found. Please upload a file first using load_artifacts_tool."
        }
    
    # Find the matching artifact
    target_artifact = None
    for artifact in artifacts:
        if artifact.name == file_name or file_name in artifact.name:
            target_artifact = artifact
            break
    
    if not target_artifact:
        available_files = [a.name for a in artifacts]
        return {
            "status": "error",
            "message": f"File '{file_name}' not found in artifacts. Available files: {', '.join(available_files)}"
        }
    
    # Get file extension
    file_extension = Path(target_artifact.name).suffix.lower()
    
    # Supported formats
    image_formats = ['.png', '.jpg', '.jpeg']
    document_formats = ['.pdf']
    
    # Read file content
    file_data = target_artifact.data
    
    try:
        if file_extension in image_formats:
            # Process image
            image = Image.open(io.BytesIO(file_data))
            
            # Extract image properties
            width, height = image.size
            mode = image.mode
            format_name = image.format
            
            # Get color information
            if mode == 'RGB':
                color_info = "Full color (RGB)"
            elif mode == 'RGBA':
                color_info = "Full color with transparency (RGBA)"
            elif mode == 'L':
                color_info = "Grayscale"
            else:
                color_info = f"Color mode: {mode}"
            
            # Calculate aspect ratio
            aspect_ratio = round(width / height, 2)
            
            return {
                "status": "success",
                "file_type": "image",
                "file_name": target_artifact.name,
                "analysis": f"""Image Analysis Results:

**Basic Properties:**
- Dimensions: {width} x {height} pixels
- Aspect Ratio: {aspect_ratio}:1
- Format: {format_name}
- Color Mode: {color_info}
- File Size: {len(file_data):,} bytes

**Image Characteristics:**
- Resolution: {width * height:,} total pixels
- Suitable for: {'High resolution display' if width >= 1920 else 'Standard display' if width >= 1280 else 'Thumbnail/small display'}

The image has been successfully loaded and is ready for visual analysis by vision-capable models.
You can now describe what you see in the image, identify objects, read text, or answer questions about its content."""
            }
        
        elif file_extension in document_formats:
            # Process PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
            
            num_pages = len(pdf_reader.pages)
            
            # Extract text from all pages
            extracted_text = []
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    extracted_text.append(f"--- Page {page_num} ---\n{text}")
            
            full_text = "\n\n".join(extracted_text)
            word_count = len(full_text.split())
            char_count = len(full_text)
            
            # Get document info if available
            metadata = pdf_reader.metadata
            doc_info = ""
            if metadata:
                if metadata.title:
                    doc_info += f"\n- Title: {metadata.title}"
                if metadata.author:
                    doc_info += f"\n- Author: {metadata.author}"
                if metadata.subject:
                    doc_info += f"\n- Subject: {metadata.subject}"
            
            return {
                "status": "success",
                "file_type": "pdf",
                "file_name": target_artifact.name,
                "analysis": f"""PDF Document Analysis Results:

**Document Properties:**
- Pages: {num_pages}
- File Size: {len(file_data):,} bytes{doc_info}

**Content Statistics:**
- Total Characters: {char_count:,}
- Total Words: {word_count:,}
- Average Words per Page: {word_count // num_pages if num_pages > 0 else 0}

**Extracted Content:**

{full_text[:5000]}{'...\n\n[Content truncated - showing first 5000 characters]' if len(full_text) > 5000 else ''}

The full text has been extracted and is ready for analysis."""
            }
        
        else:
            return {
                "status": "error",
                "file_type": "unsupported",
                "file_name": target_artifact.name,
                "format": file_extension if file_extension else "Unknown",
                "message": "Unsupported format. Supported formats: Images (.png, .jpg, .jpeg) and Documents (.pdf)"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error processing file '{file_name}': {str(e)}"
        }

# Define your custom agent
root_agent = LlmAgent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction="""Your task is to process and analyze user-uploaded files including images and PDF documents.
    
    **CRITICAL Workflow - Follow Every Time:**
    1. **ALWAYS start by calling `load_artifacts_tool` FIRST** - This must be done every single time, even if you processed a file before. This loads the current artifacts into the context.
    2. After loading artifacts, use `file_processing_function` with the filename to analyze the file.
    3. Based on the file type returned:
       - **Images (.png, .jpg, .jpeg)**: The function will extract image properties. Describe what you understand about the image.
       - **PDF Documents (.pdf)**: The function will extract the full text content. Analyze and summarize the extracted text.
    4. Provide a comprehensive analysis to the user based on the extracted content.
    
    **Important Rules:**
    - **NEVER skip calling `load_artifacts_tool` first** - it must be called before EVERY `file_processing_function` call
    - When a user asks about a file, ALWAYS call `load_artifacts_tool` then `file_processing_function` in that order
    - If `file_processing_function` reports no artifacts found, you forgot to call `load_artifacts_tool` first
    - DO NOT ask the user to upload a file if one has already been provided
    - For PDF files, the extracted text will be in the analysis result - use that text to answer questions
    - For unsupported formats, inform the user about supported formats (.png, .jpg, .jpeg, .pdf)
    
    **Example workflow when user asks "What's in the PDF?":**
    1. Call `load_artifacts_tool` (loads artifacts)
    2. Call `file_processing_function` with the PDF filename (extracts text)
    3. Read the extracted text from the result
    4. Answer the user's question based on that text
    """,
    tools=[load_artifacts_tool, file_processing_function],
)
