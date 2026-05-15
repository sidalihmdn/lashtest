from typing import Any, Dict, Optional
from jsonpath_ng import parse
import requests
from ..assertions.facade import AssertionsFacade

class Response:
    """A class representing an API response."""
    def __init__(self, raw_response : requests.Response) -> None:
        self._raw : requests.Response = raw_response
        self.status_code: int = raw_response.status_code
        self.headers: Dict[str, str] = raw_response.headers
        self.elapsed: float = raw_response.elapsed.total_seconds()
        self._json_cache: Optional[Dict[str, Any]] = None


    @property
    def text(self) -> Any:
        """Return the response body as text."""
        return self._raw.text

    @property
    def ok(self) -> bool:
        """Return True if the response status code is 200-299."""
        return 200 <= self.status_code < 300

    @property
    def status(self) -> int:
        """Return the response status code.
        Args:
            None
        Returns:
            The HTTP status code of the response.
        """
        return self.status_code

    @property
    def assertions(self) -> "AssertionsFacade":
        """Return an assertions Facade instance that can be chained with other methods"""
        return AssertionsFacade(self)

    def json(self) -> Dict[str, Any]:
        """Return the response body as JSON.
        Args:
            None
        Returns:
            The response body parsed as a JSON object.
        Raises:
            ValueError: If the response body is not valid JSON.
        """
        if self._json_cache is None:
            try:
                self._json_cache = self._raw.json()
            except ValueError:
                raise ValueError("Response body is not valid JSON")
        return self._json_cache

    # assertions

    def assert_status(self, expected_status: int) -> "Response":
        """Assert that the response status code matches the expected status code.
        Args:
            expected_status: The expected HTTP status code.
        Returns:
            The current Response instance for chaining.
        Raises:
            AssertionError: If the actual status code does not match the expected status code."""

        __tracebackhide__ = True
        assert self.status_code == expected_status, f"Expected status code {expected_status}, got {self.status_code}"
        return self

    def assert_json(self, expected_json: Dict[str, Any]) -> "Response":
        """
        Assert that the response JSON matches the expected JSON.

        Args:
            expected_json: The expected JSON object.

        Returns:
            The current Response instance for chaining.

        Raises:
            AssertionError: If the response JSON does not match the expected JSON.
        """
        __tracebackhide__ = True
        actual_json = self.json()
        assert actual_json == expected_json, f"Expected JSON {expected_json}, got {actual_json}"
        return self

    def assert_header(self, key: str, expected_value: Optional[str] = None) -> "Response":
        """Assert that a response header exists, and optionally matches a value.

      Args:
          key: The header name to check.
          expected_value: If provided, the exact value the header must match.
              If omitted, only the presence of the header is asserted.

      Returns:
          The current Response instance for chaining.

      Raises:
          AssertionError: If the header is missing or its value does not match.
      """
        __tracebackhide__ = True
        actual_value = self.headers.get(key)
        assert actual_value is not None, f"Expected header '{key}' to be present but it was not found"
        if expected_value is not None:
            assert actual_value == expected_value, \
                f"Expected header '{key}' to be '{expected_value}', got '{actual_value}'"
        return self

    def assert_ok(self) -> "Response":
        """Assert that the response status code is 200-299.
        Returns:
            The current Response instance for chaining.
        Raises:
            AssertionError: If the response status code is not in the 200-299 range.
        """
        __tracebackhide__ = True
        assert self.ok, f"Expected response to be OK (status code 200-299), got {self.status_code}"
        return self

    def assert_json_contains(self, expected_subset: Dict[str, Any]) -> "Response":
        """Assert that the response JSON contains the expected subset.

        Args:
            expected_subset: The expected subset of the JSON object.

        Returns:
            The current Response instance for chaining.

        Raises:
            AssertionError: If the response JSON does not contain the expected subset.
        """
        __tracebackhide__ = True
        actual_json = self.json()
        assert isinstance(actual_json, dict), f"Expected JSON response to be a dictionary, got {type(actual_json)}"
        for key, value in expected_subset.items():
            assert key in actual_json, f"Expected key '{key}' not found in response JSON"
            assert actual_json[key] == value, f"Expected key '{key}' to have value '{value}', got '{actual_json[key]}'"
        return self

    def assert_json_schema(self, schema: Dict[str, Any]) -> "Response":
        """Assert that the response JSON matches the expected schema.

        Args:
            schema: The JSON schema to validate against.

        Returns:
            The current Response instance for chaining.

        Raises:
            AssertionError: If the response JSON does not match the schema.
        """
        from jsonschema import validate, ValidationError
        __tracebackhide__ = True
        actual_json = self.json()
        try:
            validate(instance=actual_json, schema=schema)
        except ValidationError as e:
            raise AssertionError(f"JSON schema validation failed: {e.message}")
        return self

    def assert_response_time(self, max_time: float) -> "Response":
        """Assert that the response time is less than the specified maximum time in seconds.

        Args:
            max_time: The maximum allowed response time in seconds.

        Returns:
            The current Response instance for chaining.

        Raises:
            AssertionError: If the response time exceeds the specified maximum time.
        """
        __tracebackhide__ = True
        assert self.elapsed < max_time, f"Expected response time to be less than {max_time} seconds, got {self.elapsed} seconds"
        return self

    def assert_json_path(self, json_path: str, expected_value: Any) -> "Response":
        """Assert that the value at the specified JSON path matches the expected value.
        Args:
            json_path: The JSON path expression to evaluate.
            expected_value: The expected value at the specified JSON path.
        Returns:
            The current Response instance for chaining.
        Raises:
            AssertionError: If the value at the specified JSON path does not match the expected value.

        Example:
            >>> json_response = {
            ...     "data": {
            ...         "id": 123,
            ...         "name": "Test Item"
            ...     }
            ... }
            ... response.assert_json_path("$.data.id", 123)
        """
        __tracebackhide__ = True
        actual_json = self.json()
        jsonpath_expr = parse(json_path)
        matches = [match.value for match in jsonpath_expr.find(actual_json)]
        assert matches, f"No matches found for JSON path '{json_path}'"
        assert matches[0] == expected_value, f"Expected value at JSON path '{json_path}' to be '{expected_value}', got '{matches[0]}'"
        return self

    def assert_json_path_type(self, json_path: str, expected_type: type) -> "Response":
        """Assert that the value at the specified JSON path is of the expected type.

        Args:
            json_path: The JSON path expression to evaluate.
            expected_type: The expected type of the value at the specified JSON path.

        Returns:
            The current Response instance for chaining.

        Raises:
            AssertionError: If the value at the specified JSON path is not of the expected type.
        """
        __tracebackhide__ = True
        actual_json = self.json()
        jsonpath_expr = parse(json_path)
        matches = [match.value for match in jsonpath_expr.find(actual_json)]
        assert matches, f"No matches found for JSON path '{json_path}'"
        assert isinstance(matches[0], expected_type), f"Expected value at JSON path '{json_path}' to be of type '{expected_type.__name__}', got '{type(matches[0]).__name__}'"
        return self

    def assert_json_path_exists(self, json_path: str) -> "Response":
        """Assert that a value exists at the specified JSON path.

        Args:
            json_path: The JSON path expression to evaluate.

        Returns:
            The current Response instance for chaining.

        Raises:
            AssertionError: If no value exists at the specified JSON path.
        """
        __tracebackhide__ = True
        actual_json = self.json()
        jsonpath_expr = parse(json_path)
        matches = [match.value for match in jsonpath_expr.find(actual_json)]
        assert matches, f"No matches found for JSON path '{json_path}'"
        return self

    def assert_cookie_exists(self, key: str) -> "Response":
        """Assert that a cookie with the specified key exists in the response.
        Args:
            key: The name of the cookie to check for.
        Returns:
            The current Response instance for chaining.
        Raises:
            AssertionError: If a cookie with the specified key does not exist in the response.
        """
        __tracebackhide__ = True
        cookies = self._raw.cookies
        assert key in cookies, f"Expected cookie '{key}' not found in response"
        assert cookies[key] != "", f"Expected cookie '{key}' to have a non-empty value, got an empty value"
        return self

    def assert_cookie_value(self, key: str, expected_value: str) -> "Response":
        """Assert that a cookie with the specified key has the expected value.
        Args:
            key: The name of the cookie to check.
            expected_value: The expected value of the cookie.

        Returns:
            The current Response instance for chaining.

        Raises:
            AssertionError: If a cookie with the specified key does not have the expected value.
        """
        __tracebackhide__ = True
        cookies = self._raw.cookies
        assert key in cookies, f"Expected cookie '{key}' not found in response"
        actual_value = cookies[key]
        assert actual_value == expected_value, f"Expected cookie '{key}' to have value '{expected_value}', got '{actual_value}'"
        return self