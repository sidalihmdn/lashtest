from ..errors import AssertionFailure

class StringAssertions:
    def __init__(self, value:str, description:str=None):
        self.value = value
        self.description = description or f"String value '{value}'"
    
    def exists(self):
        """Assert that the string value exists (is not None)."""
        if self.value is None:
            raise AssertionFailure(f"Expected {self.description} to exist, but it is None.")
        return self

    def eq(self, expected:str):
        """Assert that the string value is equal to the expected value."""
        if self.value != expected:
            raise AssertionFailure(f"Expected {self.description} to be equal to '{expected}', but got '{self.value}'")
        return self
    
    def not_eq(self, expected:str):
        """Assert that the string value is not equal to the expected value."""
        if self.value == expected:
            raise AssertionFailure(f"Expected {self.description} to not be equal to '{expected}', but got '{self.value}'")
        return self
    
    def contains(self, substring:str):
        """Assert that the string value contains the expected substring."""
        if substring not in self.value:
            raise AssertionFailure(f"Expected {self.description} to contain '{substring}', but it does not.")
        return self
    
    def not_contains(self, substring:str):
        """Assert that the string value does not contain the expected substring."""
        if substring in self.value:
            raise AssertionFailure(f"Expected {self.description} to not contain '{substring}', but it does.")
        return self
    
    def starts_with(self, prefix:str):
        """Assert that the string value starts with the expected prefix."""
        if not self.value.startswith(prefix):
            raise AssertionFailure(f"Expected {self.description} to start with '{prefix}', but it does not.")
        return self
    
    def ends_with(self, suffix:str):
        """Assert that the string value ends with the expected suffix."""
        if not self.value.endswith(suffix):
            raise AssertionFailure(f"Expected {self.description} to end with '{suffix}', but it does not.")
        return self
    
    def not_exists(self):
        """Assert that the string value does not exist (is None)."""
        if self.value is not None:
            raise AssertionFailure(f"Expected {self.description} to not exist, but it does.")
        return self
