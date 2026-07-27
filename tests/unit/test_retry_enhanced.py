"""Unit tests for the enhanced retry policy."""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import timedelta
from lashtest.core.request import Request
from lashtest.core.response import Response
from lashtest.core.exceptions import MaxRetriesExceededError, APIConnectionError, APITimeoutError


def make_raw(status_code):
    raw = MagicMock()
    raw.status_code = status_code
    raw.headers = {}
    raw.elapsed = timedelta(seconds=0.1)
    raw.cookies = {}
    raw.json.return_value = {}
    return raw


def make_client(*status_codes):
    """Return a mock client that yields the given status codes in sequence."""
    client = MagicMock()
    client.timeout = 30
    client._send_request.side_effect = [Response(make_raw(s)) for s in status_codes]
    return client


class TestBackoffFactor:

    @patch("time.sleep")
    def test_custom_backoff_factor_applied(self, mock_sleep):
        client = make_client(500, 200)
        r = Request(client, "GET", "/x")
        r.with_retry(3, on_status=[500], backoff_factor=2.0)
        r._execute()
        # attempt 1 failed (status 500) → sleep(2.0 * 2^0 = 2.0)
        mock_sleep.assert_called_once_with(pytest.approx(2.0, abs=1.1))

    @patch("time.sleep")
    def test_max_backoff_caps_delay(self, mock_sleep):
        client = make_client(500, 500, 200)
        r = Request(client, "GET", "/x")
        r.with_retry(4, on_status=[500], backoff_factor=100.0, max_backoff=5.0)
        r._execute()
        for call_args in mock_sleep.call_args_list:
            assert call_args[0][0] <= 5.0 + 1.1  # +1.1 for possible jitter headroom


class TestJitter:

    @patch("time.sleep")
    def test_jitter_adds_random_component(self, mock_sleep):
        import random
        random.seed(42)
        client = make_client(500, 200)
        r = Request(client, "GET", "/x")
        r.with_retry(3, on_status=[500], backoff_factor=1.0, jitter=True)
        r._execute()
        # Delay should be 1.0 + random(), i.e. between 1.0 and 2.0
        delay = mock_sleep.call_args[0][0]
        assert 1.0 <= delay <= 2.0

    @patch("time.sleep")
    def test_no_jitter_is_deterministic(self, mock_sleep):
        client = make_client(500, 200)
        r = Request(client, "GET", "/x")
        r.with_retry(3, on_status=[500], backoff_factor=1.0, jitter=False)
        r._execute()
        assert mock_sleep.call_args[0][0] == pytest.approx(1.0)


class TestRetryOnExceptions:

    @patch("time.sleep")
    def test_retries_on_connection_error_when_flag_set(self, mock_sleep):
        client = MagicMock()
        client.timeout = 30
        ok_resp = Response(make_raw(200))
        client._send_request.side_effect = [
            APIConnectionError("refused"),
            ok_resp,
        ]
        r = Request(client, "GET", "/x")
        r.with_retry(3, retry_on_exceptions=True)
        result = r._execute()
        assert result.status_code == 200
        assert client._send_request.call_count == 2

    @patch("time.sleep")
    def test_retries_on_timeout_error_when_flag_set(self, mock_sleep):
        client = MagicMock()
        client.timeout = 30
        ok_resp = Response(make_raw(200))
        client._send_request.side_effect = [
            APITimeoutError(30),
            ok_resp,
        ]
        r = Request(client, "GET", "/x")
        r.with_retry(3, retry_on_exceptions=True)
        result = r._execute()
        assert result.status_code == 200

    def test_connection_error_propagates_when_flag_not_set(self):
        client = MagicMock()
        client.timeout = 30
        client._send_request.side_effect = APIConnectionError("refused")
        r = Request(client, "GET", "/x")
        r.with_retry(3, retry_on_exceptions=False)
        with pytest.raises(APIConnectionError):
            r._execute()

    @patch("time.sleep")
    def test_raises_last_exception_when_all_attempts_fail(self, mock_sleep):
        client = MagicMock()
        client.timeout = 30
        client._send_request.side_effect = APIConnectionError("refused")
        r = Request(client, "GET", "/x")
        r.with_retry(2, retry_on_exceptions=True)
        with pytest.raises(APIConnectionError):
            r._execute()


class TestWithRetryDefaults:

    def test_backoff_factor_defaults_to_one(self):
        r = Request(MagicMock(timeout=30), "GET", "/x")
        r.with_retry(3)
        assert r._retry_config["backoff_factor"] == 1.0

    def test_max_backoff_defaults_to_sixty(self):
        r = Request(MagicMock(timeout=30), "GET", "/x")
        r.with_retry(3)
        assert r._retry_config["max_backoff"] == 60.0

    def test_jitter_defaults_to_false(self):
        r = Request(MagicMock(timeout=30), "GET", "/x")
        r.with_retry(3)
        assert r._retry_config["jitter"] is False

    def test_retry_on_exceptions_defaults_to_false(self):
        r = Request(MagicMock(timeout=30), "GET", "/x")
        r.with_retry(3)
        assert r._retry_config["retry_on_exceptions"] is False

    def test_returns_self_for_chaining(self):
        r = Request(MagicMock(timeout=30), "GET", "/x")
        assert r.with_retry(3, backoff_factor=2.0, max_backoff=30.0, jitter=True) is r
