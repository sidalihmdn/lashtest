from datetime import timedelta
from unittest.mock import MagicMock

import pytest

from lashtest.core.response import Response


def make_response(json_data) -> Response:
    raw = MagicMock()
    raw.status_code = 200
    raw.text = ""
    raw.headers = {"Content-Type": "application/json"}
    raw.elapsed = timedelta(seconds=0.1)
    raw.cookies = {}
    raw.json.return_value = json_data
    return Response(raw)


class TestJsonAssertionsFluentApi:

    def test_path_count_assertions(self):
        response = make_response({"items": [1, 2, 3]})
        response.assertions.json.path("$.items[*]").count.gte(2).eq(3)

    def test_path_first_text_assertions(self):
        response = make_response({"user": {"name": "John"}})
        response.assertions.json.path("$.user.name").first.text.eq("John")

    def test_path_all_text_collection_assertions(self):
        response = make_response({"books": [{"title": "Python Guide"}, {"title": "Go Guide"}]})
        response.assertions.json.path("$.books[*].title").all().text.contains("Python Guide")

    def test_path_exists_fails_when_no_matches(self):
        response = make_response({"user": {}})
        with pytest.raises(AssertionError, match="No matches found"):
            response.assertions.json.path("$.user.missing").exists()
