"""Unit tests for XML assertions DSL"""

import pytest
from unittest.mock import MagicMock
from lashtest.assertions.xml.xml_assertions import XmlAssertions
from lashtest.assertions.xml.xpath_selection import XpathSelection, AllNodesSelection
from lashtest.assertions.errors import LashtestError, XmlAssertionFailure


# ── helpers ───────────────────────────────────────────────────────────────────

def make_xml_response(xml_content: str = '') -> MagicMock:
    """Create a mock response with XML content."""
    response = MagicMock()
    response.text = xml_content
    return response


# ── XmlAssertions initialization ──────────────────────────────────────────────

class TestXmlAssertionsInitialization:
    """Test XmlAssertions initialization and parsing."""

    def test_valid_xml_parses_successfully(self):
        """Valid XML should parse without error."""
        xml = """<?xml version="1.0"?>
        <root>
            <item>Test</item>
        </root>
        """
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        assert xml_assertions._xml is not None

    def test_invalid_xml_raises_error(self):
        """Invalid XML should raise LashtestError."""
        xml = """<?xml version="1.0"?>
        <root>
            <unclosed>
        </root>
        """
        response = make_xml_response(xml)
        with pytest.raises(LashtestError, match="Invalid XML"):
            XmlAssertions(response)

    def test_malformed_xml_raises_error(self):
        """Malformed XML without root element should raise error."""
        response = make_xml_response("Not valid XML")
        with pytest.raises(LashtestError, match="Invalid XML"):
            XmlAssertions(response)

    def test_empty_xml_raises_error(self):
        """Empty response should raise error."""
        response = make_xml_response("")
        with pytest.raises(LashtestError, match="Invalid XML"):
            XmlAssertions(response)

    def test_xml_with_declaration_parses(self):
        """XML with declaration should parse correctly."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <root><item>Test</item></root>
        """
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        assert xml_assertions._xml is not None

    def test_xml_without_declaration_parses(self):
        """XML without declaration should parse correctly."""
        xml = "<root><item>Test</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        assert xml_assertions._xml is not None


# ── XPath selection and parsing ───────────────────────────────────────────────

class TestXPathSelection:
    """Test XPath expression selection."""

    def test_valid_xpath_returns_nodes(self):
        """Valid XPath should return matching nodes."""
        xml = "<root><item>A</item><item>B</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//item')
        assert isinstance(result, XpathSelection)
        assert len(result.nodes) == 2

    def test_invalid_xpath_raises_error(self):
        """Invalid XPath syntax should raise XmlAssertionFailure."""
        xml = "<root><item>Test</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        with pytest.raises(XmlAssertionFailure, match="Invalid XPath"):
            xml_assertions.xpath('//item[@invalid syntax')

    def test_xpath_no_matches(self):
        """XPath with no matches should return empty result."""
        xml = "<root><item>Test</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//nonexistent')
        assert len(result.nodes) == 0

    def test_xpath_with_predicate(self):
        """XPath with predicates should work."""
        xml = """<root>
            <item id="1">First</item>
            <item id="2">Second</item>
        </root>
        """
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//item[@id="2"]')
        assert len(result.nodes) == 1

    def test_xpath_with_position(self):
        """XPath with position predicate should work."""
        xml = "<root><item>A</item><item>B</item><item>C</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//item[2]')
        assert len(result.nodes) == 1


# ── XpathSelection.count ──────────────────────────────────────────────────────

class TestXPathSelectionCount:
    """Test counting nodes."""

    def test_count_returns_value_assertions(self):
        """count property should return ValueAssertions."""
        xml = "<root><item>A</item><item>B</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//item').count
        # ValueAssertions has methods like eq(), gte(), etc.
        assert hasattr(result, 'eq')
        assert hasattr(result, 'gte')

    def test_count_eq(self):
        """count.eq() should pass when count matches."""
        xml = "<root><item>A</item><item>B</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        # Should not raise
        xml_assertions.xpath('//item').count.eq(2)

    def test_count_eq_fails(self):
        """count.eq() should fail when count doesn't match."""
        xml = "<root><item>A</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        with pytest.raises(AssertionError):
            xml_assertions.xpath('//item').count.eq(5)

    def test_count_gte(self):
        """count.gte() should work for greater than or equal."""
        xml = "<root><item>A</item><item>B</item><item>C</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        xml_assertions.xpath('//item').count.gte(3)
        xml_assertions.xpath('//item').count.gte(2)


# ── XpathSelection.first ──────────────────────────────────────────────────────

class TestXPathSelectionFirst:
    """Test selecting first node."""

    def test_first_returns_xpath_selection(self):
        """first property should return XpathSelection."""
        xml = "<root><item>A</item><item>B</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//item').first
        assert isinstance(result, XpathSelection)

    def test_first_with_matches(self):
        """first should return single first node when matches exist."""
        xml = "<root><item>A</item><item>B</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//item').first
        assert len(result.nodes) == 1
        assert result.nodes[0].text == 'A'

    def test_first_with_no_matches(self):
        """first should return empty result when no matches."""
        xml = "<root><item>Test</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//nonexistent').first
        assert len(result.nodes) == 0


# ── XpathSelection.nth ────────────────────────────────────────────────────────

class TestXPathSelectionNth:
    """Test selecting nth node."""

    def test_nth_returns_xpath_selection(self):
        """nth() should return XpathSelection."""
        xml = "<root><item>A</item><item>B</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//item').nth(1)
        assert isinstance(result, XpathSelection)

    def test_nth_first_item(self):
        """nth(1) should return first item (1-based indexing)."""
        xml = "<root><item>A</item><item>B</item><item>C</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//item').nth(1)
        assert len(result.nodes) == 1
        assert result.nodes[0].text == 'A'

    def test_nth_middle_item(self):
        """nth(2) should return second item."""
        xml = "<root><item>A</item><item>B</item><item>C</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//item').nth(2)
        assert result.nodes[0].text == 'B'

    def test_nth_last_item(self):
        """nth(3) should return third item."""
        xml = "<root><item>A</item><item>B</item><item>C</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//item').nth(3)
        assert result.nodes[0].text == 'C'

    def test_nth_out_of_bounds(self):
        """nth() with out-of-bounds index should raise error."""
        xml = "<root><item>A</item><item>B</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        with pytest.raises(LashtestError, match="5th node.*only 2 nodes"):
            xml_assertions.xpath('//item').nth(5)

    def test_nth_zero_index(self):
        """nth(0) should raise error (1-based indexing)."""
        xml = "<root><item>A</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        with pytest.raises(LashtestError, match="0th node"):
            xml_assertions.xpath('//item').nth(0)

    def test_nth_negative_index(self):
        """nth() with negative index should raise error."""
        xml = "<root><item>A</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        with pytest.raises(LashtestError):
            xml_assertions.xpath('//item').nth(-1)


# ── XpathSelection.text ───────────────────────────────────────────────────────

class TestXPathSelectionText:
    """Test accessing text content."""

    def test_text_returns_string_assertions(self):
        """text property should return StringAssertions."""
        xml = "<root><item>Test</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//item').text
        assert hasattr(result, 'eq')
        assert hasattr(result, 'contains')

    def test_text_eq(self):
        """text.eq() should work."""
        xml = "<root><item>Hello</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        xml_assertions.xpath('//item').text.eq('Hello')

    def test_text_contains(self):
        """text.contains() should work."""
        xml = "<root><item>Hello World</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        xml_assertions.xpath('//item').text.contains('World')

    def test_text_on_empty_result_raises_error(self):
        """text on empty XPath result should raise error."""
        xml = "<root><item>Test</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        with pytest.raises(LashtestError, match="no nodes were found"):
            xml_assertions.xpath('//nonexistent').text

    def test_text_gets_first_node_only(self):
        """text should get text from first node only."""
        xml = "<root><item>A</item><item>B</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        xml_assertions.xpath('//item').text.eq('A')


# ── XpathSelection.attribute ──────────────────────────────────────────────────

class TestXPathSelectionAttribute:
    """Test accessing attributes."""

    def test_attribute_returns_string_assertions(self):
        """attribute() should return StringAssertions."""
        xml = '<root><item id="123">Test</item></root>'
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//item').attribute('id')
        assert hasattr(result, 'eq')

    def test_attribute_eq(self):
        """attribute().eq() should work."""
        xml = '<root><item id="123">Test</item></root>'
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        xml_assertions.xpath('//item').attribute('id').eq('123')

    def test_attribute_contains(self):
        """attribute().contains() should work."""
        xml = '<root><item email="test@example.com">User</item></root>'
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        xml_assertions.xpath('//item').attribute('email').contains('@example')

    def test_missing_attribute_raises_error(self):
        """Missing attribute should raise error."""
        xml = '<root><item id="123">Test</item></root>'
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        with pytest.raises(LashtestError, match="Expected attribute 'name'"):
            xml_assertions.xpath('//item').attribute('name')

    def test_missing_attribute_shows_available_attributes(self):
        """Missing attribute error should show available attributes."""
        xml = '<root><item id="123" class="active" status="enabled">Test</item></root>'
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        with pytest.raises(LashtestError, match="Available attributes"):
            xml_assertions.xpath('//item').attribute('data')

    def test_attribute_on_empty_result_raises_error(self):
        """attribute on empty result should raise error."""
        xml = "<root><item>Test</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        with pytest.raises(LashtestError, match="no nodes were found"):
            xml_assertions.xpath('//nonexistent').attribute('id')

    def test_attribute_gets_first_node_only(self):
        """attribute should get from first node only."""
        xml = '<root><item id="1">A</item><item id="2">B</item></root>'
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        xml_assertions.xpath('//item').attribute('id').eq('1')


# ── XpathSelection.exists ─────────────────────────────────────────────────────

class TestXPathSelectionExists:
    """Test exists assertion."""

    def test_exists_with_matches(self):
        """exists() should pass when nodes are found."""
        xml = "<root><item>Test</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        # Should not raise
        xml_assertions.xpath('//item').exists()

    def test_exists_with_no_matches(self):
        """exists() should fail when no nodes are found."""
        xml = "<root><item>Test</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        with pytest.raises(XmlAssertionFailure, match="Expected at least one node"):
            xml_assertions.xpath('//nonexistent').exists()

    def test_exists_returns_self_for_chaining(self):
        """exists() should return self for chaining."""
        xml = "<root><item>Test</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//item').exists()
        assert isinstance(result, XpathSelection)


# ── XpathSelection.all ────────────────────────────────────────────────────────

class TestXPathSelectionAll:
    """Test .all() for collection assertions."""

    def test_all_returns_all_nodes_selection(self):
        """all() should return AllNodesSelection."""
        xml = "<root><item>A</item><item>B</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        result = xml_assertions.xpath('//item').all()
        assert isinstance(result, AllNodesSelection)

    def test_all_text_contains(self):
        """all().text.contains() should check if collection contains exact item."""
        xml = "<root><book>Python</book><book>JavaScript</book></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        # Collection contains checks for exact item in collection
        xml_assertions.xpath('//book').all().text.contains('Python')

    def test_all_text_not_contains(self):
        """all().text.not_contains() should check collection."""
        xml = "<root><book>Python</book><book>JavaScript</book></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        xml_assertions.xpath('//book').all().text.not_contains('Ruby')

    def test_all_text_count(self):
        """all().text.length should allow count assertions."""
        xml = "<root><item>A</item><item>B</item><item>C</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        xml_assertions.xpath('//item').all().text.length.eq(3)


# ── AllNodesSelection ─────────────────────────────────────────────────────────

class TestAllNodesSelection:
    """Test AllNodesSelection for collection operations."""

    def test_all_nodes_selection_has_text_property(self):
        """AllNodesSelection should have text property."""
        xml = "<root><item>A</item><item>B</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        all_selection = xml_assertions.xpath('//item').all()
        assert hasattr(all_selection, 'text')

    def test_all_nodes_selection_text_filters_none(self):
        """AllNodesSelection.text should filter out None values."""
        xml = "<root><item>A</item><item></item><item>C</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        collection = xml_assertions.xpath('//item').all().text
        # Should only have A and C (not the empty one)
        assert len(collection.collection) == 2

    def test_all_nodes_selection_empty(self):
        """AllNodesSelection with no nodes should work."""
        xml = "<root><item>Test</item></root>"
        response = make_xml_response(xml)
        xml_assertions = XmlAssertions(response)
        
        collection = xml_assertions.xpath('//nonexistent').all().text
        assert len(collection.collection) == 0
