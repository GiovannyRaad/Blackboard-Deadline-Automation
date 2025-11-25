from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
import requests
import urllib.parse
import os
import json
from dotenv import load_dotenv



def add_params(url, params):
    # appends parameters to url end
    return f"{url}?{urllib.parse.urlencode(params)}"


def compute_midnight(tmz):
    # Compute and format date and time to ISO 8601
    local = ZoneInfo(tmz)
    local_midnight = datetime.now(local).replace(hour=0, minute=0, second=0, microsecond=0)
    utc_midnight = local_midnight.astimezone(timezone.utc)
    date_str = utc_midnight.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return date_str


def fetch_events(cookies):
    #returns json
    #fetching events using requests
    date_str = compute_midnight("Asia/Beirut")

    params = {
        "date": date_str,
        "date_compare": "greaterOrEqual",
        "includeCount": "true",
        "limit": "20",
        "offset": "0"
    }

    #Events and deadlines json url
    url = add_params("https://elearn.lau.edu.lb/learn/api/v1/calendars/dueDateCalendarItems", params)

    client = requests.Session()
    response = client.get(url, cookies=cookies)
    events = response.text

    data = json.loads(events)

    return data


def selenium_fetch(username, password):
    #returns json
    #Fetch using selenium headless browser

    
    options = Options()
    options.add_argument("--headless") #no gui
    caps = DesiredCapabilities().FIREFOX
    caps['marionette'] = True
    caps['moz:firefoxOptions'] = {'args': ['-headless']}

    service = Service("/usr/local/bin/geckodriver")
    try:

        driver = webdriver.Firefox(options=options, service=service)

        #Go to login page
        driver.get("https://elearn.lau.edu.lb/auth-saml/saml/login?apId=_240_1&redirectUrl=https://elearn.lau.edu.lb/ultra")

        # Wait and fill login fields
        search = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
        search.send_keys(username)
        search = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "password")))
        search.send_keys(password)
        search.submit()

        # Wait for redirect
        WebDriverWait(driver, 10).until(EC.url_contains("ultra"))

        selenium_cookies = driver.get_cookies()
        with open("cookies.json", "w") as f:
            json.dump(selenium_cookies, f)
        cookies = {c['name']: c['value'] for c in selenium_cookies}
        data = fetch_events(cookies)
        

    finally:
        driver.quit()
        return data

def run():
    load_dotenv()

    username = os.environ.get("UNI_USER")
    password = os.environ.get("UNI_PASS")
    #Main

    try:
        cookies = {}
        with open("cookies.json", "r") as f:
            selenium_cookies = json.load(f)
            cookies = {c['name']: c['value'] for c in selenium_cookies}
        data = fetch_events(cookies)
        if not data.get("results"):
            raise Exception("No events found with saved cookies.")
        print("Fetched events using saved cookies.")

    except Exception as e:
        print(f"Error fetching events: {e}")
        data = selenium_fetch()
        print("Fetched events using selenium.")

    finally:
        events_data = {}
        id = 0
        for i in data.get("results", []):
        
            title = i.get("title", "No Title")
            endDate = i.get("endDate", "No End Date")
            course = i.get("calendarNameLocalizable", {}).get("rawValue", "No Course")
            events_data[id] = {
                "title": title,
                "endDate": endDate,
                "course": course
            }
            id += 1
        return events_data