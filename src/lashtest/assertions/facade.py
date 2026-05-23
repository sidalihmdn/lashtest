from .xml.xml_assertions import XmlAssertions
from .json.json_assertions import JsonAssertions

class AssertionsFacade:
    """Facade for accessing different types of assertions."""
    def __init__(self, response):
        self.response = response

    @property
    def xml(self):
        """Access XML-specific assertions."""
        return XmlAssertions(self.response)

    @property
    def json(self):
        """Access JSON-specific assertions."""
        return JsonAssertions(self.response)
