"""Decorators for API testing"""

import functools
import inspect
from typing import Callable, Any
from ..http.auth import BasicAuth, BearerToken, APIKey
import pytest
import allure

def authenticated(auth: Any):
      """Apply authentication to every request made via self.client.
      Works on both individual methods and entire test classes.

      Args:
          auth: An Auth instance (BasicAuth, BearerToken, APIKey).

      Examples:
          >>> # on a single method
          ... class TestAPI:
          ...     client = APIClient('https://api.example.com')
          ...
          ...     @authenticated(BearerToken('my-token'))
          ...     def test_protected(self):
          ...         with self.client.get('/profile') as response:
          ...             response.assert_ok()

          >>> # on the entire class — all test methods get auth
          ... @authenticated(BearerToken('my-token'))
          ... class TestProtectedRoutes:
          ...     client = APIClient('https://api.example.com')
          ...
          ...     def test_profile(self):
          ...         with self.client.get('/profile') as response:
          ...             response.assert_ok()
      """
      def decorator(target):

          if inspect.isclass(target):
              # apply to every test_ method in the class
              for name, method in inspect.getmembers(target, predicate=inspect.isfunction):
                  if name.startswith('test_'):
                      setattr(target, name, decorator(method))
              return target

          # apply to a single method
          @functools.wraps(target)
          def wrapper(self, *args, **kwargs):
              original_client = self.client
              self.client = self.client.with_auth(auth)
              try:
                  return target(self, *args, **kwargs)
              finally:
                  self.client = original_client
          return wrapper
      return decorator

def tag(*tags: str):
    """Apply tags to a test function or class."""
    def decorator(target):
        def wrapper(*args, **kwargs):
            for tag in tags:
                pytest.mark.__getattr__(tag)(target)
            return target(*args, **kwargs)
        return wrapper
    return decorator



#############################################################
# allure decorators — avoid importing allure in every test file #
#############################################################

def title(text: str) -> Callable:
      """Set the title of the test in the Allure report.

      Shorthand for @allure.title — avoids importing allure in every test file.

      Args:
          text: The title to display in the Allure report.

      Examples:
          >>> @title("Get user by ID returns the correct user data")
          ... def test_get_user():
          ...     with client.get('/users/1') as response:
          ...         response.assert_ok()

          >>> class TestUsers:
          ...     client = APIClient('https://api.example.com')
          ...
          ...     @title("Create a new user successfully")
          ...     def test_create_user(self):
          ...         with self.client.post('/users') as response:
          ...             response.assert_status(201)
      """
      def decorator(func):
          return allure.title(text)(func)
      return decorator

def severity(level: str) -> Callable:
    """Set the severity level of the test in the Allure report.
    shorthand for @allure.severity — avoids importing allure in every test file.
    Args:
    level: The severity level (e.g. 'blocker', 'critical', 'normal', 'minor', 'trivial').
    Examples:
    >>> @severity('critical')
    ... def test_critical_feature():
    ...     with client.get('/critical-endpoint') as response:
    ...         response.assert_ok()
    """
    def decorator(func):
        return allure.severity(level)(func)
    return decorator

def description(text: str) -> Callable:
    """Set the description of the test in the Allure report.
    shorthand for @allure.description — avoids importing allure in every test file.
    Args:
    text: The description text to display in the Allure report.
    Examples:
    >>> @description("This test verifies that the user can log in with valid credentials.")
    ... def test_login():
    ...     with client.post('/login') as response:
    ...         response.assert_ok()
    """
    def decorator(func):
        return allure.description(text)(func)
    return decorator

def link(url: str, name: str = None) -> Callable:
    """Add a link to the test in the Allure report.
    shorthand for @allure.link — avoids importing allure in every test file.
    Args:
    url: The URL of the link.
    name: An optional name for the link (defaults to the URL if not provided).
    Examples:
    >>> @link("https://jira.example.com/browse/PROJ-123", name="JIRA Ticket")
    ... def test_related_to_jira():
    ...     with client.get('/some-endpoint') as response:
    ...         response.assert_ok()
    """
    def decorator(func):
        return allure.link(url, name)(func)
    return decorator





__all__ = ['authenticated', 'tag', 'title', 'severity', 'description', 'link']
