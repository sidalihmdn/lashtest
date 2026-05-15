from .xml.xml_assertions import XmlAssertions

class AssertionsFacade:
    """Facade for accessing different types of assertions."""
    def __init__(self, response):
        self.response = response

    @property
    def xml(self):
        """Access XML-specific assertions."""
        return XmlAssertions(self.response)

    # TODO : migrate the json, http here
