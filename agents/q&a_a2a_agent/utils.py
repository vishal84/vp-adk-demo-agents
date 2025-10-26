import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any, cast

from google.auth import default
from google.auth.credentials import Credentials as GoogleCredentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from starlette.requests import Request

logging.getLogger().setLevel(logging.INFO)


def receive_wrapper(data: dict[str, Any] | None = None) -> Callable[[], Awaitable[dict[str, Any]]]:
    """Creates a mock ASGI receive callable for testing."""

    async def receive():
        payload = data if data is not None else {}
        byte_data = json.dumps(payload).encode("utf-8")
        return {"type": "http.request", "body": byte_data, "more_body": False}

    return receive


def build_post_request(
    data: dict[str, Any] | None = None, path_params: dict[str, str] | None = None
) -> Request:
    """Builds a mock Starlette Request object for a POST request with JSON data."""
    scope = {
        "type": "http",
        "http_version": "1.1",
        "headers": [(b"content-type", b"application/json")],
        "app": None,
    }
    if path_params:
        scope["path_params"] = path_params
    receiver = receive_wrapper(data)
    return Request(scope, receiver)


def build_get_request(path_params: dict[str, str] | None = None) -> Request:
    """Builds a mock Starlette Request object for a GET request."""
    scope = {
        "type": "http",
        "http_version": "1.1",
        "query_string": b"",
        "app": None,
    }
    if path_params:
        scope["path_params"] = path_params

    async def receive():
        return {"type": "http.disconnect"}

    return Request(scope, receive)


def get_bearer_token() -> str | None:
    """Fetches a Google Cloud bearer token using Application Default Credentials."""
    try:
        credentials, _ = default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        google_credentials = cast(GoogleCredentials, credentials)
        google_credentials.refresh(GoogleAuthRequest())
        return google_credentials.token
    except Exception as e:
        print(f"Error getting credentials: {e}")
        print(
            "Please ensure you have authenticated with 'gcloud auth application-default login'."
        )
    return None