"""Unit tests for lashtest.http.auth"""

import base64
import pytest
from lashtest.http.auth import Auth, BasicAuth, BearerToken, APIKey


# ── Auth base class ───────────────────────────────────────────────────────────

class TestAuthBase:

    def test_apply_raises_not_implemented(self):
        auth = Auth()
        with pytest.raises(NotImplementedError):
            auth.apply({})


# ── BasicAuth ─────────────────────────────────────────────────────────────────

class TestBasicAuth:

    def test_applies_authorization_header(self):
        auth = BasicAuth('user', 'pass')
        headers = auth.apply({})
        assert 'Authorization' in headers

    def test_uses_basic_scheme(self):
        auth = BasicAuth('user', 'pass')
        headers = auth.apply({})
        assert headers['Authorization'].startswith('Basic ')

    def test_encodes_credentials_correctly(self):
        auth = BasicAuth('user', 'pass')
        headers = auth.apply({})
        expected = base64.b64encode(b'user:pass').decode()
        assert headers['Authorization'] == f'Basic {expected}'

    def test_preserves_existing_headers(self):
        auth = BasicAuth('user', 'pass')
        headers = auth.apply({'X-Custom': 'value'})
        assert headers['X-Custom'] == 'value'
        assert 'Authorization' in headers

    def test_returns_headers_dict(self):
        auth = BasicAuth('user', 'pass')
        result = auth.apply({})
        assert isinstance(result, dict)

    def test_special_characters_in_credentials(self):
        auth = BasicAuth('user@domain.com', 'p@ss:w0rd!')
        headers = auth.apply({})
        expected = base64.b64encode(b'user@domain.com:p@ss:w0rd!').decode()
        assert headers['Authorization'] == f'Basic {expected}'


# ── BearerToken ───────────────────────────────────────────────────────────────

class TestBearerToken:

    def test_applies_authorization_header(self):
        auth = BearerToken('my-token')
        headers = auth.apply({})
        assert 'Authorization' in headers

    def test_uses_bearer_scheme(self):
        auth = BearerToken('my-token')
        headers = auth.apply({})
        assert headers['Authorization'].startswith('Bearer ')

    def test_includes_token_value(self):
        auth = BearerToken('my-secret-token')
        headers = auth.apply({})
        assert headers['Authorization'] == 'Bearer my-secret-token'

    def test_preserves_existing_headers(self):
        auth = BearerToken('token')
        headers = auth.apply({'X-Custom': 'value'})
        assert headers['X-Custom'] == 'value'

    def test_returns_headers_dict(self):
        result = BearerToken('t').apply({})
        assert isinstance(result, dict)

    def test_empty_token(self):
        auth = BearerToken('')
        headers = auth.apply({})
        assert headers['Authorization'] == 'Bearer '

    def test_jwt_token(self):
        token = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.signature'
        auth = BearerToken(token)
        headers = auth.apply({})
        assert headers['Authorization'] == f'Bearer {token}'


# ── APIKey ────────────────────────────────────────────────────────────────────

class TestAPIKey:

    def test_default_header_name(self):
        auth = APIKey(api_key='secret')
        headers = auth.apply({})
        assert 'X-API-KEY' in headers

    def test_custom_header_name(self):
        auth = APIKey(header_name='X-Custom-Key', api_key='secret')
        headers = auth.apply({})
        assert 'X-Custom-Key' in headers

    def test_includes_api_key_value(self):
        auth = APIKey(header_name='X-API-Key', api_key='my-secret-key')
        headers = auth.apply({})
        assert headers['X-API-Key'] == 'my-secret-key'

    def test_preserves_existing_headers(self):
        auth = APIKey(api_key='key')
        headers = auth.apply({'X-Other': 'value'})
        assert headers['X-Other'] == 'value'

    def test_returns_headers_dict(self):
        result = APIKey(api_key='k').apply({})
        assert isinstance(result, dict)

    def test_empty_api_key(self):
        auth = APIKey(api_key='')
        headers = auth.apply({})
        assert headers['X-API-KEY'] == ''


# ── inheritance ───────────────────────────────────────────────────────────────

class TestAuthInheritance:

    def test_basic_auth_is_auth_subclass(self):
        assert isinstance(BasicAuth('u', 'p'), Auth)

    def test_bearer_token_is_auth_subclass(self):
        assert isinstance(BearerToken('t'), Auth)

    def test_api_key_is_auth_subclass(self):
        assert isinstance(APIKey(), Auth)
