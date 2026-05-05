import pytest
from lashtest import APIClient as Client

class TestBasePath:
    client = Client('https://httpbin.org')\
        .with_base_path('/status')\
        .with_header("User-Agent", "lashtest-base-path-tests/1.0")

    def test_status_200(self):
        """Test that the client correctly constructs URLs with base path"""
        with self.client.get('/200') as response:
            response.assert_status(200)

    def test_status_404(self):
        """Test that the client correctly constructs URLs with base path for 404"""
        with self.client.get('/404') as response:
            response.assert_status(404)
