from playwright.sync_api import sync_playwright
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
import requests
import urllib.parse
import json
import os

# Resolve the cookie cache next to this file so the skill works from any cwd.
COOKIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.json")




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


def fetch_events(cookies, tmz):
    #returns json
    #fetching events using requests
    date_str = compute_midnight(tmz)

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


def browser_fetch(username, password, tmz):
    #returns json
    #Fetch using playwright headless browser

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)  #no gui
        try:
            context = browser.new_context()
            page = context.new_page()

            #Go to login page
            page.goto("https://elearn.lau.edu.lb/auth-saml/saml/login?apId=_240_1&redirectUrl=https://elearn.lau.edu.lb/ultra")

            # Wait and fill login fields
            page.wait_for_selector("#username", timeout=10000)
            page.fill("#username", username)
            page.fill("#password", password)
            page.press("#password", "Enter")

            # Wait for redirect
            page.wait_for_url(lambda url: "ultra" in url, timeout=10000)

            browser_cookies = context.cookies()
            with open(COOKIES_PATH, "w") as f:
                json.dump(browser_cookies, f)
            cookies = {c['name']: c['value'] for c in browser_cookies}
            return fetch_events(cookies, tmz)

        finally:
            browser.close()

def run(username, password, tmz):
    #Main

    try:
        cookies = {}
        with open(COOKIES_PATH, "r") as f:
            saved_cookies = json.load(f)
            cookies = {c['name']: c['value'] for c in saved_cookies}
        data = fetch_events(cookies, tmz)
        if not data.get("results"):
            raise Exception("No events found with saved cookies.")
        print("Fetched events using saved cookies.")

    except Exception as e:
        print(f"Error fetching events: {e}")
        data = browser_fetch(username, password, tmz)
        print("Fetched events using playwright.")

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


if __name__ == "__main__":
    # Standalone entrypoint: emit the deadlines as JSON on stdout.
    import sys

    events = run(
        os.environ.get("UNI_USER"),
        os.environ.get("UNI_PASS"),
        os.environ.get("TIMEZONE"),
    )
    json.dump(events, sys.stdout, indent=2)
    print()
