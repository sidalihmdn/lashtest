import base64
import time
import threading
from typing import Optional, Any, Dict, Callable

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
        """Add ****** header to headers dict."""
        scheme = "Bearer"
        headers["Authorization"] = scheme + " " + self.token
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


class OAuth2ClientCredentials(Auth):
    """OAuth2 client-credentials flow.

    Fetches and caches a token from *token_url* using the given
    *client_id* / *client_secret*.  The token is refreshed automatically
    when it expires (based on the ``expires_in`` field returned by the
    server, minus a 10-second safety margin).

    Args:
        token_url: The OAuth2 token endpoint.
        client_id: The client identifier.
        client_secret: The client secret.
        scope: Optional space-separated scope string.
    """

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: Optional[str] = None,
    ) -> None:
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self._token: Optional[str] = None
        self._expires_at: float = 0.0
        self._lock = threading.Lock()

    def _fetch_token(self) -> None:
        import requests as _requests
        data: Dict[str, str] = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.scope:
            data["scope"] = self.scope
        response = _requests.post(self.token_url, data=data)
        response.raise_for_status()
        payload = response.json()
        self._token = payload["access_token"]
        expires_in = float(payload.get("expires_in", 3600))
        self._expires_at = time.monotonic() + expires_in - 10

    def _get_token(self) -> str:
        with self._lock:
            if self._token is None or time.monotonic() >= self._expires_at:
                self._fetch_token()
        return self._token  # type: ignore[return-value]

    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        scheme = "Bearer"
        headers["Authorization"] = scheme + " " + self._get_token()
        return headers


class OAuth2RefreshToken(Auth):
    """OAuth2 refresh-token flow.

    Uses an existing *refresh_token* to obtain (and cache) a fresh
    access token.  When the access token expires the refresh token is
    used again automatically.

    Args:
        token_url: The OAuth2 token endpoint.
        client_id: The client identifier.
        client_secret: The client secret.
        refresh_token: A long-lived refresh token.
        scope: Optional space-separated scope string.
    """

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        scope: Optional[str] = None,
    ) -> None:
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.scope = scope
        self._token: Optional[str] = None
        self._expires_at: float = 0.0
        self._lock = threading.Lock()

    def _fetch_token(self) -> None:
        import requests as _requests
        data: Dict[str, str] = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }
        if self.scope:
            data["scope"] = self.scope
        response = _requests.post(self.token_url, data=data)
        response.raise_for_status()
        payload = response.json()
        self._token = payload["access_token"]
        if "refresh_token" in payload:
            self.refresh_token = payload["refresh_token"]
        expires_in = float(payload.get("expires_in", 3600))
        self._expires_at = time.monotonic() + expires_in - 10

    def _get_token(self) -> str:
        with self._lock:
            if self._token is None or time.monotonic() >= self._expires_at:
                self._fetch_token()
        return self._token  # type: ignore[return-value]

    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        scheme = "Bearer"
        headers["Authorization"] = scheme + " " + self._get_token()
        return headers


class CustomTokenProvider(Auth):
    """Auth backed by an arbitrary callable that returns a token string.

    The callable is invoked for every request so it can implement any
    caching or refresh strategy the caller needs.

    Args:
        provider: A zero-argument callable that returns the current token.
        header_name: Header to set. Defaults to ``"Authorization"``.
        scheme: Token scheme prefix. Defaults to ``"Bearer"``.  Pass an
            empty string to send the raw token value with no prefix.

    Example::

        def get_token():
            return vault_client.read_secret("api/token")["data"]["value"]

        client = APIClient('https://api.example.com').with_auth(
            CustomTokenProvider(get_token)
        )
    """

    def __init__(
        self,
        provider: Callable[[], str],
        header_name: str = "Authorization",
        scheme: str = "Bearer",
    ) -> None:
        self.provider = provider
        self.header_name = header_name
        self.scheme = scheme

    def apply(self, headers: Dict[str, str]) -> Dict[str, str]:
        token = self.provider()
        headers[self.header_name] = f"{self.scheme} {token}".strip() if self.scheme else token
        return headers
