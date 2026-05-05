"""Unit tests for lashtest.core.client.APIClient"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import timedelta
from lashtest.core.client import APIClient
from lashtest.core.exceptions import InvalidURL, APITimeoutError, APIConnectionError
from lashtest.http.auth import BearerToken, BasicAuth


# ── helpers ───────────────────────────────────────────────────────────────────

def make_mock_raw_response(status_code=200, json_data=None, elapsed=0.1):
    raw = MagicMock()
    raw.status_code = status_code
    raw.headers = {'Content-Type': 'application/json'}
    raw.elapsed = timedelta(seconds=elapsed)
    raw.cookies = {}
    raw.text = ''
    raw.json.return_value = json_data or {}
    return raw


# ── initialization ────────────────────────────────────────────────────────────

class TestAPIClientInit:

    def test_base_url_strips_trailing_slash(self):
        client = APIClient('https://api.example.com/')
        assert client.base_url == 'https://api.example.com'

    def test_default_timeout_is_30(self):
        client = APIClient('https://api.example.com')
        assert client.timeout == 30

    def test_default_headers_are_empty(self):
        client = APIClient('https://api.example.com')
        assert client.headers == {}

    def test_default_auth_is_none(self):
        client = APIClient('https://api.example.com')
        assert client.auth is None

    def test_default_base_path_is_none(self):
        client = APIClient('https://api.example.com')
        assert client.base_path is None

    def test_ssl_verify_is_set(self):
        client = APIClient('https://api.example.com')
        assert client.verify_ssl is not False  # must be truthy (path or True)


# ── with_header ───────────────────────────────────────────────────────────────

class TestWithHeader:

    def test_adds_single_header(self):
        client = APIClient('https://api.example.com').with_header('X-Key', 'value')
        assert client.headers['X-Key'] == 'value'

    def test_returns_self_for_chaining(self):
        client = APIClient('https://api.example.com')
        assert client.with_header('X-Key', 'val') is client

    def test_raises_for_non_string_key(self):
        with pytest.raises(ValueError):
            APIClient('https://api.example.com').with_header(123, 'value')

    def test_raises_for_non_string_value(self):
        with pytest.raises(ValueError):
            APIClient('https://api.example.com').with_header('key', 123)


# ── with_headers ──────────────────────────────────────────────────────────────

class TestWithHeaders:

    def test_adds_multiple_headers(self):
        client = APIClient('https://api.example.com').with_headers({
            'X-A': '1', 'X-B': '2'
        })
        assert client.headers['X-A'] == '1'
        assert client.headers['X-B'] == '2'

    def test_raises_for_non_dict(self):
        with pytest.raises(ValueError):
            APIClient('https://api.example.com').with_headers('not-a-dict')

    def test_returns_self_for_chaining(self):
        client = APIClient('https://api.example.com')
        assert client.with_headers({'X-A': '1'}) is client


# ── with_auth ─────────────────────────────────────────────────────────────────

class TestWithAuth:

    def test_sets_auth(self):
        auth = BearerToken('token')
        client = APIClient('https://api.example.com').with_auth(auth)
        assert client.auth is auth

    def test_raises_for_invalid_auth(self):
        with pytest.raises(ValueError):
            APIClient('https://api.example.com').with_auth('not-an-auth')

    def test_returns_self_for_chaining(self):
        client = APIClient('https://api.example.com')
        assert client.with_auth(BearerToken('t')) is client


# ── with_timeout ──────────────────────────────────────────────────────────────

class TestWithTimeout:

    def test_sets_timeout(self):
        client = APIClient('https://api.example.com').with_timeout(10)
        assert client.timeout == 10

    def test_raises_for_zero(self):
        with pytest.raises(ValueError):
            APIClient('https://api.example.com').with_timeout(0)

    def test_raises_for_negative(self):
        with pytest.raises(ValueError):
            APIClient('https://api.example.com').with_timeout(-5)

    def test_returns_self_for_chaining(self):
        client = APIClient('https://api.example.com')
        assert client.with_timeout(5) is client


# ── with_base_path ────────────────────────────────────────────────────────────

class TestWithBasePath:

    def test_sets_base_path(self):
        client = APIClient('https://api.example.com').with_base_path('/api/v1')
        assert client.base_path == '/api/v1'

    def test_returns_self_for_chaining(self):
        client = APIClient('https://api.example.com')
        assert client.with_base_path('/api/v1') is client


# ── with_cookies ──────────────────────────────────────────────────────────────

class TestWithCookies:

    def test_sets_cookies(self):
        client = APIClient('https://api.example.com').with_cookies({'session': 'abc'})
        assert client.session.cookies.get('session') == 'abc'

    def test_raises_for_non_dict(self):
        with pytest.raises(ValueError):
            APIClient('https://api.example.com').with_cookies('not-a-dict')

    def test_returns_self_for_chaining(self):
        client = APIClient('https://api.example.com')
        assert client.with_cookies({'k': 'v'}) is client


# ── clear_cookies ─────────────────────────────────────────────────────────────

class TestClearCookies:

    def test_clears_cookies(self):
        client = APIClient('https://api.example.com').with_cookies({'session': 'abc'})
        client.clear_cookies()
        assert 'session' not in client.session.cookies

    def test_returns_self_for_chaining(self):
        client = APIClient('https://api.example.com')
        assert client.clear_cookies() is client


# ── HTTP verb methods ─────────────────────────────────────────────────────────

class TestHttpVerbMethods:

    @pytest.fixture
    def client(self):
        return APIClient('https://api.example.com')

    def test_get_returns_request(self, client):
        from lashtest.core.request import Request
        assert isinstance(client.get('/users'), Request)

    def test_post_returns_request(self, client):
        from lashtest.core.request import Request
        assert isinstance(client.post('/users'), Request)

    def test_put_returns_request(self, client):
        from lashtest.core.request import Request
        assert isinstance(client.put('/users/1'), Request)

    def test_patch_returns_request(self, client):
        from lashtest.core.request import Request
        assert isinstance(client.patch('/users/1'), Request)

    def test_delete_returns_request(self, client):
        from lashtest.core.request import Request
        assert isinstance(client.delete('/users/1'), Request)

    def test_request_has_correct_method(self, client):
        assert client.get('/users').method == 'GET'
        assert client.post('/users').method == 'POST'
        assert client.put('/users/1').method == 'PUT'
        assert client.patch('/users/1').method == 'PATCH'
        assert client.delete('/users/1').method == 'DELETE'

    def test_request_has_correct_endpoint(self, client):
        assert client.get('/users').endpoint == '/users'


# ── _validate_endpoint ────────────────────────────────────────────────────────

class TestValidateEndpoint:

    def test_valid_endpoint_passes(self):
        APIClient('https://api.example.com')._validate_endpoint('/users')

    def test_missing_leading_slash_raises(self):
        with pytest.raises(InvalidURL):
            APIClient('https://api.example.com')._validate_endpoint('users')

    def test_non_string_raises(self):
        with pytest.raises(InvalidURL):
            APIClient('https://api.example.com')._validate_endpoint(123)


# ── _send_request ─────────────────────────────────────────────────────────────

class TestSendRequest:

    @pytest.fixture
    def client(self):
        return APIClient('https://api.example.com')

    def test_builds_correct_url(self, client):
        client.session.request = MagicMock(return_value=make_mock_raw_response())
        request = client.get('/users')
        client._send_request(request)
        call_kwargs = client.session.request.call_args
        assert 'https://api.example.com/users' in call_kwargs[1]['url'] \
            or 'https://api.example.com/users' == call_kwargs[0][1] \
            or client.session.request.call_args.kwargs.get('url') == 'https://api.example.com/users'

    def test_merges_client_and_request_headers(self, client):
        client.session.request = MagicMock(return_value=make_mock_raw_response())
        client.with_header('X-Client', 'client-val')
        request = client.get('/users').with_header('X-Request', 'request-val')
        client._send_request(request)
        sent_headers = client.session.request.call_args.kwargs.get('headers', {})
        assert sent_headers.get('X-Client') == 'client-val'
        assert sent_headers.get('X-Request') == 'request-val'

    def test_applies_client_level_auth(self, client):
        client.session.request = MagicMock(return_value=make_mock_raw_response())
        client.with_auth(BearerToken('my-token'))
        request = client.get('/users')
        client._send_request(request)
        sent_headers = client.session.request.call_args.kwargs.get('headers', {})
        assert sent_headers.get('Authorization') == 'Bearer my-token'

    def test_request_auth_overrides_client_auth(self, client):
        client.session.request = MagicMock(return_value=make_mock_raw_response())
        client.with_auth(BearerToken('client-token'))
        request = client.get('/users').with_auth(BearerToken('request-token'))
        client._send_request(request)
        sent_headers = client.session.request.call_args.kwargs.get('headers', {})
        assert sent_headers.get('Authorization') == 'Bearer request-token'

    def test_base_path_included_in_url(self, client):
        client.session.request = MagicMock(return_value=make_mock_raw_response())
        client.with_base_path('/api/v1')
        request = client.get('/users')
        client._send_request(request)
        url = client.session.request.call_args.kwargs.get('url', '')
        assert '/api/v1/users' in url

    def test_raises_api_timeout_error_on_timeout(self, client):
        import requests as req
        client.session.request = MagicMock(side_effect=req.exceptions.Timeout())
        with pytest.raises(APITimeoutError):
            client._send_request(client.get('/users'))

    def test_raises_api_connection_error_on_connection_failure(self, client):
        import requests as req
        client.session.request = MagicMock(side_effect=req.exceptions.ConnectionError())
        with pytest.raises(APIConnectionError):
            client._send_request(client.get('/users'))

    def test_raises_invalid_url_on_bad_url(self, client):
        import requests as req
        client.session.request = MagicMock(side_effect=req.exceptions.InvalidURL())
        with pytest.raises(InvalidURL):
            client._send_request(client.get('/users'))


# ── context manager ───────────────────────────────────────────────────────────

class TestContextManager:

    def test_returns_self_on_enter(self):
        client = APIClient('https://api.example.com')
        with client as c:
            assert c is client

    def test_closes_session_on_exit(self):
        client = APIClient('https://api.example.com')
        client.session.close = MagicMock()
        with client:
            pass
        client.session.close.assert_called_once()
