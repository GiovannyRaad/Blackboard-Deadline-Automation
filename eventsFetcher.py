import re
import requests
import base64
from bs4 import BeautifulSoup
import os
from datetime import datetime,  timezone
from zoneinfo import ZoneInfo

username = os.getenv("UNI_USER")
password = os.getenv("UNI_PASS")

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
        resp = self.session.get(path, **kwargs)
        resp.raise_for_status()
        return resp

    def post(self, path, data=None, **kwargs):
        resp = self.session.post(path, data=data, **kwargs)
        resp.raise_for_status()
        return resp

    def put(self, path, data=None, **kwargs):
        resp = self.session.put(self._url(path), data=data, **kwargs)
        resp.raise_for_status()
        return resp

    def delete(self, path, **kwargs):
        resp = self.session.delete(self._url(path), **kwargs)
        resp.raise_for_status()
        return resp.status_code

def compute_midnight(tmz):
    #Compute and format date and time to ISO 8601
    local = ZoneInfo(tmz)
    local_midnight = datetime.now(local).replace(hour=0, minute=0, second=0, microsecond=0)
    utc_midnight = local_midnight.astimezone(timezone.utc)
    date_str = utc_midnight.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return date_str


    
#Initial page

url = "https://elearn.lau.edu.lb/auth-saml/saml/login"

params = {
    "apId": "_240_1",
    "redirectUrl": "https://elearn.lau.edu.lb/ultra"
}

client = APIClient(url)

response = client.get("https://elearn.lau.edu.lb/", allow_redirects=False)

response = client.get(url, params=params, allow_redirects=False)

print(response.headers.get("Location"))

text = response.text

#Extracting the SAMLRequest value from the response HTML

soup = BeautifulSoup(text, "html.parser")
SAMLRequest = soup.find("input", {"name": "SAMLRequest"})["value"]

payload = { "SAMLRequest": SAMLRequest }

response = client.post("https://iam.lau.edu.lb/isam/sps/LAUIDP/saml20/login", data=payload, allow_redirects=False)

print(response.headers.get("Location"))


#Submitting login form

payload = { "username": username, "password": password ,
           "logonID": "", "login-form-type": "pwd" }

headers = {
    "referer": "https://iam.lau.edu.lb/isam/sps/LAUIDP/saml20/login"
}
response = client.post("https://iam.lau.edu.lb/pkmslogin.form", data=payload, allow_redirects=False, headers=headers)



 

#Simulate js , username and password encode
#Need to update the cookies with the encoded values and send a get request

# encoded_username = base64.b64encode(username.encode()).decode()
# client.session.cookies.update({
#     "TM-SESSION-UN": encoded_username,
#     "BR-SESSION-UN": encoded_username,
#     "PC-SESSION-UN": encoded_username  
# })

# response = client.post("https://iam.lau.edu.lb/pkmslogin.form", data=payload, allow_redirects=False, headers=headers)

response = client.get("https://iam.lau.edu.lb/isam/sps/LAUIDP/saml20/login", headers={"referer":"https://iam.lau.edu.lb/isam/sps/LAUIDP/saml20/login"})

#response = client.post("https://elearn.lau.edu.lb/auth-saml/saml/SSO/alias/_240_1", data={"RelayState": "","SAMLResponse":saml}, allow_redirects=True)

print(response.status_code)
#Request calendar page
url = "https://elearn.lau.edu.lb/ultra/calendar"

response = client.get(url, allow_redirects=True)

html = response.text


m = re.search(r'xsrf"\s*:\s*"([^"]+)"|xsrf\s*:\s*"([^"]+)"', html)
if m:
    xsrf_token = m.group(1) or m.group(2)
print("xsrf:", xsrf_token)


#Interaction

jsonF = {"action":"pageview","analyticsId":"/calendar","url":"https://elearn.lau.edu.lb/ultra/calendar","applicationId":"ultra","course":"","screenDimension":{"innerHeight":897,"innerWidth":763,"outerHeight":1036,"outerWidth":1920}}

response = client.post("https://elearn.lau.edu.lb/telemetry/api/v1/browser/interactions", json=jsonF)

print(response.status_code)

print(client.session.cookies.get_dict())


url = "https://elearn.lau.edu.lb/learn/api/v1/calendars/dueDateCalendarItems"

headers = {
    "X-Blackboard-Xsrf": xsrf_token
}

date_str = compute_midnight("Asia/Beirut")

params = {
    "date": date_str,  # from above
    "date_compare": "greaterOrEqual",
    "includeCount": "true",
    "limit": "20",
    "offset": "0"
}
response = client.get(url, params=params, headers=headers)
print(response.text)