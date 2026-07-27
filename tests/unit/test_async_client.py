"""Unit tests for AsyncAPIClient."""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import timedelta
from lashtest.core.async_client import AsyncAPIClient, AsyncRequest, AsyncResponse
from lashtest.http.auth import BearerToken


# ── helpers ───────────────────────────────────────────────────────────────────

def make_raw_httpx_response(status_code=200, json_data=None):
    raw = MagicMock()
    raw.status_code = status_code
    raw.headers = {"Content-Type": "application/json"}
    raw.elapsed = timedelta(seconds=0.1)
    raw.text = "{}"
    raw.json.return_value = json_data or {}
    return raw


# ── availability guard ────────────────────────────────────────────────────────

httpx = pytest.importorskip("httpx", reason="httpx not installed")


# ── AsyncResponse ─────────────────────────────────────────────────────────────

class TestAsyncResponse:

    def test_status_code(self):
        r = AsyncResponse(make_raw_httpx_response(201))
        assert r.status_code == 201

    def test_ok_true_for_2xx(self):
        for code in [200, 201, 204]:
            assert AsyncResponse(make_raw_httpx_response(code)).ok is True

    def test_ok_false_for_4xx(self):
        assert AsyncResponse(make_raw_httpx_response(404)).ok is False

    def test_assert_status_passes(self):
        r = AsyncResponse(make_raw_httpx_response(200))
        r.assert_status(200)

    def test_assert_status_fails(self):
        r = AsyncResponse(make_raw_httpx_response(200))
        with pytest.raises(AssertionError):
            r.assert_status(201)

    def test_assert_ok_passes(self):
        r = AsyncResponse(make_raw_httpx_response(200))
        r.assert_ok()

    def test_assert_ok_fails(self):
        r = AsyncResponse(make_raw_httpx_response(500))
        with pytest.raises(AssertionError):
            r.assert_ok()

    def test_assert_header_exists(self):
        r = AsyncResponse(make_raw_httpx_response())
        r.assert_header("Content-Type")

    def test_assert_header_value_match(self):
        r = AsyncResponse(make_raw_httpx_response())
        r.assert_header("Content-Type", "application/json")

    def test_assert_json_contains(self):
        r = AsyncResponse(make_raw_httpx_response(200, {"id": 1, "name": "Alice"}))
        r.assert_json_contains({"id": 1})

    def test_assert_response_time(self):
        r = AsyncResponse(make_raw_httpx_response())
        r.assert_response_time(1.0)


# ── AsyncAPIClient configuration ──────────────────────────────────────────────

class TestAsyncAPIClientConfig:

    def test_base_url_strips_trailing_slash(self):
        client = AsyncAPIClient("https://api.example.com/")
        assert client.base_url == "https://api.example.com"

    def test_with_base_path(self):
        client = AsyncAPIClient("https://api.example.com").with_base_path("/v1")
        assert client.base_path == "/v1"

    def test_with_base_path_raises_for_no_leading_slash(self):
        with pytest.raises(ValueError):
            AsyncAPIClient("https://api.example.com").with_base_path("v1")

    def test_with_header(self):
        client = AsyncAPIClient("https://api.example.com").with_header("X-Key", "val")
        assert client.headers["X-Key"] == "val"

    def test_with_timeout(self):
        client = AsyncAPIClient("https://api.example.com").with_timeout(15.0)
        assert client.timeout == 15.0

    def test_with_timeout_raises_for_non_positive(self):
        with pytest.raises(ValueError):
            AsyncAPIClient("https://api.example.com").with_timeout(0)

    def test_with_auth(self):
        auth = BearerToken("tok")
        client = AsyncAPIClient("https://api.example.com").with_auth(auth)
        assert client.auth is auth

    def test_verb_methods_return_async_request(self):
        client = AsyncAPIClient("https://api.example.com")
        for method in ("get", "post", "put", "patch", "delete"):
            req = getattr(client, method)("/endpoint")
            assert isinstance(req, AsyncRequest)

    def test_validate_endpoint_raises_for_no_slash(self):
        with pytest.raises(ValueError):
            AsyncAPIClient("https://api.example.com").get("no-slash")


# ── AsyncRequest builder ──────────────────────────────────────────────────────

class TestAsyncRequest:

    def make_req(self):
        return AsyncAPIClient("https://api.example.com").get("/users")

    def test_with_header_chainable(self):
        r = self.make_req()
        assert r.with_header("X-H", "v") is r

    def test_with_param_adds_param(self):
        r = self.make_req().with_param("page", "1")
        assert r.params["page"] == "1"

    def test_with_json_sets_body_and_content_type(self):
        r = self.make_req().with_json({"key": "val"})
        assert r.body == {"key": "val"}
        assert r.headers["Content-Type"] == "application/json"

    def test_with_auth_overrides(self):
        auth = BearerToken("req-tok")
        r = self.make_req().with_auth(auth)
        assert r.auth is auth

    def test_with_timeout(self):
        r = self.make_req().with_timeout(5.0)
        assert r.timeout == 5.0


# ── async context manager ─────────────────────────────────────────────────────

class TestAsyncContextManager:

    @pytest.mark.asyncio
    async def test_async_context_manager_returns_response(self):
        client = AsyncAPIClient("https://api.example.com")
        mock_raw = make_raw_httpx_response(200, {"id": 1})

        async def mock_send(request):
            return AsyncResponse(mock_raw)

        client._send = mock_send
        async with client.get("/users/1") as resp:
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_client_context_manager_closes(self):
        client = AsyncAPIClient("https://api.example.com")
        close_called = []

        async def mock_close():
            close_called.append(True)

        client.close = mock_close
        async with client:
            pass
        assert close_called == [True]
