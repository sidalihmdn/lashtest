"""Unit tests for OpenAPI integration."""

import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import timedelta
from lashtest.openapi import OpenAPIValidator
from lashtest.core.response import Response


MINIMAL_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Test API", "version": "1.0.0"},
    "paths": {
        "/users/{id}": {
            "parameters": [
                {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
            ],
            "get": {
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "name": {"type": "string"},
                                    },
                                    "required": ["id", "name"],
                                }
                            }
                        },
                    }
                }
            }
        },
        "/items": {
            "post": {
                "responses": {
                    "201": {
                        "description": "Created",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "properties": {"id": {"type": "integer"}}},
                            }
                        },
                    }
                }
            }
        },
    },
}


def write_spec(tmp_path, spec=None):
    if spec is None:
        spec = MINIMAL_SPEC
    path = tmp_path / "openapi.json"
    path.write_text(json.dumps(spec))
    return path


def make_response(status_code=200, json_data=None):
    raw = MagicMock()
    raw.status_code = status_code
    raw.headers = {"Content-Type": "application/json"}
    raw.elapsed = timedelta(seconds=0.1)
    raw.cookies = {}
    raw.text = json.dumps(json_data or {})
    raw.json.return_value = json_data or {}
    return Response(raw)


# ── loading ───────────────────────────────────────────────────────────────────

class TestOpenAPIValidatorLoading:

    def test_loads_json_spec_from_file(self, tmp_path):
        path = write_spec(tmp_path)
        # openapi-spec-validator may not be installed; skip if missing
        pytest.importorskip("openapi_spec_validator")
        validator = OpenAPIValidator(path)
        assert validator.spec["openapi"] == "3.0.0"

    def test_raises_for_missing_file(self, tmp_path):
        pytest.importorskip("openapi_spec_validator")
        with pytest.raises(FileNotFoundError):
            OpenAPIValidator(tmp_path / "nonexistent.json")

    def test_raises_import_error_without_openapi_spec_validator(self, tmp_path):
        path = write_spec(tmp_path)
        import sys
        original = sys.modules.get("openapi_spec_validator")
        sys.modules["openapi_spec_validator"] = None  # type: ignore
        try:
            with pytest.raises((ImportError, TypeError)):
                OpenAPIValidator(path)
        finally:
            if original is None:
                sys.modules.pop("openapi_spec_validator", None)
            else:
                sys.modules["openapi_spec_validator"] = original


# ── get_response_schema ───────────────────────────────────────────────────────

class TestGetResponseSchema:

    @pytest.fixture
    def validator(self, tmp_path):
        pytest.importorskip("openapi_spec_validator")
        return OpenAPIValidator(write_spec(tmp_path))

    def test_returns_schema_for_existing_path(self, validator):
        schema = validator.get_response_schema("/users/{id}", "GET", 200)
        assert schema is not None
        assert schema["type"] == "object"

    def test_returns_none_for_unknown_path(self, validator):
        schema = validator.get_response_schema("/nonexistent", "GET", 200)
        assert schema is None

    def test_returns_none_for_unknown_method(self, validator):
        schema = validator.get_response_schema("/users/{id}", "DELETE", 200)
        assert schema is None

    def test_returns_none_for_unknown_status(self, validator):
        schema = validator.get_response_schema("/users/{id}", "GET", 404)
        assert schema is None

    def test_case_insensitive_method(self, validator):
        schema_upper = validator.get_response_schema("/users/{id}", "GET", 200)
        schema_lower = validator.get_response_schema("/users/{id}", "get", 200)
        assert schema_upper == schema_lower


# ── assert_response ───────────────────────────────────────────────────────────

class TestAssertResponse:

    @pytest.fixture
    def validator(self, tmp_path):
        pytest.importorskip("openapi_spec_validator")
        return OpenAPIValidator(write_spec(tmp_path))

    def test_passes_for_valid_response(self, validator):
        resp = make_response(200, {"id": 1, "name": "Alice"})
        validator.assert_response("/users/{id}", "GET", 200, resp)

    def test_fails_for_wrong_status_code(self, validator):
        resp = make_response(201, {"id": 1, "name": "Alice"})
        with pytest.raises(AssertionError, match="Expected status 200"):
            validator.assert_response("/users/{id}", "GET", 200, resp)

    def test_fails_for_schema_violation(self, validator):
        resp = make_response(200, {"id": "not-an-int", "name": "Alice"})
        with pytest.raises(AssertionError, match="OpenAPI spec"):
            validator.assert_response("/users/{id}", "GET", 200, resp)

    def test_raises_lookup_error_for_missing_schema(self, validator):
        # Use a path that exists but has no schema for the given status code
        resp = make_response(404, {})
        with pytest.raises(LookupError):
            validator.assert_response("/users/{id}", "GET", 404, resp)

    def test_passes_for_post_201(self, validator):
        resp = make_response(201, {"id": 99})
        validator.assert_response("/items", "POST", 201, resp)


# ── $ref resolution ───────────────────────────────────────────────────────────

class TestRefResolution:

    def test_resolves_component_ref(self, tmp_path):
        pytest.importorskip("openapi_spec_validator")
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "T", "version": "1"},
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
                        "required": ["id", "name"],
                    }
                }
            },
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "OK",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/User"}
                                    }
                                },
                            }
                        }
                    }
                }
            },
        }
        path = tmp_path / "spec.json"
        path.write_text(json.dumps(spec))
        validator = OpenAPIValidator(path)
        resp = make_response(200, {"id": 1, "name": "Bob"})
        validator.assert_response("/users", "GET", 200, resp)
