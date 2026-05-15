from lxml import etree
from .xpath_selection import XpathSelection
from ..errors import LashtestError, XmlAssertionFailure

class XmlAssertions:
    """Provides XML-specific assertions for API responses."""
    def __init__(self, response):
        self.response = response
        try:
            self._xml = etree.fromstring(response.text.encode())
        except etree.XMLSyntaxError as e:
            raise LashtestError(f"Invalid XML in response: {str(e)}")
        except UnicodeDecodeError as e:
            raise LashtestError(f"Response text is not valid UTF-8: {str(e)}")
        
        # Auto-detect namespaces from the document
        self._namespaces = self._extract_namespaces()

    def _extract_namespaces(self):
        """Extract all namespaces from the XML document.
        
        Converts default namespace (None key) to a usable prefix since lxml doesn't support
        empty string prefixes in XPath expressions.
        """
        namespaces = {}
        
        # Get namespaces from root element
        if self._xml.nsmap:
            namespaces.update(self._xml.nsmap)
        
        # Traverse all elements to find additional namespace declarations
        for element in self._xml.iter():
            if element.nsmap:
                namespaces.update(element.nsmap)
        
        # Handle default namespace (None key)
        # lxml doesn't support empty string prefix in XPath, so use 'ns' instead
        if None in namespaces:
            default_ns = namespaces.pop(None)
            # Check if 'ns' is already used, if so find an unused prefix
            prefix = 'ns'
            counter = 0
            while prefix in namespaces:
                prefix = f'ns{counter}'
                counter += 1
            namespaces[prefix] = default_ns
        
        return namespaces

    def xpath(self, expr):
        """Select nodes using an XPath expression.
        
        Automatically handles namespaces detected in the XML document.
        """
        try:
            # Pass namespaces if any exist in the document
            if self._namespaces:
                nodes = self._xml.xpath(expr, namespaces=self._namespaces)
            else:
                nodes = self._xml.xpath(expr)
        except etree.XPathError as e:
            raise XmlAssertionFailure(f"Invalid XPath expression '{expr}': {str(e)}")
        except TypeError as e:
            raise XmlAssertionFailure(f"XPath evaluation failed for '{expr}': {str(e)}")
        
        return XpathSelection(expr=expr, nodes=nodes)
