import os
import sys
import vertexai
from dotenv import load_dotenv
from vertexai.preview import reasoning_engines
from agent import root_agent

def main():
    """Deploys the file processing agent to Agent Engine using the Vertex AI SDK."""

    # --- Load Environment Variables ---
    load_dotenv()

    required_vars = [
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "STAGING_BUCKET",
    ]
    for var in required_vars:
        if not os.getenv(var):
            print(f"Error: Required environment variable {var} is not set correctly in .env", file=sys.stderr)
            print("Please create and configure the .env file.", file=sys.stderr)
            sys.exit(1)

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION")
    staging_bucket = os.getenv("STAGING_BUCKET")

    # --- Initialize Vertex AI ---
    print("🔧 Initializing Vertex AI...")
    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=staging_bucket
    )
    print("✅ Vertex AI initialized.")

    # --- Prepare the Agent for Deployment ---
    app = reasoning_engines.AdkApp(agent=root_agent, enable_tracing=True)

    # --- Deploy to Agent Engine ---
    AGENT_DISPLAY_NAME = os.getenv("AGENT_DISPLAY_NAME", "File Processing Agent")
    AGENT_DESCRIPTION = os.getenv("AGENT_DESCRIPTION", "An agent that can process and analyze uploaded files like images and PDFs.")

    print("🚀 Deploying agent to Agent Engine...")
    print(f"   Display Name: {AGENT_DISPLAY_NAME}")

    try:
        engine = reasoning_engines.ReasoningEngine.create(
            app,
            display_name=AGENT_DISPLAY_NAME,
            description=AGENT_DESCRIPTION,
            requirements=["Pillow", "PyPDF2"],
            extra_packages=["agent.py"],
        )
        print(f"\n✅ Agent deployed successfully!")
        print(f"   Resource Name: {engine.resource_name}")
        print(f"   Display Name: {engine.display_name}")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred during deployment: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()