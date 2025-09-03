import os

if os.getenv("LOCAL_DEV", "False").lower() in ("true", "1", "t"):
    from . import agent_as
else:
    from . import agent_local