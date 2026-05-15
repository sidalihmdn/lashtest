from ..matchers.equality import ValueAssertions
from ..matchers.strings import StringAssertions
from ..matchers.collections import CollectionAssertions

from ..errors import LashtestError, XmlAssertionFailure


class AllNodesSelection:
    """Wrapper for multiple nodes selected with .all() to enable chained property access like .text"""
    def __init__(self, nodes, expr: str):
        self.nodes = nodes
        self.expr = expr
    
    @property
    def text(self):
        """Extract text from all nodes and return as CollectionAssertions"""
        text_values = [node.text for node in self.nodes if node.text is not None]
        return CollectionAssertions(text_values, description=f"text values from nodes for XPath '{self.expr}'")
    
    @property
    def attribute(self, attr_name):
        """Extract attribute values from all nodes and return as CollectionAssertions"""
        attr_values = []
        for node in self.nodes:
            attr_value = node.get(attr_name)
            if attr_value is not None:
                attr_values.append(attr_value)
        return CollectionAssertions(attr_values, description=f"attribute '{attr_name}' values from nodes for XPath '{self.expr}'")


class XpathSelection:
    """Represents the result of an XPath selection, allowing for assertions on the selected nodes."""
    def __init__(self, expr:str, nodes):
        self.expr = expr
        self.nodes = nodes

    @property
    def count(self):
        """Assert the number of nodes selected by the XPath expression."""
        return ValueAssertions(len(self.nodes), description=f"count of nodes for XPath '{self.expr}'")
    
    @property
    def first(self):
        """Select the first node from the XPath result."""
        return XpathSelection(expr=self.expr, nodes=[self.nodes[0]] if self.nodes else [])
    
    def nth(self, n:int):
        """Select the nth node from the XPath result (1-based index)."""
        if n < 1 or n > len(self.nodes):
            raise LashtestError(f"Expected to access the {n}th node for XPath '{self.expr}', but there are only {len(self.nodes)} nodes.")
        return XpathSelection(expr=self.expr, nodes=[self.nodes[n-1]])
    
    def all(self):
        """Select all nodes from the XPath result and allow for assertions on their text values."""
        return AllNodesSelection(self.nodes, self.expr)
    
    
    def exists(self):
        """Assert that at least one node exists for the XPath expression."""
        if not self.nodes:
            raise XmlAssertionFailure(f"Expected at least one node to exist for XPath '{self.expr}', but found none.")
        return self
    
    @property
    def text(self):
        """Assert the text of the first node selected by the XPath expression."""
        if not self.nodes:
            raise LashtestError(f"Cannot access text of nodes for XPath '{self.expr}' because no nodes were found.")
        return StringAssertions(self.nodes[0].text, description=f"text of the first node for XPath '{self.expr}'")
    
    def attribute(self, attr_name):
        """Assert the value of an attribute on the first node selected by the XPath expression."""
        if not self.nodes:
            raise LashtestError(f"Cannot access attribute '{attr_name}' of nodes for XPath '{self.expr}' because no nodes were found.")
        attr_value = self.nodes[0].get(attr_name)
        if attr_value is None:
            available_attrs = list(self.nodes[0].attrib.keys())
            attrs_str = ", ".join(available_attrs) if available_attrs else "none"
            raise LashtestError(f"Expected attribute '{attr_name}' to exist on the first node for XPath '{self.expr}', but it was not found. Available attributes: {attrs_str}")
        return StringAssertions(attr_value, description=f"attribute '{attr_name}' of the first node for XPath '{self.expr}'")
