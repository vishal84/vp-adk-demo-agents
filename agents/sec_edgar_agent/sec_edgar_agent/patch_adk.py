"""
Patch for adding agentspace_auth_resource authentication scheme support
to Google ADK's McpTool._get_headers method.
"""

import logging
from typing import Optional
from google.adk.tools.mcp_tool.mcp_tool import McpTool
from google.adk.auth.auth_credential import AuthCredential
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

# Store the original method
_original_get_headers = McpTool._get_headers


async def _patched_get_headers(
    self, tool_context: ToolContext, credential: AuthCredential
) -> Optional[dict[str, str]]:
    """
    Patched version of _get_headers that adds support for agentspace_auth_resource scheme.
    
    Args:
        tool_context: The tool context of the current invocation.
        credential: The authentication credential to process.
        
    Returns:
        Dictionary of headers to add to the request, or None if no auth.
    """
    # Check for the new agentspace_auth_resource scheme first
    if (credential and 
        credential.http and 
        credential.http.scheme.lower() == "agentspace_auth_resource"):

        if hasattr(credential.http, 'agentspace_authentication_resource_auth_id'):
            auth_id = credential.http.agentspace_authentication_resource_auth_id
            access_token = tool_context.state.get(f"temp:{auth_id}")
            # access_token = "TEST123" # FIXME
            
            if access_token:
                logger.debug(f"Using agentspace_auth_resource token for auth_id: {auth_id}")
                return {"Authorization": f"Bearer {access_token}"}
            else:
                logger.warning(f"No access token found for auth_id: {auth_id}")
                return None
        else:
            logger.error("agentspace_auth_resource scheme specified but no agentspace_authentication_resource found")
            return None
    
    # Fall back to original implementation for all other cases
    return await _original_get_headers(self, tool_context, credential)


def apply_patch():
    """Apply the patch to McpTool._get_headers method."""
    McpTool._get_headers = _patched_get_headers
    logger.info("Applied agentspace_auth_resource patch to McpTool._get_headers")


def remove_patch():
    """Remove the patch and restore original functionality."""
    McpTool._get_headers = _original_get_headers
    logger.info("Removed agentspace_auth_resource patch from McpTool._get_headers")


# Auto-apply the patch when this module is imported
apply_patch()