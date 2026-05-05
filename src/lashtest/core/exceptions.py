from .response import Response

class APIError(Exception):
    """Base class for all API-related exceptions."""
    pass

class HTTPError(APIError):
    """Exception raised for HTTP errors."""
    def __init__(self, response: Response) -> None:
        self.response = response
        self.status_code = response.status_code
        self.message = f"HTTP error occurred (Status code: {self.status_code})"
        super().__init__(self.message)

class APITimeoutError(APIError):
    """Exception raised for request timeouts."""
    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        self.message = f"Request timed out after {self.timeout} seconds"
        super().__init__(self.message)

class APIConnectionError(APIError):
    """Exception raised for connection errors."""
    def __init__(self, message: str) -> None:
        self.message = f"Connection error occurred: {message}"
        super().__init__(self.message)

class InvalidURL(APIError):
    """Exception raised for invalid URLs."""
    def __init__(self, url: str) -> None:
        self.url = url
        self.message = f"Invalid URL: {self.url}"
        super().__init__(self.message)

class JSONDecodeError(APIError):
    """Exception raised for JSON decoding errors."""
    def __init__(self, message: str) -> None:
        self.message = f"JSON decode error: {message}"
        super().__init__(self.message)

class AuthenticationError(APIError):
    """Exception raised for authentication errors."""
    def __init__(self, message: str) -> None:
        self.message = f"Authentication error: {message}"
        super().__init__(self.message)

class MaxRetriesExceededError(APIError):
    """Exception raised when maximum retry attempts are exceeded."""
    def __init__(self, retries: int , status_code: int) -> None:
        self.retries = retries
        self.status_code = status_code
        self.message = f"Maximum retry attempts ({self.retries}) exceeded with status code {self.status_code}"
        super().__init__(self.message)