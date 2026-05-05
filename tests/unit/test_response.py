"""Unit tests for lashtest.core.response.Response"""

import pytest
from datetime import timedelta
from unittest.mock import MagicMock, patch
from lashtest.core.response import Response


# ── helpers ───────────────────────────────────────────────────────────────────

def make_response(
    status_code: int = 200,
    json_data=None,
    text: str = '',
    headers: dict = None,
    cookies: dict = None,
    elapsed: float = 0.1,
) -> Response:
    raw = MagicMock()
    raw.status_code = status_code
    raw.text = text
    raw.headers = headers or {'Content-Type': 'application/json'}
    raw.elapsed = timedelta(seconds=elapsed)
    raw.cookies = cookies or {}
    if json_data is not None:
        raw.json.return_value = json_data
    else:
        raw.json.side_effect = ValueError("No JSON")
    return Response(raw)


# ── properties ────────────────────────────────────────────────────────────────

class TestResponseProperties:

    def test_status_code(self):
        assert make_response(status_code=201).status_code == 201

    def test_status_alias(self):
        assert make_response(status_code=404).status == 404

    def test_ok_true_for_2xx(self):
        for code in [200, 201, 204, 299]:
            assert make_response(status_code=code).ok is True

    def test_ok_false_for_non_2xx(self):
        for code in [100, 301, 400, 404, 500]:
            assert make_response(status_code=code).ok is False

    def test_text_returns_raw_text(self):
        r = make_response(text='hello')
        assert r.text == 'hello'

    def test_elapsed_in_seconds(self):
        r = make_response(elapsed=1.5)
        assert r.elapsed == 1.5

    def test_headers_accessible(self):
        r = make_response(headers={'X-Custom': 'value'})
        assert r.headers['X-Custom'] == 'value'


# ── json() ────────────────────────────────────────────────────────────────────

class TestResponseJson:

    def test_json_returns_parsed_body(self):
        r = make_response(json_data={'key': 'value'})
        assert r.json() == {'key': 'value'}

    def test_json_caches_result(self):
        raw = MagicMock()
        raw.status_code = 200
        raw.headers = {}
        raw.elapsed = timedelta(seconds=0.1)
        raw.cookies = {}
        raw.json.return_value = {'key': 'value'}
        r = Response(raw)
        r.json()
        r.json()
        raw.json.assert_called_once()  # called only once due to cache

    def test_json_raises_value_error_for_invalid_json(self):
        r = make_response()  # json_data=None triggers ValueError
        with pytest.raises(ValueError, match="not valid JSON"):
            r.json()

    def test_json_supports_list_response(self):
        r = make_response(json_data=[1, 2, 3])
        assert r.json() == [1, 2, 3]


# ── assert_status ─────────────────────────────────────────────────────────────

class TestAssertStatus:

    def test_passes_on_exact_match(self):
        make_response(status_code=200).assert_status(200)

    def test_fails_on_mismatch(self):
        with pytest.raises(AssertionError, match="Expected status code 201, got 200"):
            make_response(status_code=200).assert_status(201)

    def test_returns_self_for_chaining(self):
        r = make_response(status_code=200)
        assert r.assert_status(200) is r


# ── assert_ok ─────────────────────────────────────────────────────────────────

class TestAssertOk:

    def test_passes_for_200(self):
        make_response(status_code=200).assert_ok()

    def test_passes_for_201(self):
        make_response(status_code=201).assert_ok()

    def test_fails_for_400(self):
        with pytest.raises(AssertionError):
            make_response(status_code=400).assert_ok()

    def test_fails_for_500(self):
        with pytest.raises(AssertionError):
            make_response(status_code=500).assert_ok()

    def test_returns_self_for_chaining(self):
        r = make_response(status_code=200)
        assert r.assert_ok() is r


# ── assert_header ─────────────────────────────────────────────────────────────

class TestAssertHeader:

    def test_passes_when_header_exists(self):
        make_response(headers={'Content-Type': 'application/json'}).assert_header('Content-Type')

    def test_fails_when_header_missing(self):
        with pytest.raises(AssertionError, match="Expected header 'X-Missing' to be present"):
            make_response(headers={}).assert_header('X-Missing')

    def test_passes_when_value_matches(self):
        make_response(headers={'Content-Type': 'application/json'}) \
            .assert_header('Content-Type', 'application/json')

    def test_fails_when_value_does_not_match(self):
        with pytest.raises(AssertionError):
            make_response(headers={'Content-Type': 'text/html'}) \
                .assert_header('Content-Type', 'application/json')

    def test_returns_self_for_chaining(self):
        r = make_response(headers={'X-Header': 'val'})
        assert r.assert_header('X-Header') is r


# ── assert_json ───────────────────────────────────────────────────────────────

class TestAssertJson:

    def test_passes_on_exact_match(self):
        make_response(json_data={'a': 1}).assert_json({'a': 1})

    def test_fails_on_mismatch(self):
        with pytest.raises(AssertionError):
            make_response(json_data={'a': 1}).assert_json({'a': 2})

    def test_returns_self_for_chaining(self):
        r = make_response(json_data={'a': 1})
        assert r.assert_json({'a': 1}) is r


# ── assert_json_contains ──────────────────────────────────────────────────────

class TestAssertJsonContains:

    def test_passes_when_subset_present(self):
        make_response(json_data={'a': 1, 'b': 2}).assert_json_contains({'a': 1})

    def test_fails_when_key_missing(self):
        with pytest.raises(AssertionError, match="Expected key 'c'"):
            make_response(json_data={'a': 1}).assert_json_contains({'c': 3})

    def test_fails_when_value_mismatch(self):
        with pytest.raises(AssertionError):
            make_response(json_data={'a': 1}).assert_json_contains({'a': 99})

    def test_fails_when_body_is_not_dict(self):
        with pytest.raises(AssertionError, match="dictionary"):
            make_response(json_data=[1, 2, 3]).assert_json_contains({'a': 1})

    def test_returns_self_for_chaining(self):
        r = make_response(json_data={'a': 1})
        assert r.assert_json_contains({'a': 1}) is r


# ── assert_json_schema ────────────────────────────────────────────────────────

class TestAssertJsonSchema:

    def test_passes_for_valid_schema(self):
        schema = {
            'type': 'object',
            'properties': {'name': {'type': 'string'}},
            'required': ['name'],
        }
        make_response(json_data={'name': 'John'}).assert_json_schema(schema)

    def test_fails_for_invalid_schema(self):
        schema = {
            'type': 'object',
            'properties': {'age': {'type': 'integer'}},
            'required': ['age'],
        }
        with pytest.raises(AssertionError, match="schema validation failed"):
            make_response(json_data={'name': 'John'}).assert_json_schema(schema)

    def test_returns_self_for_chaining(self):
        schema = {'type': 'object'}
        r = make_response(json_data={'a': 1})
        assert r.assert_json_schema(schema) is r


# ── assert_response_time ──────────────────────────────────────────────────────

class TestAssertResponseTime:

    def test_passes_when_under_limit(self):
        make_response(elapsed=0.5).assert_response_time(1.0)

    def test_fails_when_over_limit(self):
        with pytest.raises(AssertionError, match="Expected response time"):
            make_response(elapsed=2.0).assert_response_time(1.0)

    def test_returns_self_for_chaining(self):
        r = make_response(elapsed=0.1)
        assert r.assert_response_time(1.0) is r


# ── assert_json_path ──────────────────────────────────────────────────────────

class TestAssertJsonPath:

    def test_passes_when_path_matches(self):
        make_response(json_data={'user': {'name': 'John'}}) \
            .assert_json_path('$.user.name', 'John')

    def test_fails_when_path_not_found(self):
        with pytest.raises(AssertionError, match="No matches found"):
            make_response(json_data={'user': {}}).assert_json_path('$.user.missing', 'x')

    def test_fails_when_value_does_not_match(self):
        with pytest.raises(AssertionError):
            make_response(json_data={'a': 1}).assert_json_path('$.a', 99)

    def test_returns_self_for_chaining(self):
        r = make_response(json_data={'a': 1})
        assert r.assert_json_path('$.a', 1) is r


# ── assert_json_path_type ─────────────────────────────────────────────────────

class TestAssertJsonPathType:

    def test_passes_for_correct_type(self):
        make_response(json_data={'id': 1}).assert_json_path_type('$.id', int)

    def test_fails_for_wrong_type(self):
        with pytest.raises(AssertionError, match="type"):
            make_response(json_data={'id': '1'}).assert_json_path_type('$.id', int)

    def test_returns_self_for_chaining(self):
        r = make_response(json_data={'id': 1})
        assert r.assert_json_path_type('$.id', int) is r


# ── assert_json_path_exists ───────────────────────────────────────────────────

class TestAssertJsonPathExists:

    def test_passes_when_path_exists(self):
        make_response(json_data={'a': {'b': 1}}).assert_json_path_exists('$.a.b')

    def test_fails_when_path_missing(self):
        with pytest.raises(AssertionError, match="No matches found"):
            make_response(json_data={'a': {}}).assert_json_path_exists('$.a.missing')

    def test_returns_self_for_chaining(self):
        r = make_response(json_data={'a': 1})
        assert r.assert_json_path_exists('$.a') is r


# ── assert_cookie_exists ──────────────────────────────────────────────────────

class TestAssertCookieExists:

    def test_passes_when_cookie_present(self):
        make_response(cookies={'session': 'abc123'}).assert_cookie_exists('session')

    def test_fails_when_cookie_missing(self):
        with pytest.raises(AssertionError, match="Expected cookie 'missing'"):
            make_response(cookies={}).assert_cookie_exists('missing')

    def test_returns_self_for_chaining(self):
        r = make_response(cookies={'token': 'xyz'})
        assert r.assert_cookie_exists('token') is r


# ── assert_cookie_value ───────────────────────────────────────────────────────

class TestAssertCookieValue:

    def test_passes_when_value_matches(self):
        make_response(cookies={'token': 'abc'}).assert_cookie_value('token', 'abc')

    def test_fails_when_value_mismatch(self):
        with pytest.raises(AssertionError):
            make_response(cookies={'token': 'abc'}).assert_cookie_value('token', 'wrong')

    def test_fails_when_cookie_missing(self):
        with pytest.raises(AssertionError):
            make_response(cookies={}).assert_cookie_value('missing', 'value')

    def test_returns_self_for_chaining(self):
        r = make_response(cookies={'k': 'v'})
        assert r.assert_cookie_value('k', 'v') is r


# ── chaining ──────────────────────────────────────────────────────────────────

class TestChaining:

    def test_multiple_assertions_chained(self):
        make_response(
            status_code=200,
            json_data={'id': 1, 'name': 'John'},
            headers={'Content-Type': 'application/json'},
            elapsed=0.1,
        ).assert_status(200) \
         .assert_ok() \
         .assert_header('Content-Type') \
         .assert_json_contains({'id': 1}) \
         .assert_response_time(1.0)
