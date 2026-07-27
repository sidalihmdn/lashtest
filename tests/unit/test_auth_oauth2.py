"""Unit tests for new auth types: OAuth2ClientCredentials, OAuth2RefreshToken, CustomTokenProvider."""

import time
import pytest
from unittest.mock import MagicMock, patch
from lashtest.http.auth import (
    Auth,
    OAuth2ClientCredentials,
    OAuth2RefreshToken,
    CustomTokenProvider,
)


# ── OAuth2ClientCredentials ───────────────────────────────────────────────────

class TestOAuth2ClientCredentials:

    def _make_token_response(self, access_token="tok123", expires_in=3600):
        resp = MagicMock()
        resp.json.return_value = {"access_token": access_token, "expires_in": expires_in}
        resp.raise_for_status = MagicMock()
        return resp

    def test_is_auth_subclass(self):
        auth = OAuth2ClientCredentials("https://token.example.com", "cid", "secret")
        assert isinstance(auth, Auth)

    @patch("requests.post")
    def test_fetches_token_on_first_apply(self, mock_post):
        mock_post.return_value = self._make_token_response("my-access-token")
        auth = OAuth2ClientCredentials("https://token.example.com", "cid", "csecret")
        headers = auth.apply({})
        assert "Authorization" in headers
        scheme, _, token = headers["Authorization"].partition(" ")
        assert scheme == "Bearer"
        assert token == "my-access-token"

    @patch("requests.post")
    def test_sends_client_credentials_grant(self, mock_post):
        mock_post.return_value = self._make_token_response()
        auth = OAuth2ClientCredentials("https://token.example.com", "my-client", "my-secret")
        auth.apply({})
        called_data = mock_post.call_args.kwargs.get("data") or mock_post.call_args[1].get("data")
        assert called_data["grant_type"] == "client_credentials"
        assert called_data["client_id"] == "my-client"
        assert called_data["client_secret"] == "my-secret"

    @patch("requests.post")
    def test_includes_scope_when_set(self, mock_post):
        mock_post.return_value = self._make_token_response()
        auth = OAuth2ClientCredentials(
            "https://token.example.com", "cid", "csecret", scope="read write"
        )
        auth.apply({})
        called_data = mock_post.call_args.kwargs.get("data") or mock_post.call_args[1].get("data")
        assert called_data["scope"] == "read write"

    @patch("requests.post")
    def test_caches_token(self, mock_post):
        mock_post.return_value = self._make_token_response()
        auth = OAuth2ClientCredentials("https://token.example.com", "cid", "csecret")
        auth.apply({})
        auth.apply({})
        assert mock_post.call_count == 1  # token reused

    @patch("requests.post")
    def test_refreshes_expired_token(self, mock_post):
        mock_post.return_value = self._make_token_response(expires_in=0)
        auth = OAuth2ClientCredentials("https://token.example.com", "cid", "csecret")
        auth.apply({})
        # Force expiry
        auth._expires_at = time.monotonic() - 1
        auth.apply({})
        assert mock_post.call_count == 2

    @patch("requests.post")
    def test_preserves_existing_headers(self, mock_post):
        mock_post.return_value = self._make_token_response()
        auth = OAuth2ClientCredentials("https://token.example.com", "cid", "csecret")
        headers = auth.apply({"X-Custom": "value"})
        assert headers["X-Custom"] == "value"


# ── OAuth2RefreshToken ────────────────────────────────────────────────────────

class TestOAuth2RefreshToken:

    def _make_token_response(self, access_token="access123", refresh_token=None, expires_in=3600):
        payload = {"access_token": access_token, "expires_in": expires_in}
        if refresh_token:
            payload["refresh_token"] = refresh_token
        resp = MagicMock()
        resp.json.return_value = payload
        resp.raise_for_status = MagicMock()
        return resp

    def test_is_auth_subclass(self):
        auth = OAuth2RefreshToken("https://t.example.com", "cid", "sec", "rt")
        assert isinstance(auth, Auth)

    @patch("requests.post")
    def test_fetches_token_on_first_apply(self, mock_post):
        mock_post.return_value = self._make_token_response("acc-tok")
        auth = OAuth2RefreshToken("https://t.example.com", "cid", "sec", "rt123")
        headers = auth.apply({})
        scheme, _, token = headers["Authorization"].partition(" ")
        assert scheme == "Bearer"
        assert token == "acc-tok"

    @patch("requests.post")
    def test_sends_refresh_token_grant(self, mock_post):
        mock_post.return_value = self._make_token_response()
        auth = OAuth2RefreshToken("https://t.example.com", "cid", "sec", "my-refresh")
        auth.apply({})
        called_data = mock_post.call_args.kwargs.get("data") or mock_post.call_args[1].get("data")
        assert called_data["grant_type"] == "refresh_token"
        assert called_data["refresh_token"] == "my-refresh"

    @patch("requests.post")
    def test_rotates_refresh_token_when_server_returns_new_one(self, mock_post):
        mock_post.return_value = self._make_token_response(refresh_token="new-rt")
        auth = OAuth2RefreshToken("https://t.example.com", "cid", "sec", "old-rt")
        auth.apply({})
        assert auth.refresh_token == "new-rt"

    @patch("requests.post")
    def test_keeps_refresh_token_when_server_does_not_rotate(self, mock_post):
        mock_post.return_value = self._make_token_response()  # no refresh_token in response
        auth = OAuth2RefreshToken("https://t.example.com", "cid", "sec", "stable-rt")
        auth.apply({})
        assert auth.refresh_token == "stable-rt"

    @patch("requests.post")
    def test_caches_token(self, mock_post):
        mock_post.return_value = self._make_token_response()
        auth = OAuth2RefreshToken("https://t.example.com", "cid", "sec", "rt")
        auth.apply({})
        auth.apply({})
        assert mock_post.call_count == 1

    @patch("requests.post")
    def test_refreshes_expired_token(self, mock_post):
        mock_post.return_value = self._make_token_response(expires_in=0)
        auth = OAuth2RefreshToken("https://t.example.com", "cid", "sec", "rt")
        auth.apply({})
        auth._expires_at = time.monotonic() - 1
        auth.apply({})
        assert mock_post.call_count == 2


# ── CustomTokenProvider ───────────────────────────────────────────────────────

class TestCustomTokenProvider:

    def test_is_auth_subclass(self):
        auth = CustomTokenProvider(lambda: "tok")
        assert isinstance(auth, Auth)

    def test_calls_provider_on_apply(self):
        called = []
        def provider():
            called.append(True)
            return "dynamic-token"

        auth = CustomTokenProvider(provider)
        headers = auth.apply({})
        assert called == [True]
        scheme, _, token = headers["Authorization"].partition(" ")
        assert scheme == "Bearer"
        assert token == "dynamic-token"

    def test_custom_header_name(self):
        auth = CustomTokenProvider(lambda: "tok", header_name="X-Auth-Token", scheme="")
        headers = auth.apply({})
        assert "X-Auth-Token" in headers
        assert headers["X-Auth-Token"] == "tok"

    def test_custom_scheme(self):
        auth = CustomTokenProvider(lambda: "tok", scheme="Token")
        headers = auth.apply({})
        assert headers["Authorization"].startswith("Token ")

    def test_empty_scheme_sends_raw_token(self):
        auth = CustomTokenProvider(lambda: "rawtoken", scheme="")
        headers = auth.apply({})
        assert headers["Authorization"] == "rawtoken"

    def test_provider_called_every_request(self):
        counter = [0]
        def provider():
            counter[0] += 1
            return f"token-{counter[0]}"

        auth = CustomTokenProvider(provider)
        auth.apply({})
        auth.apply({})
        # provider is called each time (no built-in caching)
        assert counter[0] == 2

    def test_preserves_other_headers(self):
        auth = CustomTokenProvider(lambda: "tok")
        headers = auth.apply({"X-Other": "val"})
        assert headers["X-Other"] == "val"
