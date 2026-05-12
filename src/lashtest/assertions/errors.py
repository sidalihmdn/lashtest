class LashtestError(Exception):
    """Base framework exception."""

class AssertionFailure(AssertionError):
    """Base Assertions failure."""

class XmlAssertionFailure(AssertionFailure):
    """Xml Assertion failure."""

class JsonAssetionFailure(AssertionFailure):
    """Json Assertion failure."""

class XpathNotFound(XmlAssertionFailure):
    """Xpath did not match any nodes."""

class InvalidXpath(XmlAssertionFailure):
    """Xpath expression is invalid."""
