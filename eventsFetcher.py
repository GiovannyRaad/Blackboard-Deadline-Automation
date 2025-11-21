import requests
from bs4 import BeautifulSoup

class APIClient:
    def __init__(self, base_url, headers=None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

        # set default headers
        if headers:
            self.session.headers.update(headers)

    def _url(self, path):
        return f"{self.base_url}/{path.lstrip('/')}"

    def get(self, path, **kwargs):
        resp = self.session.get(self._url(path), **kwargs)
        resp.raise_for_status()
        return resp.text

    def post(self, path, data=None, **kwargs):
        resp = self.session.post(path, data=data, **kwargs)
        resp.raise_for_status()
        return resp.text

    def put(self, path, data=None, **kwargs):
        resp = self.session.put(self._url(path), data=data, **kwargs)
        resp.raise_for_status()
        return resp.text

    def delete(self, path, **kwargs):
        resp = self.session.delete(self._url(path), **kwargs)
        resp.raise_for_status()
        return resp.status_code
    

url = "https://elearn.lau.edu.lb/auth-saml/saml/login"

params = {
    "apId": "_240_1",
    "redirectUrl": "https://elearn.lau.edu.lb/ultra"
}

client = APIClient(url)

response = client.get("", params=params)

soup = BeautifulSoup(response, "html.parser")
SAMLRequest = soup.find("input", {"name": "SAMLRequest"})["value"]

payload = { "SAMLRequest": SAMLRequest }

response = client.post("https://iam.lau.edu.lb/isam/sps/LAUIDP/saml20/login", data=payload)
print(response)