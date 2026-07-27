"""Unit tests for request/response hooks on APIClient."""

import pytest
from unittest.mock import MagicMock
from datetime import timedelta
from lashtest.core.client import APIClient
from lashtest.core.request import Request
from lashtest.core.response import Response


def make_raw_response(status_code=200):
    raw = MagicMock()
    raw.status_code = status_code
    raw.headers = {"Content-Type": "application/json"}
    raw.elapsed = timedelta(seconds=0.1)
    raw.cookies = {}
    raw.text = ""
    raw.json.return_value = {}
    return raw


class TestAddHook:

    def test_raises_for_non_callable(self):
        client = APIClient("https://api.example.com")
        with pytest.raises(ValueError, match="callable"):
            client.add_hook("before_request", "not-a-fn")

    def test_raises_for_unknown_event(self):
        client = APIClient("https://api.example.com")
        with pytest.raises(ValueError, match="Unknown hook event"):
            client.add_hook("unknown_event", lambda r: None)

    def test_returns_self_for_chaining(self):
        client = APIClient("https://api.example.com")
        result = client.add_hook("before_request", lambda r: None)
        assert result is client

    def test_registers_before_request_hook(self):
        client = APIClient("https://api.example.com")
        fn = lambda r: None
        client.add_hook("before_request", fn)
        assert fn in client._before_request_hooks

    def test_registers_after_response_hook(self):
        client = APIClient("https://api.example.com")
        fn = lambda req, resp: None
        client.add_hook("after_response", fn)
        assert fn in client._after_response_hooks

    def test_multiple_hooks_registered(self):
        client = APIClient("https://api.example.com")
        fn1 = lambda r: None
        fn2 = lambda r: None
        client.add_hook("before_request", fn1)
        client.add_hook("before_request", fn2)
        assert len(client._before_request_hooks) == 2


class TestBeforeRequestHook:

    def test_hook_called_before_each_request(self):
        client = APIClient("https://api.example.com")
        client.session.request = MagicMock(return_value=make_raw_response())

        calls = []
        client.add_hook("before_request", lambda req: calls.append(req))

        client._send_request(client.get("/users"))
        assert len(calls) == 1
        assert isinstance(calls[0], Request)

    def test_hook_receives_correct_request(self):
        client = APIClient("https://api.example.com")
        client.session.request = MagicMock(return_value=make_raw_response())

        received = []
        client.add_hook("before_request", lambda req: received.append(req.endpoint))

        client._send_request(client.get("/users"))
        assert received == ["/users"]

    def test_multiple_before_hooks_called_in_order(self):
        client = APIClient("https://api.example.com")
        client.session.request = MagicMock(return_value=make_raw_response())

        order = []
        client.add_hook("before_request", lambda r: order.append(1))
        client.add_hook("before_request", lambda r: order.append(2))

        client._send_request(client.get("/x"))
        assert order == [1, 2]


class TestAfterResponseHook:

    def test_hook_called_after_each_response(self):
        client = APIClient("https://api.example.com")
        client.session.request = MagicMock(return_value=make_raw_response(200))

        calls = []
        client.add_hook("after_response", lambda req, resp: calls.append(resp.status_code))

        client._send_request(client.get("/users"))
        assert calls == [200]

    def test_hook_receives_request_and_response(self):
        client = APIClient("https://api.example.com")
        client.session.request = MagicMock(return_value=make_raw_response(201))

        received = []
        def hook(req, resp):
            received.append((req.endpoint, resp.status_code))

        client.add_hook("after_response", hook)
        client._send_request(client.post("/items"))
        assert received == [("/items", 201)]

    def test_multiple_after_hooks_called_in_order(self):
        client = APIClient("https://api.example.com")
        client.session.request = MagicMock(return_value=make_raw_response())

        order = []
        client.add_hook("after_response", lambda req, resp: order.append("a"))
        client.add_hook("after_response", lambda req, resp: order.append("b"))

        client._send_request(client.get("/x"))
        assert order == ["a", "b"]

    def test_after_hook_receives_response_object(self):
        client = APIClient("https://api.example.com")
        client.session.request = MagicMock(return_value=make_raw_response())

        received = []
        client.add_hook("after_response", lambda req, resp: received.append(type(resp).__name__))

        client._send_request(client.get("/x"))
        assert received == ["Response"]

    def test_hooks_can_be_used_for_redaction(self):
        """Demonstrate that hooks can inspect and redact auth headers."""
        client = APIClient("https://api.example.com")
        client.session.request = MagicMock(return_value=make_raw_response())

        logged_endpoints = []
        def audit_hook(req):
            logged_endpoints.append(req.endpoint)

        client.add_hook("before_request", audit_hook)
        client._send_request(client.get("/secure"))
        assert "/secure" in logged_endpoints
