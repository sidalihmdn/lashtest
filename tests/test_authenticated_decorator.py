"""
Tests for the @authenticated decorator applied at the class level.
Uses httpbin.org endpoints that verify authentication.
"""

import pytest
import lashtest
from lashtest import APIClient
from lashtest.http import BasicAuth, BearerToken, APIKey
from lashtest.decorators import authenticated


# ── Bearer token ──────────────────────────────────────────────────────────────

@authenticated(BearerToken('my-secret-token'))
class TestBearerAuthentication:
    """All tests in this class run with Bearer token authentication."""

    client = APIClient('https://httpbin.org').with_header("User-Agent", "lashtest-authenticated-decorator-tests/1.0")

    def test_bearer_is_authenticated(self):
        """httpbin /bearer returns 200 only if a valid Bearer token is present."""
        with self.client.get('/bearer') as response:
            response.assert_status(200) \
                    .assert_ok() \
                    .assert_json_contains({'authenticated': True})

    def test_bearer_token_value_is_correct(self):
        """Verify the exact token value received by the server."""
        with self.client.get('/bearer') as response:
            response.assert_status(200) \
                    .assert_json_contains({'token': 'my-secret-token'})

    def test_authorization_header_is_present(self):
        """Verify the Authorization header is sent on every request."""
        with self.client.get('/headers') as response:
            response.assert_status(200)
            headers = response.json()['headers']
            assert 'Authorization' in headers
            assert headers['Authorization'] == 'Bearer my-secret-token'


# ── Basic auth ────────────────────────────────────────────────────────────────

@authenticated(BasicAuth('testuser', 'testpass'))
class TestBasicAuthentication:
    """All tests in this class run with Basic authentication."""

    client = APIClient('https://httpbin.org').with_header("User-Agent", "lashtest-authenticated-decorator-tests/1.0")

    def test_basic_auth_succeeds(self):
        """httpbin /basic-auth/{user}/{pass} returns 200 only with correct credentials."""
        with self.client.get('/basic-auth/testuser/testpass') as response:
            response.assert_status(200) \
                    .assert_ok() \
                    .assert_json_contains({'authenticated': True, 'user': 'testuser'})

    def test_authorization_header_is_present(self):
        """Verify the Authorization header is sent with Basic scheme."""
        with self.client.get('/headers') as response:
            response.assert_status(200)
            headers = response.json()['headers']
            assert 'Authorization' in headers
            assert headers['Authorization'].startswith('Basic ')

    def test_wrong_credentials_returns_401(self):
        """Confirm that wrong credentials fail even with the decorator applied."""
        with self.client.get('/basic-auth/wronguser/wrongpass') as response:
            response.assert_status(401)


# ── API key ───────────────────────────────────────────────────────────────────

@authenticated(APIKey(header_name='X-API-Key', api_key='super-secret-key'))
class TestAPIKeyAuthentication:
    """All tests in this class run with API key authentication."""

    client = APIClient('https://httpbin.org').with_header("User-Agent", "lashtest-authenticated-decorator-tests/1.0")

    def test_api_key_header_is_sent(self):
        """Verify the API key header is present on every request."""
        with self.client.get('/headers') as response:
            response.assert_status(200)
            headers = response.json()['headers']
            assert 'X-Api-Key' in headers or 'X-API-Key' in headers

    def test_api_key_value_is_correct(self):
        """Verify the exact API key value received by the server."""
        with self.client.get('/headers') as response:
            response.assert_status(200)
            headers = response.json()['headers']
            key = headers.get('X-Api-Key') or headers.get('X-API-Key')
            assert key == 'super-secret-key'


# ── Method-level override ─────────────────────────────────────────────────────

@authenticated(BearerToken('default-token'))
class TestMethodLevelOverride:
    """Class uses default Bearer token, one method overrides with a different token."""

    client = APIClient('https://httpbin.org')\
        .with_header("User-Agent", "lashtest-authenticated-decorator-tests/1.0")

    @lashtest.title("Test that class-level Bearer token is used by default")
    def test_uses_default_token(self):
        """Uses the class-level Bearer token."""
        with self.client.get('/bearer') as response:
            response.assert_status(200) \
                    .assert_json_contains({'token': 'default-token'})

    @authenticated(BearerToken('override-token'))
    def test_uses_override_token(self):
        """Overrides the class-level token with a different one."""
        with self.client.get('/bearer') as response:
            response.assert_status(200) \
                    .assert_json_contains({'token': 'override-token'})

    def test_default_token_restored_after_override(self):
        """Confirms the class-level token is restored after the override test."""
        with self.client.get('/bearer') as response:
            response.assert_status(200) \
                    .assert_json_contains({'token': 'default-token'})
