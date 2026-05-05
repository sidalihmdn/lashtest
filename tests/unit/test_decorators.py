"""Unit tests for lashtest.decorators"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import timedelta
from lashtest.decorators import authenticated, title
from lashtest.http.auth import BearerToken, BasicAuth, APIKey
from lashtest.core.client import APIClient


# ── helpers ───────────────────────────────────────────────────────────────────

def make_mock_client():
    """Return a mock APIClient."""
    raw = MagicMock()
    raw.status_code = 200
    raw.headers = {}
    raw.elapsed = timedelta(seconds=0.1)
    raw.cookies = {}
    raw.json.return_value = {}

    from lashtest.core.response import Response
    mock_response = Response(raw)

    client = MagicMock(spec=APIClient)
    client.timeout = 30
    client._send_request.return_value = mock_response

    mock_request = MagicMock()
    mock_request.__enter__ = MagicMock(return_value=mock_response)
    mock_request.__exit__ = MagicMock(return_value=False)
    mock_request.with_auth = MagicMock(return_value=mock_request)

    client.get.return_value = mock_request
    client.post.return_value = mock_request

    # with_auth must return a DIFFERENT object so identity checks work correctly
    authenticated_client = MagicMock(spec=APIClient)
    authenticated_client.timeout = 30
    authenticated_client.get.return_value = mock_request
    authenticated_client.post.return_value = mock_request
    client.with_auth = MagicMock(return_value=authenticated_client)

    return client


# ── @authenticated on methods ─────────────────────────────────────────────────

class TestAuthenticatedOnMethod:

    def test_replaces_client_with_authenticated_version(self):
        auth = BearerToken('token')
        replaced = []

        class MyTest:
            client = make_mock_client()

            @authenticated(auth)
            def test_something(self):
                replaced.append(self.client)

        t = MyTest()
        original = t.client
        t.test_something()
        assert replaced[0] is not original

    def test_restores_original_client_after_test(self):
        auth = BearerToken('token')

        class MyTest:
            client = make_mock_client()

            @authenticated(auth)
            def test_something(self):
                pass

        t = MyTest()
        original = t.client
        t.test_something()
        assert t.client is original

    def test_restores_client_even_if_test_raises(self):
        auth = BearerToken('token')

        class MyTest:
            client = make_mock_client()

            @authenticated(auth)
            def test_something(self):
                raise AssertionError("test failed")

        t = MyTest()
        original = t.client
        with pytest.raises(AssertionError):
            t.test_something()
        assert t.client is original

    def test_preserves_function_name(self):
        auth = BearerToken('token')

        class MyTest:
            client = make_mock_client()

            @authenticated(auth)
            def test_something(self):
                pass

        assert MyTest.test_something.__name__ == 'test_something'


# ── @authenticated on classes ─────────────────────────────────────────────────

class TestAuthenticatedOnClass:

    def test_wraps_all_test_methods(self):
        auth = BearerToken('token')
        calls = []

        @authenticated(auth)
        class MyTestClass:
            client = make_mock_client()

            def test_one(self):
                calls.append('one')

            def test_two(self):
                calls.append('two')

            def helper_method(self):
                calls.append('helper')  # should NOT be wrapped

        t = MyTestClass()
        t.test_one()
        t.test_two()
        assert 'one' in calls
        assert 'two' in calls

    def test_does_not_wrap_non_test_methods(self):
        auth = BearerToken('token')
        client_seen = []

        @authenticated(auth)
        class MyTestClass:
            client = make_mock_client()

            def test_something(self):
                pass

            def setup(self):
                # capture what self.client looks like when setup() runs
                client_seen.append(self.client)

        t = MyTestClass()
        original = t.client
        t.setup()
        # setup is NOT wrapped — self.client must still be the original inside it
        assert client_seen[0] is original

    def test_returns_original_class(self):
        auth = BearerToken('token')

        @authenticated(auth)
        class MyTestClass:
            client = make_mock_client()

            def test_something(self):
                pass

        assert isinstance(MyTestClass, type)

    def test_restores_client_after_each_method(self):
        auth = BearerToken('token')

        @authenticated(auth)
        class MyTestClass:
            client = make_mock_client()

            def test_one(self):
                pass

            def test_two(self):
                pass

        t = MyTestClass()
        original = t.client
        t.test_one()
        assert t.client is original
        t.test_two()
        assert t.client is original


# ── @title ────────────────────────────────────────────────────────────────────

class TestTitle:

    @patch('allure.title')
    def test_calls_allure_title(self, mock_allure_title):
        mock_allure_title.return_value = lambda f: f

        @title("My test title")
        def test_something():
            pass

        mock_allure_title.assert_called_once_with("My test title")

    @patch('allure.title')
    def test_preserves_function(self, mock_allure_title):
        original = lambda: None
        mock_allure_title.return_value = lambda f: f

        result = title("title")(original)
        assert result is original
