"""OpenAPI spec loading and response validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse


class OpenAPIValidator:
    """Loads an OpenAPI 3.x spec and validates responses against it.

    Args:
        spec: Path to an OpenAPI spec file (JSON or YAML) **or** a URL
            pointing to one.

    Requires the optional ``openapi-spec-validator`` package::

        pip install openapi-spec-validator

    Example::

        from lashtest import APIClient
        from lashtest.openapi import OpenAPIValidator

        validator = OpenAPIValidator('openapi.yaml')

        def test_get_user():
            with APIClient('https://api.example.com').get('/users/1') as r:
                validator.assert_response('/users/{id}', 'GET', 200, r)
    """

    def __init__(self, spec: Union[str, Path]) -> None:
        self._spec_dict = self._load(spec)
        self._validate_spec()

    # ── loading ───────────────────────────────────────────────────────────────

    @staticmethod
    def _load(spec: Union[str, Path]) -> Dict[str, Any]:
        spec_str = str(spec)
        parsed = urlparse(spec_str)

        if parsed.scheme in ("http", "https"):
            import requests as _requests
            resp = _requests.get(spec_str)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "yaml" in content_type or spec_str.endswith((".yaml", ".yml")):
                return OpenAPIValidator._parse_yaml(resp.text)
            return resp.json()

        path = Path(spec_str)
        if not path.exists():
            raise FileNotFoundError(f"OpenAPI spec file not found: {path}")
        text = path.read_text(encoding="utf-8")
        if path.suffix in (".yaml", ".yml"):
            return OpenAPIValidator._parse_yaml(text)
        return json.loads(text)

    @staticmethod
    def _parse_yaml(text: str) -> Dict[str, Any]:
        try:
            import yaml  # type: ignore[import-not-found]
            return yaml.safe_load(text)
        except ImportError:
            raise ImportError(
                "PyYAML is required to load YAML spec files. "
                "Install it with: pip install pyyaml"
            )

    def _validate_spec(self) -> None:
        try:
            from openapi_spec_validator import validate  # type: ignore[import-not-found]
            validate(self._spec_dict)
        except ImportError:
            raise ImportError(
                "openapi-spec-validator is required for OpenAPI support. "
                "Install it with: pip install openapi-spec-validator"
            )

    # ── public API ────────────────────────────────────────────────────────────

    @property
    def spec(self) -> Dict[str, Any]:
        """The raw spec dict."""
        return self._spec_dict

    def get_response_schema(
        self, path: str, method: str, status_code: int
    ) -> Optional[Dict[str, Any]]:
        """Return the JSON Schema for the given path/method/status, or ``None``.

        Args:
            path: OpenAPI path pattern, e.g. ``"/users/{id}"``.
            method: HTTP method (case-insensitive), e.g. ``"GET"``.
            status_code: Expected status code.
        """
        paths = self._spec_dict.get("paths", {})
        path_item = paths.get(path)
        if path_item is None:
            return None

        operation = path_item.get(method.lower())
        if operation is None:
            return None

        responses = operation.get("responses", {})
        response_obj = responses.get(str(status_code)) or responses.get("default")
        if response_obj is None:
            return None

        # Resolve $ref if present
        response_obj = self._resolve_ref(response_obj)

        content = response_obj.get("content", {})
        json_media = content.get("application/json") or next(iter(content.values()), None)
        if json_media is None:
            return None

        schema = json_media.get("schema")
        return self._resolve_ref(schema) if schema else None

    def assert_response(
        self,
        path: str,
        method: str,
        status_code: int,
        response: Any,
    ) -> None:
        """Assert that *response* conforms to the OpenAPI spec.

        Args:
            path: OpenAPI path pattern (e.g. ``"/users/{id}"``).
            method: HTTP method (case-insensitive).
            status_code: Expected status code.
            response: A lashtest ``Response`` object.

        Raises:
            AssertionError: If the status code or body schema do not
                match the spec.
            LookupError: If no matching response schema is found in the spec.
        """
        from jsonschema import validate as _validate, ValidationError

        assert response.status_code == status_code, (
            f"Expected status {status_code}, got {response.status_code}"
        )

        schema = self.get_response_schema(path, method, status_code)
        if schema is None:
            raise LookupError(
                f"No response schema found in spec for "
                f"{method.upper()} {path} -> {status_code}"
            )

        try:
            _validate(instance=response.json(), schema=schema)
        except ValidationError as exc:
            raise AssertionError(
                f"Response body does not conform to OpenAPI spec "
                f"({method.upper()} {path} {status_code}): {exc.message}"
            )

    # ── helpers ───────────────────────────────────────────────────────────────

    def _resolve_ref(self, obj: Any) -> Any:
        """Resolve a JSON ``$ref`` pointer within the same document."""
        if not isinstance(obj, dict) or "$ref" not in obj:
            return obj
        ref = obj["$ref"]
        if not ref.startswith("#/"):
            return obj  # external refs not supported
        parts = ref.lstrip("#/").split("/")
        node: Any = self._spec_dict
        for part in parts:
            part = part.replace("~1", "/").replace("~0", "~")
            node = node[part]
        return node
