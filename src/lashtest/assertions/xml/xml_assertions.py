from lxml import etree
from .xpath_selection import XpathSelection

class XmlAssertions:
    def __init__(self, response):
        self.response = response
        self._xml = etree.fromstring(response.body.encode())

    def xpath(self, expr):
        return XpathSelection(expr=?, node=?)


    