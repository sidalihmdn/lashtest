"""Async API client backed by ``httpx``."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Union

from ..http.auth import Auth
from ..utils.logger import get_logger

logger = get_logger()


class AsyncResponse:
    """Thin wrapper around an ``httpx.Response`` with the same assertion API
    as the synchronous :class:`~lashtest.core.response.Response`.
    """

    def __init__(self, raw: Any) -> None:
        self._raw = raw
        self.status_code: int = raw.status_code
        self.headers: Dict[str, str] = dict(raw.headers)
        self.elapsed: float = raw.elapsed.total_seconds()
        self._json_cache: Optional[Any] = None

    @property
    def text(self) -> str:
        return self._raw.text

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        if self._json_cache is None:
            try:
                self._json_cache = self._raw.json()
            except Exception:
                raise ValueError("Response body is not valid JSON")
        return self._json_cache

    # ── assertions ────────────────────────────────────────────────────────────

    def assert_status(self, expected: int) -> "AsyncResponse":
        assert self.status_code == expected, (
            f"Expected status code {expected}, got {self.status_code}"
        )
        return self

    def assert_ok(self) -> "AsyncResponse":
        assert self.ok, f"Expected 2xx status, got {self.status_code}"
        return self

    def assert_header(self, key: str, expected_value: Optional[str] = None) -> "AsyncResponse":
        actual = self.headers.get(key)
        assert actual is not None, f"Expected header '{key}' to be present but it was not found"
        if expected_value is not None:
            assert actual == expected_value, (
                f"Expected header '{key}' to be '{expected_value}', got '{actual}'"
            )
        return self

    def assert_json_contains(self, expected_subset: Dict[str, Any]) -> "AsyncResponse":
        actual = self.json()
        assert isinstance(actual, dict), f"Expected JSON dict, got {type(actual)}"
        for k, v in expected_subset.items():
            assert k in actual, f"Expected key '{k}' not found in response JSON"
            assert actual[k] == v, f"Expected key '{k}' to have value '{v}', got '{actual[k]}'"
        return self

    def assert_response_time(self, max_time: float) -> "AsyncResponse":
        assert self.elapsed < max_time, (
            f"Expected response time < {max_time}s, got {self.elapsed}s"
        )
        return self


class AsyncRequest:
    """Fluent async request builder.  Use as an async context manager::

        async with client.get('/users/1') as response:
            response.assert_ok()
    """

    def __init__(self, client: "AsyncAPIClient", method: str, endpoint: str) -> None:
        self.client = client
        self.method = method
        self.endpoint = endpoint
        self.headers: Dict[str, str] = {}
        self.params: Dict[str, str] = {}
        self.body: Optional[Any] = None
        self.data: Optional[Any] = None
        self.auth: Optional[Auth] = None
        self.timeout: float = client.timeout

    def with_header(self, key: str, value: str) -> "AsyncRequest":
        self.headers[key] = value
        return self

    def with_param(self, key: str, value: str) -> "AsyncRequest":
        self.params[key] = value
        return self

    def with_params(self, params: Dict[str, str]) -> "AsyncRequest":
        self.params.update(params)
        return self

    def with_json(self, body: Any) -> "AsyncRequest":
        self.body = body
        self.headers["Content-Type"] = "application/json"
        return self

    def with_body(self, body: Any) -> "AsyncRequest":
        self.body = body
        return self

    def with_data(self, data: Any) -> "AsyncRequest":
        self.data = data
        return self

    def with_auth(self, auth: Auth) -> "AsyncRequest":
        self.auth = auth
        return self

    def with_timeout(self, timeout: float) -> "AsyncRequest":
        self.timeout = timeout
        return self

    async def send(self) -> AsyncResponse:
        """Execute the request and return an :class:`AsyncResponse`."""
        return await self.client._send(self)

    async def __aenter__(self) -> AsyncResponse:
        self._response = await self.send()
        return self._response

    async def __aexit__(self, *_: Any) -> None:
        pass


class AsyncAPIClient:
    """An async API client built on ``httpx``.

    Requires ``httpx``::

        pip install httpx

    Mirrors the synchronous :class:`~lashtest.core.client.APIClient` interface
    but uses ``async``/``await``::

        import asyncio
        from lashtest.core.async_client import AsyncAPIClient

        async def test_async():
            async with AsyncAPIClient('https://api.example.com') as client:
                async with client.get('/users/1') as response:
                    response.assert_ok()

        asyncio.run(test_async())

    Args:
        base_url: Base URL for all requests (trailing slash stripped).
    """

    def __init__(self, base_url: str) -> None:
        try:
            import httpx
        except ImportError:
            raise ImportError(
                "httpx is required for AsyncAPIClient. "
                "Install it with: pip install httpx"
            )
        self.base_url = base_url.rstrip("/")
        self.base_path: Optional[str] = None
        self.headers: Dict[str, str] = {}
        self.auth: Optional[Auth] = None
        self.timeout: float = 30.0
        self._client: Optional[Any] = None
        self._httpx = httpx

    # ── configuration ─────────────────────────────────────────────────────────

    def with_base_path(self, base_path: str) -> "AsyncAPIClient":
        if not isinstance(base_path, str) or not base_path.startswith("/"):
            raise ValueError("Base path must be a string starting with '/'")
        self.base_path = base_path
        return self

    def with_header(self, key: str, value: str) -> "AsyncAPIClient":
        self.headers[key] = value
        return self

    def with_headers(self, headers: Dict[str, str]) -> "AsyncAPIClient":
        self.headers.update(headers)
        return self

    def with_auth(self, auth: Auth) -> "AsyncAPIClient":
        if not isinstance(auth, Auth):
            raise ValueError("Auth must be an instance of Auth class")
        self.auth = auth
        return self

    def with_timeout(self, timeout: float) -> "AsyncAPIClient":
        if timeout <= 0:
            raise ValueError("Timeout must be a positive number")
        self.timeout = timeout
        return self

    # ── request factories ─────────────────────────────────────────────────────

    def _validate_endpoint(self, endpoint: str) -> None:
        if not isinstance(endpoint, str) or not endpoint.startswith("/"):
            raise ValueError(f"Invalid endpoint: {endpoint!r}. Must start with '/'.")

    def get(self, endpoint: str) -> AsyncRequest:
        self._validate_endpoint(endpoint)
        return AsyncRequest(self, "GET", endpoint)

    def post(self, endpoint: str) -> AsyncRequest:
        self._validate_endpoint(endpoint)
        return AsyncRequest(self, "POST", endpoint)

    def put(self, endpoint: str) -> AsyncRequest:
        self._validate_endpoint(endpoint)
        return AsyncRequest(self, "PUT", endpoint)

    def patch(self, endpoint: str) -> AsyncRequest:
        self._validate_endpoint(endpoint)
        return AsyncRequest(self, "PATCH", endpoint)

    def delete(self, endpoint: str) -> AsyncRequest:
        self._validate_endpoint(endpoint)
        return AsyncRequest(self, "DELETE", endpoint)

    # ── internal ──────────────────────────────────────────────────────────────

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}{self.base_path or ''}/{endpoint.lstrip('/')}"

    async def _send(self, request: AsyncRequest) -> AsyncResponse:
        if self._client is None:
            self._client = self._httpx.AsyncClient(timeout=self.timeout)

        url = self._build_url(request.endpoint)
        merged_headers = {**self.headers, **request.headers}

        auth_to_use = request.auth or self.auth
        if auth_to_use and hasattr(auth_to_use, "apply"):
            merged_headers = auth_to_use.apply(merged_headers)

        logger.debug(f" -> async {request.method} {url}")

        kwargs: Dict[str, Any] = {
            "method": request.method,
            "url": url,
            "headers": merged_headers,
            "params": request.params,
            "timeout": request.timeout,
        }
        if request.body is not None:
            kwargs["json"] = request.body
        if request.data is not None:
            kwargs["data"] = request.data

        raw = await self._client.request(**kwargs)
        logger.debug(f" <- async {raw.status_code}")
        return AsyncResponse(raw)

    # ── lifecycle ─────────────────────────────────────────────────────────────

    async def close(self) -> None:
        """Close the underlying httpx client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "AsyncAPIClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
