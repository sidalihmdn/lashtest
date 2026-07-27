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
        if not isinstance(auth, Auth):
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

    def with_retry(
        self,
        max_attempts: int,
        on_status: Optional[List[int]] = None,
        raise_on_exhausted: bool = False,
        backoff_factor: float = 1.0,
        max_backoff: float = 60.0,
        jitter: bool = False,
        retry_on_exceptions: bool = False,
    ) -> "Request":
        """Configure retry logic for the request.

        Args:
            max_attempts: The maximum number of retry attempts.
            on_status: HTTP status codes that trigger a retry. Defaults to [500, 502, 503, 504].
            raise_on_exhausted: Raise MaxRetriesExceededError when all attempts fail.
            backoff_factor: Multiplier applied to the exponential delay. Delay is
                ``backoff_factor * 2^(attempt-1)`` seconds. Defaults to ``1.0``.
            max_backoff: Upper bound on the computed delay in seconds. Defaults to ``60.0``.
            jitter: Add a random fraction (0–1 s) to each delay to reduce thundering-herd.
            retry_on_exceptions: Also retry on connection/timeout exceptions, not just
                status-code matches.

        Returns:
            The current Request instance for chaining.
        """
        self._retry_config = {
            "max_attempts": max_attempts,
            "on_status": on_status if on_status is not None else [500, 502, 503, 504],
            "raise_on_exhausted": raise_on_exhausted,
            "backoff_factor": backoff_factor,
            "max_backoff": max_backoff,
            "jitter": jitter,
            "retry_on_exceptions": retry_on_exceptions,
        }
        return self

    def _compute_backoff(self, attempt: int) -> float:
        """Return the sleep duration for the given attempt (1-based)."""
        import random
        cfg = self._retry_config
        delay = cfg["backoff_factor"] * (2 ** (attempt - 1))
        delay = min(delay, cfg["max_backoff"])
        if cfg["jitter"]:
            delay += random.random()
        return delay

    def _execute(self) -> "Response":
        """Internal method to execute the request and return a Response object."""
        from ..core.exceptions import APIConnectionError, APITimeoutError

        if self._retry_config is None:
            self.response = self.client._send_request(self)
            return self.response

        cfg = self._retry_config
        attempts = 0
        last_exc: Optional[Exception] = None

        while attempts < cfg["max_attempts"]:
            attempts += 1
            try:
                self.response = self.client._send_request(self)
                last_exc = None
            except (APIConnectionError, APITimeoutError) as exc:
                if cfg["retry_on_exceptions"] and attempts < cfg["max_attempts"]:
                    logger.debug(f"Retrying after exception ({type(exc).__name__}), attempt {attempts + 1}")
                    time.sleep(self._compute_backoff(attempts))
                    last_exc = exc
                    continue
                raise

            if self.response.status_code not in cfg["on_status"]:
                return self.response

            if attempts < cfg["max_attempts"]:
                logger.debug(f"Retrying request (status {self.response.status_code}), attempt {attempts + 1}")
                time.sleep(self._compute_backoff(attempts))

        if last_exc is not None:
            raise last_exc

        if cfg["raise_on_exhausted"] and self.response.status_code in cfg["on_status"]:
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

