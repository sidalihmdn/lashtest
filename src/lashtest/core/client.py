import requests
from .request import Request
from .exceptions import APIError, HTTPError, APITimeoutError, APIConnectionError, InvalidURL, JSONDecodeError, AuthenticationError
from .response import Response
from ..http.auth import Auth, BasicAuth, BearerToken, APIKey
from ..utils.ssl import find_system_ca_bundle
from ..utils.logger import get_logger

from typing import Optional, Dict, Any, Union, Literal

import certifi
import allure
import json

logger = get_logger()

class APIClient:
    """A class representing an API client.
    Args:
    base_url: The base URL for the API.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.base_path : Optional[str] = None
        self.headers : Dict[str, str] = {}
        self.auth : Optional[Auth] = None
        self.timeout : float = 30  # Default timeout in seconds
        self.session = requests.Session()
        self.verify_ssl : Optional[Union[bool, str]] = certifi.where()  # Can be True, False, or path to CA bundle

    def with_header(self, key: str, value: str) -> 'APIClient':
        """Add a header to the client.
        Args:
            key: The header name.
            value: The header value.
        Returns:
            The current APIClient instance for chaining.
        Raises:
            ValueError: If the key or value is not a string.
        """
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("Header key and value must be strings")
        self.headers[key] = value
        return self

    def with_base_path(self, base_path: str) -> 'APIClient':
        """Set the base path for the client, overriding the base URL.
        Args:
            base_path: The base path to set for the client.
        Returns:
            The current APIClient instance for chaining.
        """
        if not isinstance(base_path, str) or not base_path.startswith('/'):
            raise ValueError("Base path must be a string starting with '/'")
        self.base_path = base_path
        return self

    def with_headers(self, headers: Dict[str, str]) -> 'APIClient':
        """Add multiple headers to the client.
        Args:
            headers: A dictionary of headers to add.
        Returns:
            The current APIClient instance for chaining.
        Raises:
            ValueError: If headers is not a dictionary.
        """
        if not isinstance(headers, dict):
            raise ValueError("Headers must be a dictionary")
        self.headers.update(headers)
        return self

    def with_auth(self, auth: Union[Auth, BasicAuth, BearerToken, APIKey]) -> 'APIClient':
        """Set the authentication for the client.
        Args:
            auth: An instance of the Auth class.
        Returns:
            The current APIClient instance for chaining.
        Raises:
            ValueError: If auth is not an instance of the Auth class.
        """
        if not isinstance(auth, (Auth, BasicAuth, BearerToken, APIKey)):
            raise ValueError("Auth must be an instance of Auth class")
        self.auth = auth
        return self

    def with_ssl_verification(self, verify: Optional[Union[bool, str]]) -> 'APIClient':
        """Set SSL verification for the client.
        Args:
            verify: SSL verification setting. Can be True, False, or path to CA bundle.
        Returns:
            The current APIClient instance for chaining.
        Raises:
            ValueError: If verify is not a boolean or string.
        """
        self.verify_ssl = verify
        return self

    def with_timeout(self, timeout: float) -> 'APIClient':
        """Set the timeout for the client.
        Args:
            timeout: Timeout in seconds.
        Returns:
            The current APIClient instance for chaining.
        Raises:
            ValueError: If timeout is not a positive number.
        """
        if timeout <= 0:
            raise ValueError("Timeout must be a positive number")
        self.timeout = timeout
        return self

    def with_cookies(self, cookies: Dict[str, str]) -> 'APIClient':
        """Set cookies for the client.
        Args:
            cookies: A dictionary of cookies to set.
        Returns:
            The current APIClient instance for chaining.
        Raises:
            ValueError: If cookies is not a dictionary.
        """
        if not isinstance(cookies, dict):
            raise ValueError("Cookies must be a dictionary")
        self.session.cookies.update(cookies)
        return self

    def clear_cookies(self) -> 'APIClient':
        """Clear all cookies from the client.
        Returns:
            The current APIClient instance for chaining.
        """
        self.session.cookies.clear()
        return self

    def get(self, endpoint: str) -> Request:
        """Create a GET request.
        Args:
            endpoint: The API endpoint for the GET request.
        Returns:
            A Request object for the GET request.
        Raises:
            InvalidURL: If the endpoint is not a valid string starting with '/'. """
        self._validate_endpoint(endpoint)
        return Request(self, 'GET', endpoint)

    def post(self, endpoint: str) -> Request:
        """Create a POST request.
        Args:
            endpoint: The API endpoint for the POST request.
        Returns:
            A Request object for the POST request.
        Raises:
            InvalidURL: If the endpoint is not a valid string starting with '/'.
        """
        self._validate_endpoint(endpoint)
        return Request(self, 'POST', endpoint)

    def put(self, endpoint: str) -> Request:
        """Create a PUT request.
        Args:
            endpoint: The API endpoint for the PUT request.
        Returns:
            A Request object for the PUT request.
        Raises:
            InvalidURL: If the endpoint is not a valid string starting with '/'.
        """
        self._validate_endpoint(endpoint)
        return Request(self, 'PUT', endpoint)

    def delete(self, endpoint: str) -> Request:
        """Create a DELETE request.
        Args:
            endpoint: The API endpoint for the DELETE request.
        Returns:
            A Request object for the DELETE request.
        Raises:
            InvalidURL: If the endpoint is not a valid string starting with '/'.
        """
        self._validate_endpoint(endpoint)
        return Request(self, 'DELETE', endpoint)

    def patch(self, endpoint: str) -> Request:
        """Create a PATCH request.
        Args:
            endpoint: The API endpoint for the PATCH request.
        Returns:
            A Request object for the PATCH request.
        Raises:
            InvalidURL: If the endpoint is not a valid string starting with '/'.
        """
        self._validate_endpoint(endpoint)
        return Request(self, 'PATCH', endpoint)

    def _send_request(self, request: Request) -> Response:
        """Send the request and return the response.
        Args:
            request: The Request object to be sent.
        Returns:
            A Response object containing the server's response.
        Raises:
            HTTPError: If an HTTP error occurs.
            APITimeoutError: If the request times out.
            APIConnectionError: If a connection error occurs.
            InvalidURL: If the URL is invalid.
            JSONDecodeError: If the response JSON is invalid.
            APIError: For other API-related errors.
        """
        url = f"{self.base_url}{self.base_path or ''}/{request.endpoint.lstrip('/')}"

        # Merge headers from client defaults and request-specific
        merged_headers = {**self.headers, **request.headers}

        # Apply authentication if present
        auth_to_use = request.auth or self.auth
        if auth_to_use and hasattr(auth_to_use, 'apply'):
            merged_headers = auth_to_use.apply(merged_headers)

        # Allure step for request
        with allure.step(f"Send {request.method} request to {url}"):
            allure.attach(
                json.dumps({
                    "method": request.method,
                    "url": url,
                    "headers": merged_headers,
                    "params": request.params,
                    "body": request.body,
                    "data": request.data,
                    "files": list(request.files.keys())  # Just attach file names for readability
                }, indent=2)
            , name="Request Details", attachment_type=allure.attachment_type.JSON)


            # debug log
            logger.debug(f" -> {request.method} {url}")
            logger.debug(f"     Headers: {merged_headers}")
            logger.debug(f"     Params : {request.params}")
            if request.body :   logger.debug(f"     Body   : {request.body}")
            if request.data :   logger.debug(f"     Data   : {request.data}")
            if request.files :  logger.debug(f"     Files  : {request.files}")

            try:
                response = self.session.request(
                    method=request.method,
                    url=url,
                    headers=merged_headers,
                    params=request.params,
                    json=request.body,
                    data=request.data,
                    files=request.files,
                    timeout=request.timeout or self.timeout,
                    verify=self.verify_ssl  # Use SSL verification setting
                )
                request.response = response
                logger.debug(f" <- {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
                return Response(response)
            except requests.exceptions.HTTPError as e:
                raise HTTPError(e.response) from e
            except requests.exceptions.Timeout as e:
                raise APITimeoutError(request.timeout) from e
            except requests.exceptions.ConnectionError as e:
                raise APIConnectionError(str(e)) from e
            except requests.exceptions.InvalidURL as e:
                raise InvalidURL(str(e)) from e
            except requests.exceptions.JSONDecodeError as e:
                raise JSONDecodeError(str(e)) from e
            except requests.exceptions.RequestException as e:
                raise APIError(str(e)) from e

    def close(self) -> None:
        """Close the session."""
        self.session.close()

    def __enter__(self) -> 'APIClient':
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type : Optional[type], exc_value: Optional[BaseException], traceback: Optional[Any]) -> Literal[False]:
        """Exit the runtime context related to this object."""
        self.close()
        return False  # Don't suppress exceptions

    def _validate_endpoint(self, endpoint: str) -> None:
        """Validate the endpoint format."""
        if not isinstance(endpoint, str) or not endpoint.startswith('/'):
            raise InvalidURL(f"Invalid endpoint: {endpoint}. Endpoint must be a string starting with '/'.")

