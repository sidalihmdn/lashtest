class AssertionsFacade:
    def __init__(self, reponse : Response):
        self.response = repsonse

    @proprety
    def xml(self):
        return XmlAssertions(self.response.body)

    # TODO : migrate the json, http here
