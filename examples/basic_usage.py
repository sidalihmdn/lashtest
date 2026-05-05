from lashtest import APIClient
from lashtest.http import BasicAuth


client = APIClient(base_url="https://testpages.eviltester.com/")

with client.with_auth(BasicAuth(username="authorized", password="password001")).get("/pages/auth/basic-auth/") as response:
    print("Status Code:", response.status_code)
    print("Response Body:", response.text)
