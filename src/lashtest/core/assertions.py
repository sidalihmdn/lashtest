from .repsonse import Response
from lxml import etree


class XmlAssertions:
    def __init__(self, xml_text : str):
        self._tree = etree.fromstring(xml_text.encode())

    def xpath(self, expr : str, namespace:str = None):
        nodes = self._tree.xpath(expr, namespace=namespace)

        return XpathSelection(expr=expr, nodes=nodes)




