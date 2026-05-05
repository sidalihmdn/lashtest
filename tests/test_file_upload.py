import tempfile
import os
import pytest
from lashtest import APIClient as Client
from lashtest.http import BasicAuth, BearerToken
import logging
import requests

LOGGER = logging.getLogger(__name__)

class TestFileUpload:
      """Test suite for file upload functionality"""
      client = Client('https://httpbin.org').with_header("User-Agent", "lashtest-file-upload-tests/1.0")

      @pytest.fixture
      def tmp_file(self):
          """Create a temporary file for upload tests, delete after test."""
          with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
              f.write('hello from lashtest')
              path = f.name
          yield path
          os.unlink(path)

      def test_single_file_upload(self, tmp_file):
          """Test uploading a single file"""
          with self.client.post('/post').with_file('file', tmp_file) as response:
              response.assert_status(200)
              response.assert_json_path_exists('$.files.file')

      def test_file_content_is_sent(self, tmp_file):
          """Test that file content is correctly received by the server"""
          with self.client.post('/post').with_file('file', tmp_file).with_retry(3) as response:
              response.assert_status(200)
              response.assert_json_path('$.files.file', 'hello from lashtest')

      def test_multiple_files_upload(self, tmp_path):
          """Test uploading multiple files in a single request"""
          file1 = tmp_path / "first.txt"
          file2 = tmp_path / "second.txt"
          file1.write_text('content one')
          file2.write_text('content two')

          with self.client.post('/post') \
              .with_file('file1', str(file1)) \
              .with_file('file2', str(file2)) as response:

              response.assert_status(200)
              response.assert_json_path_exists('$.files.file1')
              response.assert_json_path_exists('$.files.file2')

      def test_file_handles_are_closed_after_request(self, tmp_file):
          """Test that file handles are properly closed after the context manager exits"""
          request = self.client.post('/post').with_file('file', tmp_file)

          with request as response:
              response.assert_status(200)

          for handle in request._open_handles:
              assert handle.closed

      def test_retry_on_error(self, tmp_file):
          """Test that the retry mechanism works when a request fails"""
          with self.client.post('/status/500').with_file('file', tmp_file).with_retry(3) as response:
              # an error response should trigger retries, but eventually we expect a 500 status code
              response.assert_status(500)
