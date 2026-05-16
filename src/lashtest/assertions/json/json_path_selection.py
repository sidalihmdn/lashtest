from ..errors import AssertionFailure
from ..matchers.equality import ValueAssertions
from ..matchers.strings import StringAssertions
from ..matchers.collections import CollectionAssertions


class AllValuesSelection:
    """Wrapper for multiple JSON values selected with .all()."""

    def __init__(self, values, expr: str):
        self.values = values
        self.expr = expr

    @property
    def text(self):
        """Extract string values and return as CollectionAssertions."""
        text_values = [value for value in self.values if isinstance(value, str)]
        return CollectionAssertions(text_values, description=f"text values for JSON path '{self.expr}'")


class JsonPathSelection:
    """Represents JSONPath matches and exposes fluent assertions."""

    def __init__(self, expr: str, values):
        self.expr = expr
        self.values = values

    @property
    def count(self):
        return ValueAssertions(len(self.values), description=f"count of values for JSON path '{self.expr}'")

    @property
    def first(self):
        return JsonPathSelection(expr=self.expr, values=[self.values[0]] if self.values else [])

    def all(self):
        return AllValuesSelection(self.values, self.expr)

    def exists(self):
        if not self.values:
            raise AssertionFailure(f"No matches found for JSON path '{self.expr}'")
        return self

    @property
    def text(self):
        self.exists()
        value = self.values[0]
        if not isinstance(value, str):
            raise AssertionFailure(
                f"Expected value at JSON path '{self.expr}' to be of type 'str', got '{type(value).__name__}'"
            )
        return StringAssertions(value, description=f"text of the first value for JSON path '{self.expr}'")

    @property
    def value(self):
        self.exists()
        return ValueAssertions(self.values[0], description=f"value at JSON path '{self.expr}'")
