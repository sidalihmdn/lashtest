"""Unit tests for lashtest.core.request.Request"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from datetime import timedelta
from lashtest.core.request import Request
from lashtest.core.exceptions import MaxRetriesExceededError
from lashtest.http.auth import BearerToken


# ── helpers ───────────────────────────────────────────────────────────────────

def make_mock_client(status_code=200):
    """Return a mock APIClient whose _send_request returns a mock Response."""
    raw = MagicMock()
    raw.status_code = status_code
    raw.headers = {'Content-Type': 'application/json'}
    raw.elapsed = timedelta(seconds=0.1)
    raw.cookies = {}
    raw.json.return_value = {}

    from lashtest.core.response import Response
    mock_response = Response(raw)

    client = MagicMock()
    client.timeout = 30
    client._send_request.return_value = mock_response
    return client


def make_request(method='GET', endpoint='/users', status_code=200) -> Request:
    return Request(make_mock_client(status_code), method, endpoint)


# ── initialization ────────────────────────────────────────────────────────────

class TestRequestInit:

    def test_method_stored(self):
        r = make_request(method='POST')
        assert r.method == 'POST'

    def test_endpoint_stored(self):
        r = make_request(endpoint='/items')
        assert r.endpoint == '/items'

    def test_default_headers_empty(self):
        assert make_request().headers == {}

    def test_default_params_empty(self):
        assert make_request().params == {}

    def test_default_body_none(self):
        assert make_request().body is None

    def test_default_data_none(self):
        assert make_request().data is None

    def test_default_retry_config_none(self):
        assert make_request()._retry_config is None

    def test_default_files_empty(self):
        assert make_request().files == {}


# ── with_header ───────────────────────────────────────────────────────────────

class TestWithHeader:

    def test_adds_header(self):
        r = make_request().with_header('X-Key', 'value')
        assert r.headers['X-Key'] == 'value'

    def test_returns_self(self):
        r = make_request()
        assert r.with_header('X-Key', 'v') is r


# ── with_param / with_params ──────────────────────────────────────────────────

class TestWithParams:

    def test_adds_single_param(self):
        r = make_request().with_param('page', '1')
        assert r.params['page'] == '1'

    def test_adds_multiple_params(self):
        r = make_request().with_params({'page': '1', 'limit': '10'})
        assert r.params['page'] == '1'
        assert r.params['limit'] == '10'

    def test_with_params_returns_self(self):
        r = make_request()
        assert r.with_params({'a': '1'}) is r


# ── with_body / with_json ─────────────────────────────────────────────────────

class TestWithBody:

    def test_sets_body(self):
        r = make_request().with_body({'key': 'value'})
        assert r.body == {'key': 'value'}

    def test_with_json_sets_body_and_content_type(self):
        r = make_request().with_json({'key': 'value'})
        assert r.body == {'key': 'value'}
        assert r.headers['Content-Type'] == 'application/json'

    def test_with_body_returns_self(self):
        r = make_request()
        assert r.with_body({}) is r

    def test_with_json_returns_self(self):
        r = make_request()
        assert r.with_json({}) is r


# ── with_auth ─────────────────────────────────────────────────────────────────

class TestWithAuth:

    def test_sets_auth(self):
        auth = BearerToken('token')
        r = make_request().with_auth(auth)
        assert r.auth is auth

    def test_returns_self(self):
        r = make_request()
        assert r.with_auth(BearerToken('t')) is r


# ── with_timeout ──────────────────────────────────────────────────────────────

class TestWithTimeout:

    def test_sets_timeout(self):
        r = make_request().with_timeout(10.0)
        assert r.timeout == 10.0

    def test_returns_self(self):
        r = make_request()
        assert r.with_timeout(5.0) is r


# ── with_data ─────────────────────────────────────────────────────────────────

class TestWithData:

    def test_sets_data(self):
        r = make_request().with_data({'field': 'value'})
        assert r.data == {'field': 'value'}

    def test_returns_self(self):
        r = make_request()
        assert r.with_data({}) is r


# ── with_file ─────────────────────────────────────────────────────────────────

class TestWithFile:

    def test_opens_file_handle(self, tmp_path):
        f = tmp_path / 'test.txt'
        f.write_text('content')
        r = make_request().with_file('file', str(f))
        assert 'file' in r.files
        r._open_handles[0].close()

    def test_tracks_open_handle(self, tmp_path):
        f = tmp_path / 'test.txt'
        f.write_text('content')
        r = make_request().with_file('file', str(f))
        assert len(r._open_handles) == 1
        r._open_handles[0].close()

    def test_multiple_files(self, tmp_path):
        f1 = tmp_path / 'a.txt'
        f2 = tmp_path / 'b.txt'
        f1.write_text('a')
        f2.write_text('b')
        r = make_request().with_file('file1', str(f1)).with_file('file2', str(f2))
        assert len(r.files) == 2
        assert len(r._open_handles) == 2
        for h in r._open_handles:
            h.close()

    def test_returns_self(self, tmp_path):
        f = tmp_path / 'test.txt'
        f.write_text('content')
        r = make_request()
        result = r.with_file('file', str(f))
        assert result is r
        r._open_handles[0].close()


# ── with_retry ────────────────────────────────────────────────────────────────

class TestWithRetry:

    def test_sets_max_attempts(self):
        r = make_request().with_retry(3)
        assert r._retry_config['max_attempts'] == 3

    def test_default_on_status(self):
        r = make_request().with_retry(3)
        assert r._retry_config['on_status'] == [500, 502, 503, 504]

    def test_custom_on_status(self):
        r = make_request().with_retry(3, on_status=[429, 503])
        assert r._retry_config['on_status'] == [429, 503]

    def test_default_raise_on_exhausted_is_false(self):
        r = make_request().with_retry(3)
        assert r._retry_config['raise_on_exhausted'] is False

    def test_raise_on_exhausted_can_be_set(self):
        r = make_request().with_retry(3, raise_on_exhausted=True)
        assert r._retry_config['raise_on_exhausted'] is True

    def test_returns_self(self):
        r = make_request()
        assert r.with_retry(3) is r


# ── _execute / retry logic ────────────────────────────────────────────────────

class TestExecuteRetry:

    def test_no_retry_when_status_not_in_list(self):
        client = make_mock_client(status_code=200)
        r = Request(client, 'GET', '/users')
        r.with_retry(3, on_status=[500])
        r._execute()
        assert client._send_request.call_count == 1

    @patch('time.sleep')
    def test_retries_on_matching_status(self, mock_sleep):
        from lashtest.core.response import Response
        from datetime import timedelta

        raw_fail = MagicMock()
        raw_fail.status_code = 500
        raw_fail.headers = {}
        raw_fail.elapsed = timedelta(seconds=0.1)
        raw_fail.cookies = {}
        raw_fail.json.return_value = {}

        raw_ok = MagicMock()
        raw_ok.status_code = 200
        raw_ok.headers = {}
        raw_ok.elapsed = timedelta(seconds=0.1)
        raw_ok.cookies = {}
        raw_ok.json.return_value = {}

        client = MagicMock()
        client.timeout = 30
        client._send_request.side_effect = [Response(raw_fail), Response(raw_ok)]

        r = Request(client, 'GET', '/users')
        r.with_retry(3, on_status=[500])
        response = r._execute()

        assert client._send_request.call_count == 2
        assert response.status_code == 200

    @patch('time.sleep')
    def test_raises_max_retries_when_exhausted_and_flag_set(self, mock_sleep):
        from lashtest.core.response import Response
        from datetime import timedelta

        raw_fail = MagicMock()
        raw_fail.status_code = 500
        raw_fail.headers = {}
        raw_fail.elapsed = timedelta(seconds=0.1)
        raw_fail.cookies = {}
        raw_fail.json.return_value = {}

        client = MagicMock()
        client.timeout = 30
        client._send_request.return_value = Response(raw_fail)

        r = Request(client, 'GET', '/users')
        r.with_retry(2, on_status=[500], raise_on_exhausted=True)

        with pytest.raises(MaxRetriesExceededError):
            r._execute()

    @patch('time.sleep')
    def test_returns_last_response_when_exhausted_without_raise(self, mock_sleep):
        from lashtest.core.response import Response
        from datetime import timedelta

        raw_fail = MagicMock()
        raw_fail.status_code = 503
        raw_fail.headers = {}
        raw_fail.elapsed = timedelta(seconds=0.1)
        raw_fail.cookies = {}
        raw_fail.json.return_value = {}

        client = MagicMock()
        client.timeout = 30
        client._send_request.return_value = Response(raw_fail)

        r = Request(client, 'GET', '/users')
        r.with_retry(2, on_status=[503], raise_on_exhausted=False)
        response = r._execute()

        assert response.status_code == 503


# ── context manager ───────────────────────────────────────────────────────────

class TestContextManager:

    def test_enter_returns_response(self):
        from lashtest.core.response import Response
        r = make_request()
        with r as response:
            assert isinstance(response, Response)

    def test_exit_closes_file_handles(self, tmp_path):
        f = tmp_path / 'test.txt'
        f.write_text('content')
        r = make_request().with_file('file', str(f))
        handle = r._open_handles[0]
        with r:
            pass
        assert handle.closed

    def test_exit_clears_open_handles_list(self, tmp_path):
        f = tmp_path / 'test.txt'
        f.write_text('content')
        r = make_request().with_file('file', str(f))
        with r:
            pass
        assert r._open_handles == []


# ── send() ────────────────────────────────────────────────────────────────────

class TestSend:

    def test_send_returns_response(self):
        from lashtest.core.response import Response
        r = make_request()
        response = r.send()
        assert isinstance(response, Response)
