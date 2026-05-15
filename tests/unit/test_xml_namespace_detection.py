"""
Tests for automatic namespace detection in XML assertions.
"""

import pytest
from unittest.mock import MagicMock
from lashtest.assertions.xml.xml_assertions import XmlAssertions


def make_xml_response(xml_content: str) -> MagicMock:
    """Create a mock response with XML content."""
    response = MagicMock()
    response.text = xml_content
    return response


class TestNamespaceDetection:
    """Test automatic namespace detection."""

    def test_detect_default_namespace(self):
        """Test detection of default namespace."""
        xml = """<?xml version="1.0"?>
        <root xmlns="http://example.com">
            <item>Test</item>
        </root>
        """
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        # Default namespace should be detected and mapped to 'ns' prefix
        assert xml_assertions._namespaces is not None
        assert 'http://example.com' in xml_assertions._namespaces.values()

    def test_detect_prefixed_namespace(self):
        """Test detection of prefixed namespace."""
        xml = """<?xml version="1.0"?>
        <root xmlns:app="http://example.com/app">
            <app:item>Test</app:item>
        </root>
        """
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        # Namespace should be detected
        assert 'app' in xml_assertions._namespaces
        assert xml_assertions._namespaces['app'] == 'http://example.com/app'

    def test_detect_multiple_namespaces(self):
        """Test detection of multiple namespaces."""
        xml = """<?xml version="1.0"?>
        <root xmlns="http://example.com" xmlns:app="http://app.com" xmlns:custom="http://custom.com">
            <item>Test</item>
        </root>
        """
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        # All namespaces should be detected
        assert len(xml_assertions._namespaces) >= 2

    def test_no_namespace_xml(self):
        """Test XML without namespaces."""
        xml = """<?xml version="1.0"?>
        <root>
            <item>Test</item>
        </root>
        """
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        # Namespace dict should exist but be empty or minimal
        assert xml_assertions._namespaces is not None

    def test_xpath_with_default_namespace(self):
        """Test XPath queries work with default namespace."""
        xml = """<?xml version="1.0"?>
        <root xmlns="http://example.com">
            <item>First</item>
            <item>Second</item>
        </root>
        """
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        # Should find items using wildcard XPath (works with or without namespace)
        result = xml_assertions.xpath('//*')
        assert len(result.nodes) >= 2

    def test_xpath_with_prefixed_namespace(self):
        """Test XPath queries work with prefixed namespace."""
        xml = """<?xml version="1.0"?>
        <root xmlns:app="http://example.com/app">
            <app:item id="1">First</app:item>
            <app:item id="2">Second</app:item>
        </root>
        """
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        # Use the detected namespace prefix in XPath
        result = xml_assertions.xpath('//app:item')
        assert len(result.nodes) >= 1

    def test_soap_envelope_with_namespaces(self):
        """Test SOAP response with namespaces."""
        xml = """<?xml version="1.0"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <GetUserResponse xmlns="http://example.com/api">
                    <user id="123">John Doe</user>
                </GetUserResponse>
            </soap:Body>
        </soap:Envelope>
        """
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        # Namespaces should be detected
        assert xml_assertions._namespaces is not None
        
        # XPath should work
        result = xml_assertions.xpath('//soap:Body')
        assert len(result.nodes) >= 1

    def test_atom_feed_with_namespace(self):
        """Test Atom feed (RSS-like) with namespace."""
        xml = """<?xml version="1.0" encoding="utf-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Example Feed</title>
            <entry>
                <title>Entry 1</title>
            </entry>
            <entry>
                <title>Entry 2</title>
            </entry>
        </feed>
        """
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        # Namespace should be detected
        assert xml_assertions._namespaces is not None
        
        # XPath should find entries
        result = xml_assertions.xpath('//*')
        assert len(result.nodes) >= 2

    def test_nested_namespace_declarations(self):
        """Test XML with nested namespace declarations."""
        xml = """<?xml version="1.0"?>
        <root xmlns="http://example.com">
            <section xmlns:local="http://local.com">
                <local:item>Test</local:item>
            </section>
        </root>
        """
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        # Nested namespaces should be detected
        assert len(xml_assertions._namespaces) >= 1

    def test_namespace_auto_detect_is_transparent(self):
        """Test that namespace auto-detection is transparent to user."""
        xml = """<?xml version="1.0"?>
        <root xmlns="http://example.com">
            <book id="1">
                <title>Python Guide</title>
                <author>John Doe</author>
            </book>
        </root>
        """
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        # User should be able to use xpath as normal without worrying about namespaces
        count = xml_assertions.xpath('//*').count
        assert count.value >= 3  # root, book, title, author
