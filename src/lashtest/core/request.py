from typing import Dict, Optional, Any, List, Union, TYPE_CHECKING
from ..http.auth import Auth, BasicAuth, BearerToken, APIKey
import time
import allure

from .exceptions import MaxRetriesExceededError
from ..utils.logger import get_logger
if TYPE_CHECKING:
    from .client import APIClient
    from .response import Response


logger = get_logger()


class Request:
    """A class representing an API request."""

    def __init__(self, client : "APIClient", method: str, endpoint: str) -> None:
        self.client : "APIClient" = client
        self.method : str = method
        self.endpoint : str = endpoint
        self.headers : Dict[str, str] = {}
        self.params : Dict[str, str] = {}
        self.body : Optional[Any] = None
        self.timeout : float = client.timeout
        self.data : Optional[Any] = None
        self.auth : Optional[Any] = None
        self.response : Optional[Any] = None
        self.files : Dict[str, Any] = {}
        self._open_handles : List[Any] = []
        self._retry_config : Optional[Dict[str, Any]] = None

    def with_header(self, key: str, value: str) -> "Request":
        """Add a header to the request.
        Args:
            key: The header name.
            value: The header value.
        Returns:
            The current Request instance for chaining.
        Raises:
            ValueError: If the key or value is not a string.
        """
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("Header key and value must be strings")
        self.headers[key] = value
        return self

    def with_param(self, key: str, value: str) -> "Request":
        """Add a query parameter to the request.
        Args:
            key: The parameter name.
            value: The parameter value.
        Returns:
            The current Request instance for chaining.
        Raises:
            ValueError: If the key or value is not a string.
        """
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("Parameter key and value must be strings")
        self.params[key] = value
        return self

    def with_params(self, params: Dict[str, str]) -> "Request":
        """Add multiple query parameters to the request.
        Args:
            params: A dictionary of query parameters to add.
        Returns:
            The current Request instance for chaining.
        Raises:
            ValueError: If params is not a dictionary.
        """
        if not isinstance(params, dict):
            raise ValueError("Params must be a dictionary")
        self.params.update(params)
        return self

    def with_body(self, body : Any) -> "Request":
        """Set the body of the request.
        Args:
            body: The body content to set for the request.
        Returns:
            The current Request instance for chaining.
        """
        self.body = body
        return self

    def with_json(self, json_body: Dict[str, Any]) -> "Request":
        """Set the body of the request as JSON.
        Args:
            json_body: The JSON body content to set for the request.
        Returns:
            The current Request instance for chaining.
        """
        self.body = json_body
        self.headers["Content-Type"] = "application/json"
        return self

    def with_auth(self, auth: Union[Auth, BasicAuth, BearerToken, APIKey]) -> "Request":
        """Set the authentication for the request.
        Args:
            auth: The authentication to set for the request.
        Returns:
            The current Request instance for chaining.
        Raises:
            ValueError: If auth is not an instance of the Auth class.
        """
        if not isinstance(auth, (Auth, BasicAuth, BearerToken, APIKey)):
            raise ValueError("Auth must be an instance of Auth class")
        self.auth = auth
        return self

    def with_timeout(self, timeout: float) -> "Request":
        """Set the timeout for the request.
        Args:
            timeout: The timeout value in seconds.
        Returns:
            The current Request instance for chaining.
        """
        self.timeout = timeout
        return self

    def with_file(self, field: str, path: str) -> "Request":
        """Set the file to be uploaded in the request.
        Args:
            field: The form field name for the file.
            path: The file path to upload.
        Returns:
            The current Request instance for chaining.
        Raises:
            ValueError: If field or path is not a string, or if the file cannot be opened.
        """
        if not isinstance(field, str) or not isinstance(path, str):
            raise ValueError("Field and path must be strings")
        try:
            handle = open(path, 'rb')
        except Exception as e:
            raise ValueError(f"Failed to open file: {e}")
        self.files[field] = handle
        self._open_handles.append(handle)
        return self

    def with_data(self, data: Any) -> "Request":
        """Set the form data for the request.
        Args:
            data: The form data to set for the request.
        Returns:
            The current Request instance for chaining.
        """
        self.data = data
        return self

    def with_retry(self, max_attempts: int, on_status: Optional[List[int]] = None, raise_on_exhausted: bool = False) -> "Request":
        """Configure retry logic for the request.
        Args:
            max_attempts: The maximum number of retry attempts.
            on_status: A list of HTTP status codes that should trigger a retry. Defaults to [500, 502, 503, 504].
            raise_on_exhausted: Whether to raise an exception if the maximum retry attempts are exhausted. Defaults to False.
        Returns:
            The current Request instance for chaining.
        """

        self._retry_config = {
            "max_attempts": max_attempts,
            "on_status": on_status if on_status is not None else [500, 502, 503, 504],
            "raise_on_exhausted": raise_on_exhausted
        }
        return self

    def _execute(self) -> "Response":
        """Internal method to execute the request and return a Response object."""
        self.response = self.client._send_request(self)
        # retry logic
        if self._retry_config is not None:
            attempts = 1
            while self.response.status_code in self._retry_config['on_status'] and attempts < self._retry_config['max_attempts']:
                logger.debug(f"Retrying request, attempt {attempts + 1}")
                attempts += 1
                time.sleep(2 ** (attempts - 1))  # Exponential backoff
                self.response = self.client._send_request(self)

            if self._retry_config['raise_on_exhausted'] :
                if self.response.status_code in self._retry_config['on_status']:
                    raise MaxRetriesExceededError(attempts, self.response.status_code)
        return self.response

    # context manager
    def __enter__(self) -> "Response":
        return self._execute()

    # direct call for testing
    def send(self) -> "Response":
        """Send the request and return the response."""
        return self._execute()

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> None:
        for handle in self._open_handles:
            handle.close()
        self._open_handles.clear()

