from jsonpath_ng import parse

from .json_path_selection import JsonPathSelection


class JsonAssertions:
    """Provides JSON-specific fluent assertions for API responses."""

    def __init__(self, response):
        self.response = response
        self._json = response.json()

    def path(self, expr: str):
        jsonpath_expr = parse(expr)
        matches = [match.value for match in jsonpath_expr.find(self._json)]
        return JsonPathSelection(expr=expr, values=matches)
