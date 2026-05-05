import base64
from typing import Optional, Any, Dict

class Auth:
    """Base class for authentication methods."""
    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Apply authentication to the given headers dictionary."""
        raise NotImplementedError("Auth subclasses must implement the apply method")

class BasicAuth(Auth):
    """Authentication using basic HTTP authentication."""
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Add Basic Auth header to headers dict."""
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers["Authorization"] = f"Basic {encoded_credentials}"
        return headers

class BearerToken(Auth):
    """Authentication using a bearer token."""
    def __init__(self, token: str) -> None:
        self.token = token

    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Add Bearer token header to headers dict."""
        headers["Authorization"] = f"Bearer {self.token}"
        return headers

class APIKey(Auth):
    """Authentication using an API key in a custom header."""
    def __init__(self, header_name: str = "X-API-KEY", api_key: str = "") -> None:
        self.header_name = header_name
        self.api_key = api_key

    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Add API key header to headers dict."""
        headers[self.header_name] = self.api_key
        return headers