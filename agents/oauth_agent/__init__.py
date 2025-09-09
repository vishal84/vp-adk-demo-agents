import os

if os.getenv("LOCAL_DEV", "TRUE").lower() in ("true", "1", "t"):
    from .agent_local import root_agent
else:
    from .agent_as import root_agent