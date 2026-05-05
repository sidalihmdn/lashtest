"""Unit tests for lashtest.utils.ssl"""

import pytest
from unittest.mock import patch
from lashtest.utils.ssl import find_system_ca_bundle


class TestFindSystemCaBundle:

    @patch('platform.system', return_value='Darwin')
    @patch('os.path.exists')
    def test_returns_first_existing_path_on_macos(self, mock_exists, mock_system):
        mock_exists.side_effect = lambda p: p == '/etc/ssl/cert.pem'
        result = find_system_ca_bundle()
        assert result == '/etc/ssl/cert.pem'

    @patch('platform.system', return_value='Linux')
    @patch('os.path.exists')
    def test_returns_first_existing_path_on_linux(self, mock_exists, mock_system):
        mock_exists.side_effect = lambda p: p == '/etc/ssl/certs/ca-certificates.crt'
        result = find_system_ca_bundle()
        assert result == '/etc/ssl/certs/ca-certificates.crt'

    @patch('platform.system', return_value='Linux')
    @patch('os.path.exists')
    def test_falls_back_to_second_linux_path(self, mock_exists, mock_system):
        mock_exists.side_effect = lambda p: p == '/etc/pki/tls/certs/ca-bundle.crt'
        result = find_system_ca_bundle()
        assert result == '/etc/pki/tls/certs/ca-bundle.crt'

    @patch('platform.system', return_value='Windows')
    @patch('os.path.exists', return_value=False)
    @patch('certifi.where', return_value='/path/to/certifi/cacert.pem')
    def test_falls_back_to_certifi_on_windows(self, mock_certifi, mock_exists, mock_system):
        result = find_system_ca_bundle()
        assert result == '/path/to/certifi/cacert.pem'

    @patch('platform.system', return_value='Darwin')
    @patch('os.path.exists', return_value=False)
    @patch('certifi.where', return_value='/path/to/certifi/cacert.pem')
    def test_falls_back_to_certifi_when_no_system_path_exists(self, mock_certifi, mock_exists, mock_system):
        result = find_system_ca_bundle()
        assert result == '/path/to/certifi/cacert.pem'

    @patch('platform.system', return_value='UnknownOS')
    @patch('os.path.exists', return_value=False)
    @patch('certifi.where', return_value='/fallback/cacert.pem')
    def test_falls_back_to_certifi_on_unknown_platform(self, mock_certifi, mock_exists, mock_system):
        result = find_system_ca_bundle()
        assert result == '/fallback/cacert.pem'

    @patch('platform.system', return_value='Darwin')
    @patch('os.path.exists')
    def test_returns_string(self, mock_exists, mock_system):
        mock_exists.return_value = True
        result = find_system_ca_bundle()
        assert isinstance(result, str)
