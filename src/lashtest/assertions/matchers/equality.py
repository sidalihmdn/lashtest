from ..errors import AssertionFailure

class ValueAssertions: 
    def __init__(self, value, description=None):
        self.value = value
        self.description = description

    def eq(self, expected):
        """Assert that the value is equal to the expected value."""
        if self.value != expected:
            raise AssertionFailure(f"Expected {self.description} to be equal to {expected}, but got {self.value}")
        return self
    
    def not_eq(self, expected):
        """Assert that the value is not equal to the expected value."""
        if self.value == expected:
            raise AssertionFailure(f"Expected {self.description} to not be equal to {expected}, but got {self.value}")
        return self
    
    def gt(self, expected):
        """Assert that the value is greater than the expected value."""
        if self.value <= expected:
            raise AssertionFailure(f"Expected {self.description} to be greater than {expected}, but got {self.value}")
        return self
    
    def lt(self, expected):
        """Assert that the value is less than the expected value."""
        if self.value >= expected:
            raise AssertionFailure(f"Expected {self.description} to be less than {expected}, but got {self.value}")
        return self
    
    def gte(self, expected):
        """Assert that the value is greater than or equal to the expected value."""
        if self.value < expected:
            raise AssertionFailure(f"Expected {self.description} to be greater than or equal to {expected}, but got {self.value}")
        return self
    
    def lte(self, expected):
        """Assert that the value is less than or equal to the expected value."""
        if self.value > expected:
            raise AssertionFailure(f"Expected {self.description} to be less than or equal to {expected}, but got {self.value}")
        return self