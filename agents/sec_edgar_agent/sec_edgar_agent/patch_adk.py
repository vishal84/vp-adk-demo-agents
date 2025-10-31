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
            # when testing locally you can hardcode the identity token token here temporarily
            #access_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImI1ZTQ0MGFlOTQxZTk5ODFlZTJmYTEzNzZkNDJjNDZkNzMxZGVlM2YiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiIzMjU1NTk0MDU1OS5hcHBzLmdvb2dsZXVzZXJjb250ZW50LmNvbSIsImF1ZCI6IjMyNTU1OTQwNTU5LmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwic3ViIjoiMTA0MjU1ODA0MjcxMTk4NTUxNzY0IiwiaGQiOiJ2aXNoYWxhcGF0ZWwuYWx0b3N0cmF0LmNvbSIsImVtYWlsIjoidmlzaGFsQHZpc2hhbGFwYXRlbC5hbHRvc3RyYXQuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImF0X2hhc2giOiJ6SkowemxEbm9ieXhNVFZueWN0Q25RIiwiaWF0IjoxNzYxOTIwNTQ2LCJleHAiOjE3NjE5MjQxNDZ9.ESTDoWyMOgTXP5kAkWPc649e_PqP9zHVyI47bSbP-CnwjmTuRjzJDsRk1JErGIMn3CB70mP_ydYps1eRnO5GNmwt9c01iKmVtHH0o6_BxFQCb8xNcAddKnfSELW46EYGMCAtowhsCLgSnBo_4ijhhfIAB16DGyoMMYyM1uZ5bDz9xmUC6qmkVIe3HH4vm5_ScdB2pdfmNWGWkpyxsmaiq2ylqaextCYqatQNBxHsX-l9AF71fYuo4ZzSfhWtc6y3Wq_g22IviMsonfmh3ko97KtXTNIJ5pGp4IPyQlhvlMgaA9pbhMeYL0WoTOGQ8EZ9A8namjOU4vyLUMSUT4Obxg" # FIXME
            
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